from __future__ import print_function
import dbus
import dbus.exceptions
import dbus.mainloop.glib
import dbus.service
from .dbus_objects import BluetoothServer
from gi.repository import GLib
import log
from . import ucloud_service
from system import System


def main(ucloud_id: str, system: System):
    dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)
    try:
        bus = dbus.SystemBus()
    except dbus.exceptions.DBusException as e:
        log.error(f"could not start dbus: {e}")
        return

    mainloop = GLib.MainLoop()

    BluetoothServer(
        bus,
        [ucloud_service.UcloudService(system, ucloud_id, bus, 0)],
    )
    log.info("running Glib mainloop for GATT server...")
    mainloop.run()

