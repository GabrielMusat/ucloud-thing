import typing as T

import dbus

from . import utils
from .advertisement import Advertisement
from .application import Application
from .constants import *
from .exceptions import *
from .service import Service


class AppAdvertisement(Advertisement):
    def __init__(self, bus: dbus.Bus, services: T.List[Service], index: int):
        super().__init__(bus, index, 'peripheral')
        for service in services:
            self.add_service_uuid(service.uuid)
        self.include_tx_power = True


class BluetoothServer:
    def __init__(self,
                 bus: dbus.Bus,
                 services: T.List[Service],
                 index: int = 0):
        self.init_advertiser(bus, services, index)
        self.init_gatt(bus, services)

    def init_advertiser(
            self,
            bus: dbus.Bus,
            services: T.List[Service],
            index: int
    ):
        adapter = utils.find_adapter(bus)
        if not adapter:
            raise Exception('LEAdvertisingManager1 interface not found')

        adapter_props = dbus.Interface(bus.get_object(BLUEZ_SERVICE_NAME, adapter), DBUS_PROP_IFACE)
        adapter_props.Set("org.bluez.Adapter1", "Powered", dbus.Boolean(1))
        ad_manager = dbus.Interface(
            bus.get_object(BLUEZ_SERVICE_NAME, adapter),
            LE_ADVERTISING_MANAGER_IFACE
        )
        advertisement = AppAdvertisement(bus, services, index)

        ad_manager.RegisterAdvertisement(
            advertisement.get_path(),
            {},
            reply_handler=lambda: print('Advertisement registered'),
            error_handler=self.on_error
        )

    def init_gatt(
        self,
        bus: dbus.Bus,
        services: T.List[Service]
    ):
        adapter = utils.find_adapter(bus)
        if not adapter:
            raise Exception('GattManager1 interface not found')

        service_manager = dbus.Interface(
            bus.get_object(BLUEZ_SERVICE_NAME, adapter),
            GATT_MANAGER_IFACE
        )

        app = Application(bus, services)

        service_manager.RegisterApplication(
            app.get_path(),
            {},
            reply_handler=lambda: print('GATT application registered'),
            error_handler=self.on_error
        )

    def on_error(self, error):
        print(error)
        exit(1)


