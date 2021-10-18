from ackWebsockets import SocketMessageResponse
from .listener import PrinterListener, InstructionListener
import log

DEFAULT_SPEED = 1000


class MoveListener(PrinterListener):
    def __init__(self, *args, **kwargs):
        super(MoveListener, self).__init__(*args, **kwargs)
        self.instruction_listeners["move"] = InstructionListener(
            ["Operational"],
            self.move
        )

    async def move(self, data) -> SocketMessageResponse:
        log.info("moving...")
        for k in ['axis', 'distance']:
            if k not in data:
                return SocketMessageResponse(1, k + " not specified")

        speed = DEFAULT_SPEED if "speed" not in data else data["speed"]
        for cmd in ['G91', 'G1 {}{} F{}'.format(data['axis'], data['distance'], speed), 'G90']:
            log.info("executing command from move command chain " + cmd + "...")
            await self.octo_api.post_command(cmd)
        return SocketMessageResponse(0, "ok")
