import asyncio
import json
import typing as T

import aiohttp
import websockets

import ackWebsockets

GREEN_LIGHT = "green"
RED_LIGHT = "red"
INIT = "init"
INSTRUCTION = "instruction"


class UcloudApi:
    def __init__(self, url_socket: str, url_backend: str, ucloud_id: str):
        self.url_socket: str = url_socket
        self.url_backend: str = url_backend
        self.ucloud_id: str = ucloud_id
        self.socket: T.Union[None, ackWebsockets.Socket] = None
        self.session = aiohttp.ClientSession(headers={"ucloud-id": self.ucloud_id})
        async def dummy(*_, **__): return
        self.on_connect: T.Callable[[], T.Awaitable[None]] = dummy
        self.on_init: T.Callable[[str], T.Awaitable[None]] = dummy
        self.on_green_light: T.Callable[[str], T.Awaitable[None]] = dummy
        self.on_red_light: T.Callable[[str], T.Awaitable[None]] = dummy
        self.on_unauthorized: T.Callable[[str], T.Awaitable[None]] = dummy
        self.on_disconnect: T.Callable[[], T.Awaitable[None]] = dummy
        self.on_error: T.Callable[[Exception], T.Awaitable[None]] = dummy
        self.on_instruction: T.Callable[[str], T.Awaitable[ackWebsockets.SocketMessageResponse]] = dummy

    async def exists(self, file: str, token: str) -> bool:
        url = self.url_backend + '/files/private/' + file
        r: aiohttp.ClientResponse = await self.session.head(url, headers={"authorization": token})
        return r.status == 200

    async def download(self, file: str, token: str) -> aiohttp.ClientResponse:
        url = self.url_backend + '/files/private/' + file
        return await self.session.get(url, headers={"authorization": token})

    async def reconnect(self):
        self.socket = None
        await asyncio.sleep(10)
        await self.connect()

    async def connect(self, loop: asyncio.AbstractEventLoop = asyncio.get_event_loop()) -> None:
        while True:
            try:
                conn = await websockets.connect(self.url_socket, extra_headers={"ucloud-id": self.ucloud_id})
                self.socket = ackWebsockets.Socket(conn)
                await self.on_connect()

                async def on_disconnect():
                    await self.on_disconnect()
                    await self.reconnect()
                self.socket.onDisconnect(on_disconnect)

                async def on_error(ex: Exception):
                    await self.on_error(ex)
                    await self.reconnect()
                self.socket.onError(on_error)
                self.socket.on(INIT, self.on_init)
                self.socket.on(GREEN_LIGHT, self.on_green_light)
                self.socket.on(RED_LIGHT, self.on_red_light)
                self.socket.on_sync(INSTRUCTION, self.on_instruction)
                loop.create_task(self.socket.run())
                break

            except Exception as e:  # todo: catch concrete exceptions
                await self.on_error(e)
                self.socket = None
                await asyncio.sleep(10)

    async def update_status(self, spec: dict) -> None:
        await self.socket.emit("update", json.dumps(spec))
