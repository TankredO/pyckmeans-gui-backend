from cloup import command, help_option, version_option

from pyckmeans_gui_backend import __version__
import logging

logger = logging.getLogger('root')
logging.basicConfig(level=logging.INFO)


@command('pyckmeans GUI')
@version_option(__version__, '--version', '-v')
@help_option('-h', '--help')
def cli():
    from ..app import ApplicationServer

    app = ApplicationServer('127.0.0.1', 36000, file_explorer_root='.')
    app.start()
