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
        command: str = data['command']
        for cmd in command.split(";"):
            if ("G1 " in cmd or "G0 " in cmd) and not self.position_known:
                return SocketMessageResponse(1, "position unknown")

        for cmd in command.split(";"):
            log.info(cmd)
            if cmd.upper().strip() == "G28":
                self.position_known = True
            await self.octo_api.post_command(cmd)
        return SocketMessageResponse(0, "ok")
