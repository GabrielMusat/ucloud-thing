import dbus

import os
from .dbus_objects import Characteristic, Service
import typing as T
from .wifi_file import WifiEntry, WifiFile
import log
import json


def str_2_dbus_bytes(string: str) -> T.List[dbus.Byte]:
    return [dbus.Byte(ord(c)) for c in string]


def dbus_bytes_2_str(dbus_bytes: T.List[dbus.Byte]) -> str:
    return "".join([chr(c) for c in dbus_bytes])


class UcloudService(Service):
    UUID_SUFFIX = '12345678'

    def __init__(self, ucloud_id: str, bus, index):
        if len(ucloud_id) != 24:
            raise ValueError("ucloud_id length must be 24")
        self.UUID = f"{ucloud_id[0:8]}-" \
                    f"{ucloud_id[8:12]}-" \
                    f"{ucloud_id[12:16]}-" \
                    f"{ucloud_id[16:20]}-" \
                    f"{ucloud_id[20:24]}{self.UUID_SUFFIX}"
        super().__init__(
            bus,
            index,
            self.UUID,
            True
        )
        self.add_characteristic(RebootCharacteristic(bus, 0, self))
        self.add_characteristic(WifiCharacteristic(bus, 1, self))


class RebootCharacteristic(Characteristic):
    UUID = '12345678-1234-5678-1234-56789abcdef6'

    def __init__(self, bus, index, service):
        super().__init__(
            bus,
            index,
            self.UUID,
            ['read', 'write', 'writable-auxiliaries'],
            service
        )

    def WriteValue(self, value, options):
        log.info('RebootCharacteristic Write: ' + dbus_bytes_2_str(value))
        decoded = dbus_bytes_2_str(value)
        if decoded == "reboot":
            log.info("rebooting system...")
            os.system(f"(sleep {2} && reboot) &")
        else:
            log.warning(f"received non reboot command: {decoded}")


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

    def ReadValue(self, options):
        to_return = [x.__dict__() for x in self.wifi_file.parse()]
        log.info(f'WifiCharacteristic Read: {to_return}')
        return str_2_dbus_bytes(json.dumps(to_return))

    def WriteValue(self, value, options):
        log.info('WifiCharacteristic Write: ' + dbus_bytes_2_str(value))
        decoded = json.loads(dbus_bytes_2_str(value))
        assert type(decoded) == list, log.warning("received new value is not list")
        new_value = []
        for i, d in enumerate(decoded):
            assert type(d) == dict, log.warning(f"entry {i+1} is not dict")
            assert "ssid" in d, log.warning(f"entry {i+1} has no ssid")
            assert "psk" in d, log.warning(f"entry {i+1} has no psk")
            new_value.append(WifiEntry(d["ssid"], d["psk"]))

        self.wifi_file.update_wifi(new_value)
