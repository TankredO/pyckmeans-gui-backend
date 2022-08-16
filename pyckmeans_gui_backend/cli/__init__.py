from cloup import command, option, help_option, version_option
from .. import __version__


@command('Server')
@option('-p', '--port', help='Server port', default=3000, show_default=True)
@help_option('-h', '--help')
@version_option(__version__, '-v', '--version')
def cli(port):
    import uvicorn

    uvicorn.run(
        'pyckmeans_gui_backend.app:app',
        port=port,
        reload=True,
        access_log=False,
        workers=1,
        # limit_concurrency=1,
        # limit_max_requests=1,
    )
