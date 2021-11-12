import asyncio
import typing as T
from log.logger import _get as init_logger
import threading

from pyargparse import PyArgs

from printer import Printer
from ucloud_socket import AckWsUcloudSocket
from octoprint_api import HttpOctoApi
from file_downloader import UcloudBackendFileDownloader
import bluetooth
import system


class Args(PyArgs):
    ucloud_id_path: T.Optional[str]
    ucloud_id: T.Optional[str]
    octoprint_url: str
    octoprint_config_path: str
    file_upload_path: str
    scripts_path: str
    socket_url: str
    backend_url: str
    retry_timeout: int = 20
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


class UcloudPrinter(Printer, AckWsUcloudSocket):
    pass


async def main(loop: asyncio.AbstractEventLoop):
    args = Args()
    if args.bluetooth:
        threading.Thread(target=bluetooth.main, args=(args.ucloud_id, system.LinuxSystem())).start()
    init_logger(args.log_level)
    print(args)
    printer = UcloudPrinter(
        url_socket=args.socket_url,
        ucloud_id=args.ucloud_id,
        octo_api=HttpOctoApi(args.octoprint_url, args.octoprint_config_path),
        file_downloader=UcloudBackendFileDownloader(args.backend_url),
        upload_path=args.file_upload_path,
        scripts_path=args.scripts_path,
        retry_timeout=args.retry_timeout,
        ping_timeout=args.ping_timeout
    )
    await printer.start(loop)
    await printer.loop()

if __name__ == '__main__':
    main_loop = asyncio.get_event_loop()
    main_loop.run_until_complete(main(main_loop))
