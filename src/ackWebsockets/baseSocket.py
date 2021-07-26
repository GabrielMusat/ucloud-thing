import asyncio
import typing as T
from _md5 import md5

import websockets
from websockets.client import WebSocketClientProtocol
from websockets.server import WebSocketServerProtocol

from .SocketMessage import SocketMessage, parseIncomingMessage
from .SocketMessageResponse import SocketMessageResponse, parseSocketMessageResponse
from .exceptions import IncorrectSocketMessage


class Socket:
    def __init__(self, conn: T.Union[WebSocketClientProtocol, WebSocketServerProtocol]):
        self.send: T.List[SocketMessage] = []
        self.on_disconnect: T.Union[None, T.Callable[[], T.Awaitable[None]]] = None
        self.on_error: T.Union[None, T.Callable[[Exception], T.Awaitable[None]]] = None
        self.async_listeners: T.Dict[str, T.Callable[[str], T.Awaitable[None]]] = {}
        self.sync_listeners: T.Dict[str, T.Callable[[str], T.Awaitable[SocketMessageResponse]]] = {}
        self.conn = conn
        self.label: str = "server" if isinstance(conn, websockets.WebSocketServerProtocol) else "client"

    async def run(self):
        await asyncio.wait([self.readPump()])

    def onDisconnect(self, handler: T.Callable[[], T.Awaitable[None]]):
        self.on_disconnect = handler

    def onError(self, handler: T.Callable[[Exception], T.Awaitable[None]]):
        self.on_error = handler

    def on_sync(self, event: str, handler: T.Callable[[str], T.Awaitable[SocketMessageResponse]]):
        self.sync_listeners[event] = handler

    def on(self, event: str, handler: T.Callable[[str], T.Awaitable[None]]):
        self.async_listeners[event] = handler

    def off(self, event: str):
        if event in self.sync_listeners:
            del self.sync_listeners[event]
        if event in self.async_listeners:
            del self.async_listeners[event]

    async def readPump(self):
        while True:
            try:
                msg = await self.conn.recv()
            except websockets.ConnectionClosedOK:
                if self.on_disconnect:
                    await self.on_disconnect()
                break
            except websockets.ConnectionClosedError as e:
                if self.on_error:
                    await self.on_error(e)
                break

            try:
                incoming_message = parseIncomingMessage(msg)
            except IncorrectSocketMessage as e:
                print(f"{self.label} Warning - incorrect socket message", e)
                continue

            if incoming_message.event in self.sync_listeners:
                socket_message_response = await self.sync_listeners[incoming_message.event](incoming_message.data)
                if len(incoming_message.id):
                    await self.emit(incoming_message.id, socket_message_response.encode())
            elif incoming_message.event in self.async_listeners:
                await self.async_listeners[incoming_message.event](incoming_message.data)

    async def emit(self, event: str, data: str):
        await self.conn.send(SocketMessage(event, "", data).encode())

    async def emitSync(self, event: str, data: str) -> SocketMessageResponse:
        _id = md5(data.encode()).hexdigest()
        response: T.List[SocketMessageResponse] = []
        async def handler(r: str): response.append(parseSocketMessageResponse(r))

        self.on(_id, handler)
        await self.conn.send(SocketMessage(event, _id, data).encode())
        for _ in range(10000):
            if len(response) > 0:
                r = response[0]
                break
            await asyncio.sleep(0.001)
        else:
            r = SocketMessageResponse(1, "timeout waiting for response")
        self.off(_id)
        return r

    async def close(self, code: int, reason: str):
        await self.conn.close(code, reason)
