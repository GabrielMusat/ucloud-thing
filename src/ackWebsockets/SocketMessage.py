from .exceptions import *

DATA_SEPARATOR = ' '
ID_SEPARATOR = ':'


class SocketMessage:
    def __init__(self, event: str, _id: str, data: str):
        self.event: str = event
        self.id: str = _id
        self.data: str = data

    def encode(self):
        event_id = self.event
        if self.id != '':
            event_id += ID_SEPARATOR+self.id
        return event_id+DATA_SEPARATOR+self.data


def parseIncomingMessage(msg: str) -> SocketMessage:
    event_id_message = msg.split(DATA_SEPARATOR, 1)
    if len(event_id_message) != 2:
        raise IncorrectSocketMessage("split message len is not 2")
    event_id = event_id_message[0].split(ID_SEPARATOR, 1)
    event = event_id[0]
    _id = ""
    if len(event_id) == 2:
        _id = event_id[1]
    message = event_id_message[1]
    return SocketMessage(event, _id, message)
