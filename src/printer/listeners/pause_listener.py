import os

from ackWebsockets import SocketMessageResponse
from .listener import PrinterListener, InstructionListener
import log

DEFAULT_AFTER_PAUSE_SCRIPT = '''
{% if pause_position.x is not none %}
; relative XYZE
G91
M83

; retract filament, move Z slightly upwards
G1 Z+15 E-5 F4500

; absolute XYZE
M82
G90

; move to a safe rest position, adjust as necessary
G1 X20 Y20
{% endif %}
'''


class PauseListener(PrinterListener):
    def __init__(self, *args, **kwargs):
        super(PauseListener, self).__init__(*args, **kwargs)
        self.instruction_listeners["pause"] = InstructionListener(
            ["Printing"],
            self.pause
        )

    async def pause(self, data) -> SocketMessageResponse:
        after_pause = DEFAULT_AFTER_PAUSE_SCRIPT if "after" not in data else data["after"]
        log.info("pausing print...")
        if not os.path.isdir(self.scripts_path):
            os.makedirs(self.scripts_path, exist_ok=True)
        script_path = os.path.join(self.scripts_path, "afterPrintPaused")
        with open(script_path, "w") as f:
            f.write(after_pause)
        await self.octo_api.pause()
        return SocketMessageResponse(0, "ok")
