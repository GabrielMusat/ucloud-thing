from abc import ABC, abstractmethod

import aiohttp


class FileDownloader(ABC):
    def __init__(self, url: str):
        self.url: str = url

    @abstractmethod
    def set_auth(self, auth: str):
        raise NotImplementedError()

    @abstractmethod
    async def exists(self, file: str) -> bool:
        raise NotImplementedError()

    @abstractmethod
    async def download(self, file: str) -> aiohttp.ClientResponse:
        raise NotImplementedError()
