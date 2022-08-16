''' App server
'''

import logging
import os
import signal
from typing import TYPE_CHECKING, Optional

import tornado.escape
import tornado.ioloop
import tornado.options
import tornado.web
from tornado.web import HTTPError

from ..defaults import STATIC_DIR

logger = logging.getLogger('root')


class StaticFileHandler(tornado.web.StaticFileHandler):
    # For vue router compatibility
    # If a file is not found index.html (the vue app) is returned
    def validate_absolute_path(self, root: str, absolute_path: str) -> Optional[str]:
        root = os.path.abspath(root)
        if not root.endswith(os.path.sep):
            root += os.path.sep
        if not (absolute_path + os.path.sep).startswith(root):
            raise HTTPError(403, "%s is not in root static directory", self.path)
        if os.path.isdir(absolute_path) and self.default_filename is not None:
            if not self.request.path.endswith("/"):
                self.redirect(self.request.path + "/", permanent=True)
                return None
            absolute_path = os.path.join(absolute_path, self.default_filename)
        if not os.path.exists(absolute_path):
            return str(STATIC_DIR / 'index.html')
        if not os.path.isfile(absolute_path):
            return str(STATIC_DIR / 'index.html')
        return absolute_path


class MyApplication(tornado.web.Application):
    is_closing = False

    def signal_handler(self, signum, frame):
        logger.info('exiting...')
        self.is_closing = True

    def try_exit(self):
        if self.is_closing:
            # clean up here
            tornado.ioloop.IOLoop.instance().stop()
            logger.info('exit success')


def create_app(file_explorer_root: str):

    from .api import build_handlers as build_api_handlers

    application = MyApplication(
        [
            *build_api_handlers('/api', file_explorer_root=file_explorer_root),
            (
                r'/(.*)',
                StaticFileHandler,
                {
                    'path': str(STATIC_DIR),
                    'default_filename': 'index.html',
                },
            ),
        ],
        login_url='/login',
    )

    return application


class ApplicationServer:
    def __init__(
        self,
        address: str,
        port: int,
        file_explorer_root: str,
        cors: bool = True,
    ):
        self.address = address
        self.port = port
        self.cors = cors
        self.file_explorer_root = file_explorer_root

        self.tornado_app = create_app(file_explorer_root=file_explorer_root)

    def start(self):
        self.tornado_app.listen(port=self.port, address=self.address)
        logger.info(
            f'Starting application server at http://{self.address}:{self.port} (CORS: {self.cors})'
        )

        tornado.options.parse_command_line([])
        signal.signal(signal.SIGINT, self.tornado_app.signal_handler)
        tornado.ioloop.PeriodicCallback(self.tornado_app.try_exit, 100).start()
        tornado.ioloop.IOLoop.current().start()
