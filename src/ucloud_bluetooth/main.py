from __future__ import print_function
import dbus
import dbus.exceptions
import dbus.mainloop.glib
import dbus.service
from .dbus_objects import BluetoothServer
from gi.repository import GLib
import log
from . import ucloud_service


def main():
    dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)
    bus = dbus.SystemBus()

    mainloop = GLib.MainLoop()

    BluetoothServer(
        bus,
        [ucloud_service.UcloudService(bus, 0)],
    )
    log.info("running Glib mainloop for GATT server...")
    mainloop.run()


if __name__ == '__main__':
    main()
