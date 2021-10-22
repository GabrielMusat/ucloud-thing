import typing as T

NOWHERE = 0
IN_WIFI_ENTRY = 1

WRITE_WIFI_FILE = "/boot/wpa_supplicant.conf"
READ_WIFI_FILE = "/etc/wpa_supplicant/wpa_supplicant.conf"

NETWORK_START = "network={"
NETWORK_END = "}"
SSID = "ssid"
PSK = "psk"


class WifiEntry:
    def __init__(self, ssid: str, psk: str):
        self.ssid = ssid
        self.psk = psk

    def __dict__(self):
        return {"ssid": self.ssid, "psk": self.psk}


class WifiFile:
    def update_wifi(self, wifi_entries: T.List[WifiEntry]):
        new_file = ""
        for wifi in wifi_entries:
            new_file += f'{NETWORK_START}\n' \
                        f'  {SSID}="{wifi.ssid}"\n' \
                        f'  {PSK}="{wifi.psk}"\n' \
                        f'{NETWORK_END}\n'
        state = NOWHERE
        with open(READ_WIFI_FILE) as f:
            for org_line in f.readlines():
                line = org_line.strip()
                if line == NETWORK_START:
                    state = IN_WIFI_ENTRY
                    continue
                elif line == NETWORK_END:
                    state = NOWHERE
                    continue
                if state == NOWHERE:
                    new_file += org_line
        with open(WRITE_WIFI_FILE, "w") as f:
            f.write(new_file)

    def parse(self) -> T.List[WifiEntry]:
        state = NOWHERE
        ssid = ""
        psk = ""
        new_wifi = []
        with open(READ_WIFI_FILE) as f:
            for line in f.readlines():
                line = line.strip()
                if line == NETWORK_START:
                    state = IN_WIFI_ENTRY
                    continue
                if line == NETWORK_END:
                    state = NOWHERE
                    if ssid and psk:
                        new_wifi.append(WifiEntry(ssid, psk))
                    ssid, psk = "", ""
                    continue
                if state == IN_WIFI_ENTRY:
                    if line.startswith(SSID):
                        split = line.split("=")
                        if len(split) != 2:
                            continue
                        ssid = split[1].strip('"')
                    if line.startswith(PSK):
                        split = line.split("=")
                        if len(split) != 2:
                            continue
                        psk = split[1].strip('"')
        return new_wifi
