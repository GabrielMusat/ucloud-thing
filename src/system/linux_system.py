import os
import typing as T

from .system import System
from .wifi import WifiEntry, write_wifi, read_wifi


class LinuxSystem(System):
    def read_wifi(self) -> T.List[WifiEntry]:
        return read_wifi()

    def write_wifi(self, entries: T.List[WifiEntry]):
        return write_wifi(entries)

    def reboot(self):
        os.system(f"(sleep {2} && reboot) &")
