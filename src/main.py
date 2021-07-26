import asyncio
import typing as T
from log.logger import _get as init_logger

from pyargparse import PyArgs

from printer import Printer, UcloudApi, OctoApi


class Args(PyArgs):
    ucloud_id_path: T.Optional[str]
    ucloud_id: T.Optional[str]
    octoprint_url: str
    octoprint_config_path: str
    file_upload_path: str
    socket_url: str
    backend_url: str
    ping_timeout: int = 10
    log_level: str = "INFO"

    def __init__(self):
        super(Args, self).__init__("config.production.yml")
        if self.ucloud_id is None and self.ucloud_id_path is None:
            raise ValueError("ucloud_id or ucloud_id_path must be provided")
        if self.ucloud_id_path:
            with open(self.ucloud_id_path) as f:
                self.ucloud_id = f.read()


async def main(loop: asyncio.AbstractEventLoop):
    args = Args()
    init_logger(args.log_level)
    print(args)
    octoapi = OctoApi(args.octoprint_url, args.octoprint_config_path)
    ulabapi = UcloudApi(args.socket_url, args.backend_url, args.ucloud_id)
    printer = Printer(octoapi, ulabapi, args.file_upload_path, args.ping_timeout)
    await printer.ucloud_api.connect(loop)
    await printer.loop()

if __name__ == '__main__':
    main_loop = asyncio.get_event_loop()
    main_loop.run_until_complete(main(main_loop))
