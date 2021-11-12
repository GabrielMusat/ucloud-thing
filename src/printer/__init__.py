from abc import ABC

from .printer import Printer as _Printer
from .listeners.cancel_listener import CancelListenerMixin
from .listeners.command_listener import CommandListenerMixin
from .listeners.home_listener import HomeListenerMixin
from .listeners.pause_listener import PauseListenerMixin
from .listeners.print_listener import PrintListenerMixin
from .listeners.resume_listener import ResumeListenerMixin
from .listeners.move_listener import MoveListenerMixin


class Printer(
    CancelListenerMixin,
    CommandListenerMixin,
    HomeListenerMixin,
    PauseListenerMixin,
    PrintListenerMixin,
    ResumeListenerMixin,
    MoveListenerMixin,

    _Printer,
    ABC
):
    pass
