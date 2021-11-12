import typing as T
from abc import ABC

import log
from .listener import PrinterListener, InstructionListener

DEFAULT_SPEED = 1000


class MoveListenerMixin(PrinterListener, ABC):
    def __init__(self, *args, **kwargs):
        super(MoveListenerMixin, self).__init__(*args, **kwargs)
        self.instruction_listeners["move"] = InstructionListener(
            ["Operational"],
            self.move
        )

    async def move(self, data) -> T.Tuple[int, str]:
        log.info("moving...")
        for k in ['axis', 'distance']:
            if k not in data:
                return 1, k + " not specified"
        if not self.position_known:
            return 1, "position unknown"

        speed = DEFAULT_SPEED if "speed" not in data else data["speed"]
        for cmd in ['G91', 'G1 {}{} F{}'.format(data['axis'], data['distance'], speed), 'G90']:
            log.info("executing command from move command chain " + cmd + "...")
            await self.octo_api.post_command(cmd)
        return 0, "ok"
