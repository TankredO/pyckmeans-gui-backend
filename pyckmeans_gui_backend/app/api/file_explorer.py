from pathlib import Path
from typing import Tuple, Dict, Any, Type, TYPE_CHECKING
from ..base import (
    APIErrorType,
    BaseHandler,
    require_arguments,
    with_json_response,
    APIResponse,
    APIError,
    APIErrorType,
)
from ..modules import file_explorer

if TYPE_CHECKING:
    from os import PathLike


class FileExplorerBaseHandler(BaseHandler):
    def initialize(
        self,
        root: 'PathLike',
    ):
        self.root = Path(root)
        self.file_explorer = file_explorer.FileExplorer(self.root)


class FileNotFoundApiError(APIError):
    def __init__(self):
        super().__init__(
            error_type=APIErrorType.FILE_NOT_FOUND, error_message='File not found'
        )


class RuntimeApiError(APIError):
    def __init__(self):
        super().__init__(
            error_type=APIErrorType.RUNTIME_ERROR,
            error_message='Unspecified runtime error',
        )


class GetFileHandler(FileExplorerBaseHandler):
    @with_json_response
    @require_arguments(['path'])
    def get(self):
        path = self.get_argument_from_anywhere('path')
        depth = self.get_argument_from_anywhere('depth', 0)

        try:
            file = self.file_explorer.get_file(path)
            res = APIResponse(data=file.as_dict(depth=int(depth)))
            self.write(res.as_json())
        except FileNotFoundError as err:
            res = APIResponse(error=FileNotFoundApiError())
            self.write(res.as_json())
        except RuntimeError as err:
            res = APIResponse(error=RuntimeApiError())
            self.write(res.as_json())


def build_handlers(
    base_path: str,
    root: str,
) -> Tuple[Tuple[str, Type[BaseHandler], Dict[str, Any]], ...]:
    return (
        (
            f'{base_path}/get_file',
            GetFileHandler,
            dict(root=root),
        ),
    )
