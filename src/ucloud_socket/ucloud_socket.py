from abc import ABC, abstractmethod
import typing as T


class UcloudSocket(ABC):
    def __init__(self, url_socket: str, ucloud_id: str):
        self._url_socket: str = url_socket
        self._ucloud_id: str = ucloud_id

    @abstractmethod
    async def start(self):
        raise NotImplementedError()

    @abstractmethod
    async def on_connect(self):
        raise NotImplementedError()

    @abstractmethod
    async def on_init(self):
        raise NotImplementedError()

    @abstractmethod
    async def on_green_light(self):
        raise NotImplementedError()

    @abstractmethod
    async def on_red_light(self):
        raise NotImplementedError()

    @abstractmethod
    async def on_disconnect(self):
        raise NotImplementedError()

    @abstractmethod
    async def on_error(self, e: Exception):
        raise NotImplementedError()

    @abstractmethod
    async def on_instruction(self, data: str) -> T.Tuple[int, str]:  # T.Tuple[STATUS_CODE, STATUS_MSG]
        raise NotImplementedError()

    @abstractmethod
    async def update_status(self, spec: str) -> None:
        raise NotImplementedError()
