from contextlib import asynccontextmanager

import aiohttp

from .file_downloader import FileDownloader


class UcloudBackendFileDownloader(FileDownloader):
    def __init__(self, url: str):
        super(UcloudBackendFileDownloader, self).__init__(url)
        self.token = ""

    def set_auth(self, auth: str):
        self.token = auth

    async def exists(self, file: str) -> bool:
        url = self.url + '/files/private/' + file
        async with aiohttp.ClientSession(headers={"authorization": self.token}) as session:
            async with session.head(url, ssl=False) as r:
                return r.status == 200

    @asynccontextmanager
    async def download(self, file: str) -> aiohttp.ClientResponse:
        url = self.url + '/files/private/' + file
        async with aiohttp.ClientSession(headers={"authorization": self.token}) as session:
            async with session.get(url, ssl=False) as r:
                yield r
