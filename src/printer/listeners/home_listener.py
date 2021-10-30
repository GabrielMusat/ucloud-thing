from ackWebsockets import SocketMessageResponse
from .listener import PrinterListener, InstructionListener
import log


class HomeListener(PrinterListener):
    def __init__(self, *args, **kwargs):
        super(HomeListener, self).__init__(*args, **kwargs)
        self.instruction_listeners["home"] = InstructionListener(
            ["Operational"],
            self.home
        )

    async def home(self, data) -> SocketMessageResponse:
        log.info("homing...")
        await self.octo_api.post_command("G28")
        self.position_known = True
        return SocketMessageResponse(0, "ok")
