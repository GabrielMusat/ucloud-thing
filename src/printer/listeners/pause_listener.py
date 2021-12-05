import os
import typing as T
from abc import ABC

import log
from .listener import PrinterListener, InstructionListener

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


class PauseListenerMixin(PrinterListener, ABC):
    def __init__(self, *args, **kwargs):
        super(PauseListenerMixin, self).__init__(*args, **kwargs)
        self.instruction_listeners["pause"] = InstructionListener(
            ["Printing"],
            self.pause
        )

    async def pause(self, data) -> T.Tuple[int, str]:
        after_pause = DEFAULT_AFTER_PAUSE_SCRIPT if "after" not in data else data["after"]
        log.info("pausing print...")
        if not os.path.isdir(self.scripts_path):
            os.makedirs(self.scripts_path, exist_ok=True)
        script_path = os.path.join(self.scripts_path, "afterPrintPaused")
        with open(script_path, "w") as f:
            f.write(after_pause)
        os.chmod(script_path, 0o777)
        await self.octo_api.pause()
        return 0, "ok"
