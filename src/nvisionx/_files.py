from __future__ import annotations

import mimetypes
import os
from collections.abc import Sequence
from pathlib import Path
from typing import IO, Union, cast

FileContent = Union[bytes, IO[bytes]]
FileInput = Union[
    str,
    "os.PathLike[str]",
    FileContent,
    tuple[str, FileContent],
    tuple[str, FileContent, str],
]
FilesInput = Union[FileInput, Sequence[FileInput]]

HTTPXFile = tuple[str, tuple[str, FileContent, str]]


def _content_type(name: str) -> str:
    return mimetypes.guess_type(name)[0] or "application/octet-stream"


def _one(file: FileInput, opened: list[IO[bytes]]) -> tuple[str, FileContent, str]:
    if isinstance(file, (str, os.PathLike)):
        path = Path(file)
        handle = path.open("rb")
        opened.append(handle)
        return path.name, handle, _content_type(path.name)
    if isinstance(file, tuple):
        if len(file) == 2:
            name, content = file
            return name, content, _content_type(name)
        return file
    if isinstance(file, bytes):
        return "upload", file, "application/octet-stream"
    name = Path(str(getattr(file, "name", "upload"))).name
    return name, file, _content_type(name)


def to_httpx_files(files: FilesInput, opened: list[IO[bytes]]) -> list[HTTPXFile]:
    items: Sequence[FileInput]
    if isinstance(files, (str, bytes, os.PathLike, tuple)) or hasattr(files, "read"):
        items = [cast(FileInput, files)]
    else:
        items = files
    return [("file", _one(item, opened)) for item in items]
