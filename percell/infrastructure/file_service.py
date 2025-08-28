from __future__ import annotations

import shutil
from pathlib import Path
from typing import Iterable

from percell.domain.ports import FileSystemService


class FileService(FileSystemService):
    """Minimal file service for copying and ensuring directories."""

    def ensure_dir(self, directory: str) -> None:
        Path(directory).mkdir(parents=True, exist_ok=True)

    def copy_files(self, files: Iterable[str], destination_dir: str) -> int:
        dest = Path(destination_dir)
        dest.mkdir(parents=True, exist_ok=True)
        count = 0
        for file_path in files:
            src = Path(file_path)
            if src.exists() and src.is_file():
                shutil.copy2(src, dest / src.name)
                count += 1
        return count


__all__ = ["FileService"]


