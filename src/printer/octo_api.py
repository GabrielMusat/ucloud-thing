import json

import aiohttp
import yaml

from exceptions import HttpException


class OctoApi:
    def __init__(self, url: str, config_path: str):
        self.config_path = config_path
        self.url = url
        self.key = yaml.load(open(self.config_path), Loader=yaml.loader.Loader)['api']['key']
        self.session = aiohttp.ClientSession(headers={"X-Api-Key": self.key, "Content-Type": "application/json"})

    async def connect(self) -> None:
        r = await self.session.post(self.url+'/connection', data=json.dumps({"command": "connect"}))
        if not r.status == 200:
            raise HttpException(r.status)

    async def get_status(self) -> dict:
        r = await self.session.get(self.url+'/printer')
        if not r.status == 200:
            raise HttpException(r.status)
        status = await r.json()
        return status

    async def get_job(self) -> dict:
        r = await self.session.get(self.url+'/job')
        if not r.status == 200:
            raise HttpException(r.status)
        status = await r.json()
        return status

    async def post_command(self, command: str) -> None:
        r = await self.session.post(
            url=self.url+'/printer/command',
            data=json.dumps({"commands": [command]})
        )
        if not r.status == 204:
            raise HttpException(r.status)

    async def post_script(self, script: str) -> None:
        r = await self.session.post(
            url=self.url + '/printer/command',
            data=json.dumps({"script": script})
        )
        if not r.status == 204:
            raise HttpException(r.status)

    async def print(self, file: str) -> None:
        r = await self.session.post(
            url=self.url+'/files/local/'+file,
            data=json.dumps({"command": "select", "print": True})
        )
        if not r.status == 204:
            raise HttpException(r.status)

    async def pause(self) -> None:
        r = await self.session.post(
            url=self.url+'/job',
            data=json.dumps({"command": "pause", "action": "pause"})
        )
        if not r.status == 204:
            raise HttpException(r.status)

    async def resume(self) -> None:
        r = await self.session.post(
            url=self.url+'/job',
            data=json.dumps({"command": "pause", "action": "resume"})
        )
        if not r.status == 204:
            raise HttpException(r.status)

    async def cancel(self) -> None:
        r = await self.session.post(self.url+'/job', data=json.dumps({"command": "cancel"}))
        if not r.status == 204:
            raise HttpException(r.status)
