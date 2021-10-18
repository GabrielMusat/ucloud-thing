from .printer_receiver import OctoApi, UcloudApi, PrinterReceiver
from .listeners.cancel_listener import CancelListener
from .listeners.command_listener import CommandListener
from .listeners.home_listener import HomeListener
from .listeners.pause_listener import PauseListener
from .listeners.print_listener import PrintListener
from .listeners.resume_listener import ResumeListener
from .listeners.move_listener import MoveListener


class Printer(
    CancelListener,
    CommandListener,
    HomeListener,
    PauseListener,
    PrintListener,
    ResumeListener,
    MoveListener,

    PrinterReceiver
):
    pass
