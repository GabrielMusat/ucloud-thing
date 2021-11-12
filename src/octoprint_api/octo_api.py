from abc import ABC, abstractmethod


class OctoApi(ABC):
    @abstractmethod
    async def connect(self) -> None:
        raise NotImplementedError()

    @abstractmethod
    async def get_status(self) -> dict:
        raise NotImplementedError()

    @abstractmethod
    async def get_job(self) -> dict:
        raise NotImplementedError()

    @abstractmethod
    async def post_command(self, command: str) -> None:
        raise NotImplementedError()

    @abstractmethod
    async def post_script(self, script: str) -> None:
        raise NotImplementedError()

    @abstractmethod
    async def print(self, file: str) -> None:
        raise NotImplementedError()

    @abstractmethod
    async def pause(self) -> None:
        raise NotImplementedError()

    @abstractmethod
    async def resume(self) -> None:
        raise NotImplementedError()

    @abstractmethod
    async def cancel(self) -> None:
        raise NotImplementedError()
