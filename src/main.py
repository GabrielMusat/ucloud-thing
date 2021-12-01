import asyncio
import typing as T
from log.logger import _get as init_logger
import threading

from pyargparse import PyArgs

from printer import Printer, UcloudApi, OctoApi
import bluetooth


class Args(PyArgs):
    ucloud_id_path: T.Optional[str]
    ucloud_id: T.Optional[str]
    octoprint_url: str
    octoprint_config_path: str
    file_upload_path: str
    scripts_path: str
    socket_url: str
    files_url: str
    ping_timeout: int = 10
    log_level: str = "INFO"
    bluetooth: bool = True

    def __init__(self):
        super(Args, self).__init__("config.production.yml")
        if self.ucloud_id is None and self.ucloud_id_path is None:
            raise ValueError("ucloud_id or ucloud_id_path must be provided")
        if self.ucloud_id_path:
            with open(self.ucloud_id_path) as f:
                self.ucloud_id = f.read().strip()


async def main(loop: asyncio.AbstractEventLoop):
    args = Args()
    if args.bluetooth:
        threading.Thread(target=bluetooth.main, args=(args.ucloud_id,)).start()
    init_logger(args.log_level)
    print(args)
    octoapi = OctoApi(args.octoprint_url, args.octoprint_config_path)
    ulabapi = UcloudApi(args.socket_url, args.files_url, args.ucloud_id)
    printer = Printer(octoapi, ulabapi, args.file_upload_path, args.scripts_path, args.ping_timeout)
    await printer.ucloud_api.connect(loop)
    await printer.loop()

if __name__ == '__main__':
    main_loop = asyncio.get_event_loop()
    main_loop.run_until_complete(main(main_loop))
