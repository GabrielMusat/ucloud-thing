import typing as T
from abc import ABC

import log
from .listener import PrinterListener, InstructionListener


class CommandListenerMixin(PrinterListener, ABC):
    def __init__(self, *args, **kwargs):
        super(CommandListenerMixin, self).__init__(*args, **kwargs)
        self.instruction_listeners["command"] = InstructionListener(
            ["Operational"],
            self.command
        )

    async def command(self, data: dict) -> T.Tuple[int, str]:
        log.info("executing command...")
        if 'command' not in data:
            log.warning("command not specified")
            return 1, "command not specified"
        command: str = data['command']
        for cmd in command.split(";"):
            if ("G1 " in cmd or "G0 " in cmd) and not self.position_known:
                return 1, "position unknown"

        for cmd in command.split(";"):
            log.info(cmd)
            if cmd.upper().strip() == "G28":
                self.position_known = True
            await self.octo_api.post_command(cmd)
        return 0, "ok"
