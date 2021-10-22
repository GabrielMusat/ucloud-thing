import os

from ackWebsockets import SocketMessageResponse
from .listener import PrinterListener, InstructionListener
import log

DEFAULT_BEFORE_RESUME_SCRIPT = '''
{% if pause_position.x is not none %}
; relative extruder
M83

; prime nozzle
G1 E-5 F4500
G1 E5 F4500
G1 E5 F4500

; absolute E
M82

; absolute XYZ
G90

; reset E
G92 E{{ pause_position.e }}

; move back to pause position XYZ
G1 X{{ pause_position.x }} Y{{ pause_position.y }} Z{{ pause_position.z }} F4500

; reset to feed rate before pause if available
{% if pause_position.f is not none %}G1 F{{ pause_position.f }}{% endif %}
{% endif %}
'''


class ResumeListener(PrinterListener):
    def __init__(self, *args, **kwargs):
        super(ResumeListener, self).__init__(*args, **kwargs)
        self.instruction_listeners["resume"] = InstructionListener(
            ["Paused"],
            self.resume
        )

    async def resume(self, data) -> SocketMessageResponse:
        before_resume = DEFAULT_BEFORE_RESUME_SCRIPT if "before" not in data else data["before"]
        log.info("resuming print...")
        if not os.path.isdir(self.scripts_path):
            os.makedirs(self.scripts_path, exist_ok=True)
        script_path = os.path.join(self.scripts_path, "beforePrintResumed")
        with open(script_path, "w") as f:
            f.write(before_resume)
        os.chmod(before_resume, 777)
        await self.octo_api.resume()
        return SocketMessageResponse(0, "ok")
