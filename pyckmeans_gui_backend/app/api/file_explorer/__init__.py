from pathlib import Path
from typing import List, Optional, Union
from pydantic import BaseModel
from fastapi import APIRouter, HTTPException, status
from .file_explorer import FileExplorer, FileType
from ...config import ROOT

file_explorer = FileExplorer(root=ROOT)

router = APIRouter(tags=['FileExplorer'])


class FileStats(BaseModel):
    name: str
    path: str
    type: FileType
    uid: int
    gid: int
    owner: str
    size: int
    created: float
    modified: float
    group: Optional[str] = None
    is_link: bool = False
    link_target: Optional[str] = None


class File(BaseModel):
    path: str
    stats: FileStats
    children: Union[List['File'], None] = None

    class Config:
        schema_extra = {
            'example': {
                'path': '.',
                'stats': {
                    'name': '.',
                    'path': '.',
                    'type': 'directory',
                    'uid': 123,
                    'gid': 456,
                    'owner': 'admin',
                    'size': 1024,
                    'created': 1567,
                    'modified': 1567,
                    'group': None,
                    'is_link': False,
                    'link_target': None,
                },
                'children': [],
            }
        }


File.update_forward_refs()


@router.get('/file', response_model=File)
async def get_file(path: str, depth: int = 0):
    try:
        file = file_explorer.get_file(path=Path(path))
    except FileNotFoundError as err:
        raise HTTPException(status.HTTP_409_CONFLICT, 'File not found.')
    except RuntimeError as err:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(err))

    return file.as_dict(depth=depth)
