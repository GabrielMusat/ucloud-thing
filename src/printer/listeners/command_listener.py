from ackWebsockets import SocketMessageResponse
from .listener import PrinterListener, InstructionListener
import log


class CommandListener(PrinterListener):
    def __init__(self, *args, **kwargs):
        super(CommandListener, self).__init__(*args, **kwargs)
        self.instruction_listeners["command"] = InstructionListener(
            ["Operational"],
            self.command
        )

    async def command(self, data) -> SocketMessageResponse:
        log.info("executing command...")
        if 'command' not in data:
            log.warning("command not specified")
            return SocketMessageResponse(1, "command not specified")

        for cmd in data['command'].split(";"):
            log.info(cmd)
            await self.octo_api.post_command(cmd)
        return SocketMessageResponse(0, "ok")
