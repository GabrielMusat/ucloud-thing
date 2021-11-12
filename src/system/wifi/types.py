class WifiEntry:
    def __init__(self, ssid: str, psk: str):
        self.ssid = ssid
        self.psk = psk

    def __dict__(self):
        return {"ssid": self.ssid, "psk": self.psk}