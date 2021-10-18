import asyncio
import os
import time
from typing import Dict

import aiofiles

from ackWebsockets import SocketMessageResponse
from .listener import PrinterListener, InstructionListener
import log


class PrintListener(PrinterListener):
    def __init__(self, *args, **kwargs):
        super(PrintListener, self).__init__(*args, **kwargs)
        self.instruction_listeners["print"] = InstructionListener(
            ["Operational"],
            self.print
        )

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
        existing_files = os.listdir(os.path.split(gcode)[0])
        if len(existing_files) > 10:
            log.warning("deleting files "+", ".join(existing_files))
            for file in existing_files:
                try:
                    os.remove(file)
                except Exception as e:
                    log.error("error deleting file "+file+": "+str(e))
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
            msg = "file " + self.actualState['download']['file'] + " has already been scheduled to download and print"
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
            log.info("downloading file from " + download_path + " to " + upload_path + "...")
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
