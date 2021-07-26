import asyncio
import copy
import json
import os
import time
from abc import ABC, abstractmethod
from typing import Dict, Any

from aiohttp.client_exceptions import ClientConnectorError

import diff_engine
import log
from ackWebsockets import SocketMessageResponse
from exceptions import HttpException
from printer.octo_api import OctoApi
from printer.ucloud_api import UcloudApi


class PrinterReceiver(ABC):
    def __init__(self,
                 octo_api: OctoApi,
                 ucloud_api: UcloudApi,
                 upload_path: str,
                 ping_timeout: int = 10
                 ):
        self.sentState: Dict[str, Any] = {}
        self.actualState: Dict[str, Any] = {}
        self.upload_path = upload_path
        self.ping_timeout = ping_timeout
        self.connected = False
        self.transmit = False
        self.octo_api = octo_api
        self.ucloud_api = ucloud_api

        async def connect(*_, **__):
            log.info("socket connected, nice! :)")
            self.connected = True
        self.ucloud_api.on_connect = connect

        async def disconnect(*_, **__):
            self.connected = False
            log.warning("socket disconnected, oh no! :(")
        self.ucloud_api.on_disconnect = disconnect

        async def error(e: Exception):
            self.connected = False
            log.warning("error on Socket: "+str(e))
        self.ucloud_api.on_error = error

        async def init(*_, **__):
            await self.init()
            await self.sync()
        self.ucloud_api.on_init = init

        async def green_light(*_, **__):
            log.debug("green light")
            self.transmit = True
            await init()
        self.ucloud_api.on_green_light = green_light

        async def red_light(*_, **__):
            log.debug("red light")
            self.transmit = False
        self.ucloud_api.on_red_light = red_light

        async def instruction(data: str) -> SocketMessageResponse:
            log.info("incoming instruction: "+data)
            response = await self.listener(data)
            if response.status:
                log.warning("response for instruction with status {}: {}".format(response.status, response.message))
            return response
        self.ucloud_api.on_instruction = instruction

    async def loop(self):
        last_connection_try = 0
        while True:
            await self.updateActualState()
            status = "unknown"
            if "status" in self.actualState \
                    and "state" in self.actualState["status"] \
                    and "text" in self.actualState["status"]["state"]:

                status = self.actualState["status"]["state"]["text"]

            error = self.actualState["error"] if "error" in self.actualState else 0
            if time.time() - last_connection_try > 20 and (status == 'Closed' or error == 409):
                log.warning("closed status detected, forcing connection...")
                last_connection_try = time.time()
                try:
                    await self.octo_api.connect()
                    log.info("printer connected correctly")

                except HttpException:
                    log.warning("could not connect printer, trying again in {20}s")

                except ClientConnectorError as e:
                    log.error("client connection error with octoprint server while trying to connect printer: "+str(e))

                except Exception as e:
                    log.error("unknown error while trying to connect printer: "+str(e))

            if not self.connected:
                log.debug("no sync because not connected")
            elif not self.transmit:
                log.debug("no sync because no green light")
            else:
                await self.sync()

            await asyncio.sleep(1)

    async def init(self):
        self.sentState = {}
        if os.path.isfile("../store.json"):
            self.actualState = {"settings": json.load(open("../store.json"))}
        else:
            self.actualState = {"settings": {"init_gcode": "M851 Z-0.5"}}
            json.dump(self.actualState['settings'], open("../store.json", "w"))
        self.actualState['download'] = {'file': None, 'completion': -1}
        self.actualState['error'] = None

        await self.updateActualState()

    async def updateSettings(self, spec: Dict):
        for k in spec:
            self.actualState["settings"][k] = spec[k]
        json.dump(self.actualState["settings"], open("../store.json", "w"))

    async def updateActualState(self):
        try:
            self.actualState["status"] = await self.octo_api.get_status()
            self.actualState["job"] = await self.octo_api.get_job()
            self.actualState["error"] = None

        except HttpException as e:
            self.actualState["status"] = {"state": {"text": "Disconnected"}}
            self.actualState["error"] = e.code

        except ClientConnectorError as e:
            log.error("error connecting to octoprint server: "+str(e))
            self.actualState["status"] = {"state": {"text": "Disconnected"}}
            self.actualState["error"] = 450

        except Exception as e:
            log.error("unknown error updating status: "+str(e))
            self.actualState["status"] = {"state": {"text": "Disconnected"}}
            self.actualState["error"] = 500

    async def _updateActualState(self):
        try:
            self.actualState["status"] = await self.octo_api.get_status()
            self.actualState["job"] = await self.octo_api.get_job()
            if self.actualState["status"]["state"]['text'] == 'Closed':
                log.warning("closed status detected, forcing connection...")
                await self.octo_api.connect()

        except HttpException as e:
            self.actualState["status"] = {"state": {"text": "Disconnected"}}
            if e.code == 409:
                log.warning("octoprint returned 409 while requesting status, forcing connection...")
                await self.octo_api.connect()

        except ClientConnectorError as e:
            log.error("error connecting to octoprint: "+str(e))
            self.actualState["status"] = {"state": {"text": "Disconnected"}}

    async def sync(self):
        spec = diff_engine.diff(self.actualState, self.sentState)
        if len(spec):
            try:
                log.debug(f"syncing {spec}")
                await self.ucloud_api.update_status(spec)
                self.sentState = copy.deepcopy(self.actualState)
            except Exception as e:
                log.error(e)

    @abstractmethod
    async def listener(self, data_raw: str) -> SocketMessageResponse:
        pass
