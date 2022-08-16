from cloup import command, help_option, version_option, option

from pyckmeans_gui_backend import __version__
import logging

logger = logging.getLogger('root')
logging.basicConfig(level=logging.INFO)


@command('pyckmeans GUI')
@option('-p', '--port', help='Server port', show_default=True, default=3000)
@option('-c/-nc', '--cors/--no-cors', help='CORS setting', show_default=True)
@version_option(__version__, '--version', '-v')
@help_option('-h', '--help')
def cli(port: int, cors: bool):
    from ..app import ApplicationServer

    app = ApplicationServer('127.0.0.1', port=port, file_explorer_root='.', cors=cors)
    app.start()
