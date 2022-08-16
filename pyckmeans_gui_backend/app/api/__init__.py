from typing import Tuple, Dict, Any, Type
from ..base import BaseHandler
from .file_explorer import build_handlers as build_file_explorer_handlers


class TestHandler(BaseHandler):
    def get(self):
        self.write("Hello, world")


def build_handlers(
    base_path: str,
    file_explorer_root: str,
) -> Tuple[Tuple[str, Type[BaseHandler], Dict[str, Any]], ...]:
    return (
        (
            f'{base_path}/test',
            TestHandler,
            dict(),
        ),
        *build_file_explorer_handlers(
            f'{base_path}/file_explorer', root=file_explorer_root
        ),
    )
