import json
from abc import ABC

from exceptions import HttpException
from typing import Dict, Union, List, Awaitable, Callable, Any, Tuple
import log
from ..printer import Printer


class InstructionListener:
    def __init__(self,
                 statuses: Union[None, List[str]],
                 callback: Callable[[Dict[str, Any]], Awaitable[Tuple[int, str]]]):
        self.statuses: Union[None, List[str]] = statuses
        self.callback: Callable[[Dict[str, Any]], Awaitable[Tuple[int, str]]] = callback


class PrinterListener(Printer, ABC):
    def __init__(self, *args, **kwargs):
        super(PrinterListener, self).__init__(*args, **kwargs)
        self.instruction_listeners: Dict[str, InstructionListener] = {}

    async def listener(self, data_raw: str) -> Tuple[int, str]:
        try:
            data: Dict[str, Union[str, int, float]] = json.loads(data_raw)
        except json.JSONDecodeError:
            log.error("error decoding instruction " + data_raw)
            return 1, "cannot decode instruction"

        if 'instruction' not in data:
            log.warning("received instruction without specifying an instruction name")
            return 1, "instruction not specified"

        instruction = data['instruction']
        if instruction not in self.instruction_listeners:
            log.warning(data['instruction'] + " instruction not supported")
            return 1, data['instruction'] + " instruction not supported"
        log.info("instruction " + instruction + " detected")
        if instruction in self.instruction_listeners:
            actual_state = None
            try:
                actual_state = self.actualState["status"]["state"]['text']
            except KeyError:
                pass
            except TypeError:
                pass

            allowed_states = self.instruction_listeners[instruction].statuses
            if actual_state not in allowed_states:
                log.warning("instruction '" +
                            instruction +
                            "' not allowed if ucloud is not in one of the following states: " +
                            str(", ".join(allowed_states)))
                return 1, "printer is not on an operational state"
        else:
            log.warning(data['instruction'] + " instruction not supported")
            return 1, data['instruction'] + " instruction not supported"

        try:
            return await self.instruction_listeners[instruction].callback(data)
        except HttpException as e:
            log.warning("octoapi responded " + str(e.code) + ", to " + json.dumps(data))
            return 1, "printer responded " + str(e.code)
        except Exception as e:
            log.error(str(e))
            return 1, str(e)
