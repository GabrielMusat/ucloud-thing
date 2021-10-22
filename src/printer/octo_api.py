import json

import aiohttp
import yaml

from exceptions import HttpException


class OctoApi:
    def __init__(self, url: str, config_path: str):
        self.config_path = config_path
        self.url = url
        key = yaml.load(open(self.config_path), Loader=yaml.loader.Loader)['api']['key']
        self.headers = {"X-Api-Key": key, "Content-Type": "application/json"}

    async def connect(self) -> None:
        async with aiohttp.ClientSession(headers=self.headers) as session:
            async with session.post(self.url+'/connection', data=json.dumps({"command": "connect"})) as r:
                if not r.status == 200:
                    raise HttpException(r.status)

    async def get_status(self) -> dict:
        async with aiohttp.ClientSession(headers=self.headers) as session:
            async with session.get(self.url+'/printer') as r:
                if not r.status == 200:
                    raise HttpException(r.status)
                status = await r.json()
                return status

    async def get_job(self) -> dict:
        async with aiohttp.ClientSession(headers=self.headers) as session:
            async with session.get(self.url+'/job') as r:
                if not r.status == 200:
                    raise HttpException(r.status)
                status = await r.json()
                return status

    async def post_command(self, command: str) -> None:
        async with aiohttp.ClientSession(headers=self.headers) as session:
            async with session.post(self.url+'/printer/command', data=json.dumps({"commands": [command]})) as r:
                if not r.status == 204:
                    raise HttpException(r.status)

    async def post_script(self, script: str) -> None:
        async with aiohttp.ClientSession(headers=self.headers) as session:
            async with session.post(self.url + '/printer/command', data=json.dumps({"script": script})) as r:
                if not r.status == 204:
                    raise HttpException(r.status)

    async def print(self, file: str) -> None:
        async with aiohttp.ClientSession(headers=self.headers) as session:
            async with session.post(self.url+'/files/local/'+file, data=json.dumps({"command": "select", "print": True})) as r:
                if not r.status == 204:
                    raise HttpException(r.status)

    async def pause(self) -> None:
        async with aiohttp.ClientSession(headers=self.headers) as session:
            async with session.post(self.url+'/job', data=json.dumps({"command": "pause", "action": "pause"})) as r:
                if not r.status == 204:
                    raise HttpException(r.status)

    async def resume(self) -> None:
        async with aiohttp.ClientSession(headers=self.headers) as session:
            async with session.post(self.url+'/job', data=json.dumps({"command": "pause", "action": "resume"})) as r:
                if not r.status == 204:
                    raise HttpException(r.status)

    async def cancel(self) -> None:
        async with aiohttp.ClientSession(headers=self.headers) as session:
            async with session.post(self.url+'/job', data=json.dumps({"command": "cancel"})) as r:
                if not r.status == 204:
                    raise HttpException(r.status)
