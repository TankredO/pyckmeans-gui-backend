import enum
import shutil
from os import PathLike
from sys import platform
from pathlib import Path

from typing import Union, Optional, Dict, Any, List

if platform == 'win32':

    def get_owner_name(path: PathLike) -> str:
        import win32security  # type: ignore

        path = Path(path)

        sd = win32security.GetFileSecurity(
            str(path.resolve()), win32security.OWNER_SECURITY_INFORMATION
        )
        owner_sid = sd.GetSecurityDescriptorOwner()
        name, domain, type = win32security.LookupAccountSid(None, owner_sid)

        return name

    def get_group_name(path: PathLike) -> Optional[str]:
        return None

else:
    import pwd
    import grp

    def get_owner_name(path: PathLike) -> str:
        path = Path(path)
        p_stat = path.stat()

        return pwd.getpwuid(p_stat.st_uid).pw_name

    def get_group_name(path: PathLike) -> Optional[str]:
        path = Path(path)
        p_stat = path.stat()

        return grp.getgrgid(p_stat.st_gid).gr_name


class FileType(enum.Enum):
    DIRECTORY = 'directory'
    FILE = 'file'


class FileStats:
    def __init__(
        self,
        name: str,
        path: str,
        type: FileType,
        uid: int,
        gid: int,
        owner: str,
        size: int,
        created: float,
        modified: float,
        group: Optional[str] = None,
        is_link: bool = False,
        link_target: Optional[str] = None,
    ):
        self.name = name
        self.path = path
        self.type = type
        self.uid = uid
        self.gid = gid
        self.owner = owner
        self.group: Optional[str] = group
        self.size = size
        self.created = created
        self.modified = modified
        self.is_link = is_link
        self.link_target = link_target

    def as_dict(self) -> Dict[str, Any]:
        return dict(
            name=self.name,
            path=self.path,
            type=self.type.value,
            uid=self.uid,
            gid=self.gid,
            owner=self.owner,
            group=self.group,
            size=self.size,
            created=self.created,
            modified=self.modified,
            is_link=self.is_link,
            link_target=self.link_target,
        )

    def __repr__(self) -> str:
        return f'<FileStats; {self.as_dict()}>'

    @classmethod
    def from_path(cls, path: PathLike):
        path = Path(path)
        f_path = path.as_posix()
        f_name = path.name

        # check if dir
        if path.is_dir():
            f_type = FileType.DIRECTORY
        # check if file
        elif path.is_file():
            f_type = FileType.FILE
        # only dirs and regular files
        else:
            msg = f'Unprocessible file type for file {path}'
            raise RuntimeError(msg)

        p_stat = path.stat()
        f_uid = p_stat.st_uid
        f_gid = p_stat.st_gid
        f_owner = get_owner_name(path)
        f_group = get_group_name(path)
        f_size = p_stat.st_size
        f_created = p_stat.st_ctime
        f_modified = p_stat.st_mtime

        f_is_link = False
        f_link_target = None
        if path.is_symlink():
            f_is_link = True
            f_link_target = path.resolve().as_posix()

        return cls(
            name=f_name,
            path=f_path,
            uid=f_uid,
            gid=f_gid,
            owner=f_owner,
            type=f_type,
            size=f_size,
            created=f_created,
            modified=f_modified,
            group=f_group,
            is_link=f_is_link,
            link_target=f_link_target,
        )


class File:
    def __init__(self, path: PathLike):
        self.path = Path(path)
        if not self.path.exists():
            msg = f'File "{self.path}" does not exist.'
            raise FileNotFoundError(msg)
        self.stats = FileStats.from_path(self.path)

    def delete(self):
        if self.type == FileType.FILE:
            self.path.unlink()
        else:
            shutil.rmtree(self.path)

    def rename(self, name: str):
        path = self.path.parent / name
        shutil.move(self.path, path)
        self.path = path
        self.stats = FileStats.from_path(self.path)

    def move(self, path: PathLike, file_explorer: Optional['FileExplorer'] = None):
        path = Path(path)
        if not file_explorer is None:
            path = file_explorer.root / path
        shutil.move(self.path, path)
        self.path = path
        self.stats = FileStats.from_path(self.path)

    @property
    def type(self) -> FileType:
        return self.stats.type

    @property
    def children(self) -> Optional[List['File']]:
        if self.type == FileType.FILE:
            return None
        return [File(p) for p in self.path.glob('*')]

    def as_dict(self, depth=0):
        if depth < 0:
            children = None
            if self.type == FileType.DIRECTORY:
                children = [f.as_dict(-1) for f in self.children]
            return dict(
                path=self.path.as_posix(),
                stats=self.stats.as_dict(),
                children=children,
            )

        if depth < 1:
            return dict(
                path=self.path.as_posix(),
                stats=self.stats.as_dict(),
                children=None,
            )

        children = None
        if self.type == FileType.DIRECTORY:
            children = [f.as_dict(depth - 1) for f in self.children]
        return dict(
            path=self.path.as_posix(),
            stats=self.stats.as_dict(),
            children=children,
        )

    def __repr__(self) -> str:
        return f'<File; {self.as_dict()}>'


class FileExplorer:
    def __init__(self, root: PathLike) -> None:
        self.root = Path(root)

    def get_file(self, path: PathLike) -> File:
        path = Path(path)

        if '..' in str(path):
            raise RuntimeError('Paths containing ".." are not allowed.')
        if str(path).startswith('/'):
            raise RuntimeError('Absolute paths are not allowed.')

        path = self.root / path
        return File(path)

    def get_file_stats(self, path: PathLike) -> FileStats:
        file = self.get_file(path)
        return file.stats
