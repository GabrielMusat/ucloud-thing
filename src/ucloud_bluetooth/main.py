from __future__ import print_function
import dbus
import dbus.exceptions
import dbus.mainloop.glib
import dbus.service
from .dbus_objects import BluetoothServer
from gi.repository import GLib
import log
from . import ucloud_service


def main(ucloud_id: str):
    dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)
    try:
        bus = dbus.SystemBus()
    except dbus.exceptions.DBusException as e:
        log.error(f"could not start dbus: {e}")
        return

    mainloop = GLib.MainLoop()

    BluetoothServer(
        bus,
        [ucloud_service.UcloudService(ucloud_id, bus, 0)],
    )
    log.info("running Glib mainloop for GATT server...")
    mainloop.run()

