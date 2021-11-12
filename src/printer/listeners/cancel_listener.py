import typing as T
from abc import ABC

import log
from .listener import PrinterListener, InstructionListener

DEFAULT_AFTER_CANCEL = "G91; G1 Z+200; G90"


class CancelListenerMixin(PrinterListener, ABC):
    def __init__(self, *args, **kwargs):
        super(CancelListenerMixin, self).__init__(*args, **kwargs)
        self.instruction_listeners["cancel"] = InstructionListener(
            ["Printing"],
            self.cancel
        )

    async def cancel(self, data: dict) -> T.Tuple[int, str]:
        after_cancel = DEFAULT_AFTER_CANCEL if "after" not in data else data["after"]
        log.info("cancelling print...")

        await self.octo_api.cancel()
        if after_cancel:
            log.info("executing after cancel...")
            for cmd in after_cancel.split(";"):
                log.info(cmd)
                await self.octo_api.post_command(cmd)
        return 0, "ok"
