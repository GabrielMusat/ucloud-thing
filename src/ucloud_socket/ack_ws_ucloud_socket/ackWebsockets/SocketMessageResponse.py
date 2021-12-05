import json


class SocketMessageResponse:
    def __init__(self, status: int, message: str):
        self.status: int = status
        self.message: str = message

    def encode(self):
        return json.dumps({"status": self.status, "message": self.message})


def parseSocketMessageResponse(msg: str) -> SocketMessageResponse:
    try:
        parsed = json.loads(msg)
        status = parsed["status"]
        message = parsed["message"]
    except json.JSONDecodeError or KeyError:
        return SocketMessageResponse(1, "invalid response")

    return SocketMessageResponse(status, message)
