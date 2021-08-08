import dbus

import os
from .dbus_objects import Characteristic, Service
import typing as T
from .wifi_file import WifiEntry, WifiFile
import log
import json

SECS_BEFORE_REBOOT = 3


class UcloudService(Service):
    UUID = '12345678-1234-5678-1234-56789abcdef0'

    def __init__(self, bus, index):
        super().__init__(
            bus,
            index,
            self.UUID,
            True
        )
        self.add_characteristic(WifiCharacteristic(bus, 0, self))


class WifiCharacteristic(Characteristic):
    UUID = '12345678-1234-5678-1234-56789abcdef5'

    def __init__(self, bus, index, service):
        super().__init__(
            bus,
            index,
            self.UUID,
            ['read', 'write', 'writable-auxiliaries'],
            service
        )
        self.wifi_file = WifiFile()

    @staticmethod
    def str_2_dbus_bytes(string: str) -> T.List[dbus.Byte]:
        return [dbus.Byte(ord(c)) for c in string]

    @staticmethod
    def dbus_bytes_2_str(dbus_bytes: T.List[dbus.Byte]) -> str:
        return "".join([chr(c) for c in dbus_bytes])

    def ReadValue(self, options):
        to_return = [x.__dict__() for x in self.wifi_file.parse()]
        log.info(f'WifiCharacteristic Read: {to_return}')
        return self.str_2_dbus_bytes(json.dumps(to_return))

    def WriteValue(self, value, options):
        log.info('WifiCharacteristic Write: ' + self.dbus_bytes_2_str(value))
        decoded = json.loads(self.dbus_bytes_2_str(value))
        assert type(decoded) == list, log.warning("received new value is not list")
        new_value = []
        for i, d in enumerate(decoded):
            assert type(d) == dict, log.warning(f"entry {i+1} is not dict")
            assert "ssid" in d, log.warning(f"entry {i+1} has no ssid")
            assert "psk" in d, log.warning(f"entry {i+1} has no psk")
            new_value.append(WifiEntry(d["ssid"], d["psk"]))

        self.wifi_file.update_wifi(new_value)
        os.system(f"(sleep {5} && reboot) &")
