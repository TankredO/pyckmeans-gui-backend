from pathlib import Path
import pkg_resources

ROOT = Path('.')

STATIC_DIR = Path(
    pkg_resources.resource_filename('pyckmeans_gui_backend.app', 'static')
)
