import typing as T
from abc import ABC, abstractmethod
from .wifi import WifiEntry


class System(ABC):
    @abstractmethod
    def reboot(self):
        raise NotImplemented()

    @abstractmethod
    def read_wifi(self) -> T.List[WifiEntry]:
        raise NotImplemented()

    @abstractmethod
    def write_wifi(self, entries: T.List[WifiEntry]):
        raise NotImplemented()
