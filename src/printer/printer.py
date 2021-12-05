import asyncio
import copy
import json
import typing as T
import time
from abc import ABC, abstractmethod
from typing import Dict, Any

from aiohttp.client_exceptions import ClientConnectorError

from ucloud_socket import UcloudSocket
from .diff_engine import diffengine
import log
from octoprint_api import OctoApi, HttpException
from file_downloader import FileDownloader


class Printer(UcloudSocket, ABC):
    def __init__(self,
                 url_socket: str,
                 ucloud_id: str,
                 octo_api: OctoApi,
                 file_downloader: FileDownloader,
                 upload_path: str,
                 scripts_path: str,
                 retry_timeout: int = 20,
                 ping_timeout: int = 10
                 ):
        super(Printer, self).__init__(url_socket, ucloud_id)
        self.sentState: Dict[str, Any] = {}
        self.actualState: Dict[str, Any] = {}
        self.upload_path = upload_path
        self.scripts_path = scripts_path
        self.ping_timeout = ping_timeout
        self.retry_timeout = retry_timeout
        self.connected = False
        self.transmit = False
        self.position_known = False
        self.octo_api = octo_api
        self.file_downloader = file_downloader

    async def on_connect(self):
        log.info("socket connected, nice! :)")
        self.connected = True

    async def on_disconnect(self):
        self.connected = False
        log.warning("socket disconnected, oh no! :(")

    async def on_error(self, e: Exception):
        self.connected = False
        log.warning("error on Socket: "+str(e))

    async def on_init(self):
        await self.send_initialization()
        await self.sync()

    async def on_green_light(self):
        log.debug("green light")
        self.transmit = True
        await self.send_initialization()

    async def on_red_light(self):
        log.debug("red light")
        self.transmit = False

    async def on_instruction(self, data: str) -> T.Tuple[int, str]:
        log.info("incoming instruction: "+data)
        code, msg = await self.listener(data)
        if code > 0:
            log.warning("response for instruction with status {}: {}".format(code, msg))
        return code, msg

    async def loop(self):
        last_connection_try = 0
        while True:
            await self.updateActualState()
            status = "unknown"
            try:
                status = self.actualState["status"]["state"]["text"]
            except KeyError:
                pass
            except TypeError:
                pass

            error_code = self.actualState["error"] if "error" in self.actualState else 0
            if time.time() - last_connection_try > self.retry_timeout and (status == 'Closed' or error_code == 409):
                log.warning("closed status detected, forcing connection...")
                last_connection_try = time.time()
                try:
                    await self.octo_api.connect()
                    log.info("printer connected correctly")

                except HttpException:
                    log.warning(f"could not connect printer, trying again in {self.retry_timeout}s")

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

    async def send_initialization(self):
        self.sentState = {}
        self.actualState = {
            'download': {'file': None, 'completion': -1},
            'error': None
        }
        await self.updateActualState()

    async def updateActualState(self):
        try:
            self.actualState["status"] = await self.octo_api.get_status()
            self.actualState["job"] = await self.octo_api.get_job()
            self.actualState["error"] = None
            self.actualState["position"] = "known" if self.position_known else "unknown"

        except HttpException as e:
            self.actualState["status"] = {"state": {"text": "Disconnected"}}
            self.actualState["error"] = e.code
            self.actualState["position"] = "unknown"

        except ClientConnectorError as e:
            log.error("error connecting to octoprint server: "+str(e))
            self.actualState["status"] = {"state": {"text": "Disconnected"}}
            self.actualState["error"] = 450
            self.actualState["position"] = "unknown"

        except Exception as e:
            log.error("unknown error updating status: "+str(e))
            self.actualState["status"] = {"state": {"text": "Disconnected"}}
            self.actualState["error"] = 500
            self.actualState["position"] = "unknown"

    async def sync(self):
        spec = diffengine.diff(self.actualState, self.sentState)
        if len(spec):
            try:
                log.debug(f"syncing {spec}")
                await self.update_status(json.dumps(spec))
                self.sentState = copy.deepcopy(self.actualState)
            except Exception as e:
                log.error(e)

    @abstractmethod
    async def listener(self, data: str) -> T.Tuple[int, str]:
        pass
