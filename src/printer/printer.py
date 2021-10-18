import asyncio
import json
import time
import os
from typing import Dict, Union

import aiofiles

import log
from ackWebsockets import SocketMessageResponse
from exceptions import HttpException
from .printer_receiver import PrinterReceiver


WPA_SUPPLICANT = "/boot/octopi-wpa-supplicant.txt"


class Printer(PrinterReceiver):
    async def home(self) -> SocketMessageResponse:
        log.info("homing...")
        await self.octo_api.post_command("G28")
        return SocketMessageResponse(0, "ok")

    async def _print_file(self, gcode: str, init: str = None) -> None:
        log.info("printing file " + gcode + '...')
        if init:
            for pre_cmd in init.split(";"):
                if len(pre_cmd) < 2:
                    continue
                log.info("executing init gcode " + pre_cmd)
                await self.octo_api.post_command(pre_cmd)
        await self.octo_api.print(gcode.split('/')[-1])

    async def _download_file(self, file: str, token: str, gcode: str) -> None:
        self.actualState["download"]["file"] = file
        self.actualState["download"]["completion"] = 0.0
        r = await self.ucloud_api.download(file, token)
        f = await aiofiles.open(gcode, mode='wb')
        chunk_size = 1024
        read = 0
        while True:
            if r.content_length:
                self.actualState["download"]["file"] = file
                self.actualState["download"]["completion"] = read / r.content_length
            chunk = await r.content.read(chunk_size)
            if not chunk:
                break
            await f.write(chunk)
            read += chunk_size
        log.info("file " + gcode + ' downloaded successfully, printing it...')
        self.actualState["download"]["file"] = None
        self.actualState["download"]["completion"] = -1
        await self.sync()

    async def print(self, data: Dict[str, str]) -> SocketMessageResponse:
        log.info("printing...")
        if 'file' not in data:
            return SocketMessageResponse(1, "file not specified")
        if 'token' not in data:
            return SocketMessageResponse(1, "token not specified")
        token = data["token"]
        user_id = data["user"] if "user" in data else ""

        if self.actualState['download']['file'] is not None:
            msg = "file "+self.actualState['download']['file']+" has already been scheduled to download and print"
            return SocketMessageResponse(1, msg)

        if not self.actualState["status"]["state"]['text'] == 'Operational':
            return SocketMessageResponse(1, "ucloud is not in an operational state")

        if not os.path.isdir(self.upload_path):
            os.mkdir(self.upload_path)
        upload_path = f"{self.upload_path}/{data['file']}"
        if not upload_path.endswith(".gcode"):
            upload_path += ".gcode"
        download_path = f"{user_id}/{data['file']}" if user_id else data['file']

        init = data['init'] if 'init' in data and data['init'] else None

        if not os.path.isfile(upload_path) or user_id:
            log.info("downloading file from " + download_path + " to " + upload_path+"...")
            exists = await self.ucloud_api.exists(download_path, token)

            if not exists:
                log.warning("path " + download_path + " does not exist on server")
                return SocketMessageResponse(1, "file does not exist")

            async def download_and_print():
                start = time.time()
                await self._download_file(download_path, token, upload_path)
                log.info(f"file {download_path} downloaded in {round(time.time() - start, 2)}s")
                await self._print_file(upload_path, init)

            asyncio.get_running_loop().create_task(download_and_print())
            return SocketMessageResponse(0, "file was not on ucloud, downloading it and printing it...")

        await self._print_file(upload_path, init)
        return SocketMessageResponse(0, "ok")

    async def cancel(self, data) -> SocketMessageResponse:
        default = "G91; G1 Z+100; G90"
        after_cancel = default if "after" not in data else data["after"]
        log.info("cancelling print...")
        if not self.actualState["status"]["state"]['flags']['printing']:
            return SocketMessageResponse(1, "ucloud is not in an printing state")

        await self.octo_api.cancel()
        if after_cancel:
            log.info("executing after cancel...")
            for cmd in after_cancel.split(";"):
                log.info(cmd)
                await self.octo_api.post_command(cmd)
        return SocketMessageResponse(0, "ok")

    async def pause(self, data) -> SocketMessageResponse:
        default = 'G91; G1 Z+20 F1000; G90; G1 X0 Y0'
        after_pause = default if "after" not in data else data["after"]
        log.info("pausing print...")
        if not self.actualState["status"]["state"]['flags']['printing']:
            return SocketMessageResponse(1, "ucloud is not in an printing state")

        await self.octo_api.pause()
        if after_pause:
            log.info("executing after pause...")
            for cmd in after_pause.split(";"):
                log.info(cmd)
                await self.octo_api.post_command(cmd)
        return SocketMessageResponse(0, "ok")

    async def resume(self) -> SocketMessageResponse:
        log.info("resuming print...")
        if not self.actualState["status"]["state"]['flags']['paused']:
            return SocketMessageResponse(1, "ucloud is not in an paused state")

        await self.octo_api.resume()
        return SocketMessageResponse(0, "ok")

    async def settings(self, data: Dict[str, str]) -> SocketMessageResponse:
        log.info("changing settings...")
        keys = [x for x in data if x not in ['instruction']]
        if not len(keys):
            return SocketMessageResponse(1, "no new settings has been sent")

        for k in keys:
            if k not in self.actualState['settings']:
                return SocketMessageResponse(1, "setting " + k + " not supported")

        for k in keys:
            self.actualState['settings'][k] = data[k]
        json.dump(self.actualState['settings'], open("../store.json", "w"))
        await self.sync()
        return SocketMessageResponse(0, "ok")

    async def move(self, data: Dict[str, str]) -> SocketMessageResponse:
        log.info("moving...")
        for k in ['axis', 'distance']:
            if k not in data:
                return SocketMessageResponse(1, k + " not specified")

        for cmd in ['G91', 'G1 {}{} F1000'.format(data['axis'], data['distance']), 'G90']:
            log.info("executing command from move command chain " + cmd + "...")
            await self.octo_api.post_command(cmd)
        return SocketMessageResponse(0, "ok")

    async def command(self, data: Dict[str, str]) -> SocketMessageResponse:
        log.info("executing command...")
        if 'command' not in data:
            log.warning("command not specified")
            return SocketMessageResponse(1, "command not specified")

        for cmd in data['command'].split(";"):
            log.info(cmd)
            await self.octo_api.post_command(cmd)
        return SocketMessageResponse(0, "ok")

    async def load(self) -> SocketMessageResponse:
        log.info("loading filament...")
        for cmd in ['M109 S210', 'G92 E0', 'G1 E100 F150', 'M109 S0']:
            log.info("executing command from load command chain " + cmd + "...")
            await self.octo_api.post_command(cmd)
        return SocketMessageResponse(0, "ok")

    async def unload(self) -> SocketMessageResponse:
        log.info("unloading filament...")
        for cmd in ['M109 S210', 'G28', 'G1 Z140', 'G92 E0', 'G1 E15 F150', 'G1 E-135 F300', 'M109 S0']:
            log.info("executing command from unload command chain " + cmd + "...")
            await self.octo_api.post_command(cmd)
        return SocketMessageResponse(0, "ok")

    async def wifi(self, data: Dict[str, str]) -> SocketMessageResponse:
        log.info("changing wifi...")
        for k in ['ssid', 'psk']:
            if k not in data:
                return SocketMessageResponse(1, k + " parameter not specified")

        log.info("new wifi data: ssid=" + data['ssid'] + " psk=" + data['psk'])
        wifi = 'network={\n  ssid="' + data['ssid'] + '"\n  psk="' + data['psk'] + '"\n}\n'
        wpa_supplicant_txt = open(WPA_SUPPLICANT).read()
        open(WPA_SUPPLICANT, "w").write(wifi + wpa_supplicant_txt)
        return SocketMessageResponse(0, "ok")

    async def listener(self, data_raw: str) -> SocketMessageResponse:
        try:
            data: Dict[str, Union[str, int, float]] = json.loads(data_raw)
        except json.JSONDecodeError:
            log.error("error decoding instruction " + data_raw)
            return SocketMessageResponse(1, "cannot decode instruction")

        if 'instruction' not in data:
            log.warning("received instruction without specifying an instruction name")
            return SocketMessageResponse(1, "instruction not specified")

        instruction = data['instruction']
        log.info("instruction " + instruction + " detected")
        if instruction in ["home", "print", "command", "load", "unload", "move"]:
            error_flag = False
            try:
                if self.actualState["status"]["state"]['text'] != 'Operational':
                    error_flag = True
            except KeyError:
                error_flag = True
            except TypeError:
                error_flag = True
            if error_flag:
                log.warning("instruction not allowed if ucloud is not on an operational state")
                return SocketMessageResponse(1, "printer is not on an operational state")

        try:
            if instruction == 'home':
                return await self.home()

            elif instruction == 'print':
                return await self.print(data)

            elif instruction == 'cancel':
                return await self.cancel(data)

            elif instruction == 'pause':
                return await self.pause(data)

            elif instruction == 'resume':
                return await self.resume()

            elif instruction == 'settings':
                return await self.settings(data)

            elif instruction == 'move':
                return await self.move(data)

            elif instruction == 'command':
                return await self.command(data)

            elif instruction == 'load':
                return await self.load()

            elif instruction == 'unload':
                return await self.unload()

            elif instruction == 'wifi':
                return await self.wifi(data)

            else:
                return SocketMessageResponse(1, data['instruction'] + " instruction not supported")

        except HttpException as e:
            log.warning("octoapi responded " + str(e.code) + ", to " + json.dumps(data))
            return SocketMessageResponse(1, "printer responded " + str(e.code))

        except Exception as e:
            log.error(str(e))
            return SocketMessageResponse(1, str(e))
