import typing as T

from .system import System
from .wifi import WifiEntry


class MockSystem(System):
    def __init__(self):
        self.entries: T.List[WifiEntry] = []

    def read_wifi(self) -> T.List[WifiEntry]:
        return self.entries

    def write_wifi(self, entries: T.List[WifiEntry]):
        self.entries = entries

    def reboot(self):
        print("oh no! rebooooting...")
