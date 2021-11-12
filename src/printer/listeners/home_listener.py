import typing as T
from abc import ABC

import log
from .listener import PrinterListener, InstructionListener


class HomeListenerMixin(PrinterListener, ABC):
    def __init__(self, *args, **kwargs):
        super(HomeListenerMixin, self).__init__(*args, **kwargs)
        self.instruction_listeners["home"] = InstructionListener(
            ["Operational"],
            self.home
        )

    async def home(self, data: dict) -> T.Tuple[int, str]:
        log.info("homing...")
        await self.octo_api.post_command("G28")
        self.position_known = True
        return 0, "ok"
