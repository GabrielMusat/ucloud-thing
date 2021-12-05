import asyncio
import typing as T
from abc import ABC

import websockets

from .ackWebsockets import Socket, SocketMessageResponse
from ..ucloud_socket import UcloudSocket

GREEN_LIGHT = "green"
RED_LIGHT = "red"
INIT = "init"
INSTRUCTION = "instruction"


class AckWsUcloudSocket(UcloudSocket, ABC):
    def __init__(self, url_socket: str, ucloud_id: str):
        super(AckWsUcloudSocket, self).__init__(url_socket, ucloud_id)
        self.socket: T.Optional[Socket] = None

    async def _on_disconnect(self):
        await self.on_disconnect()
        await self._reconnect()

    async def _on_error(self, e: Exception):
        await self.on_error(e)
        await self._reconnect()

    async def _on_instruction(self, data: str) -> SocketMessageResponse:
        code, msg = await self.on_instruction(data)
        return SocketMessageResponse(code, msg)

    def _link_socket(self, socket: Socket):
        socket.onDisconnect(self._on_disconnect)
        socket.onError(self._on_error)
        socket.on(INIT, lambda _: self.on_init())
        socket.on(GREEN_LIGHT, lambda _: self.on_green_light())
        socket.on(RED_LIGHT, lambda _: self.on_red_light())
        socket.on_sync(INSTRUCTION, self._on_instruction)

    async def _reconnect(self):
        await asyncio.sleep(10)
        self.socket = None
        await self.start()

    async def start(self, loop: asyncio.AbstractEventLoop = asyncio.get_event_loop()) -> None:
        while True:
            try:
                conn = await websockets.connect(self._url_socket, extra_headers={"ucloud-id": self._ucloud_id})
                break
            except Exception as e:
                await self.on_error(e)
                await asyncio.sleep(10)

        self.socket = Socket(conn)
        self._link_socket(self.socket)
        await self.on_connect()
        loop.create_task(self.socket.run())

    async def update_status(self, data: str) -> None:
        await self.socket.emit("update", data)
