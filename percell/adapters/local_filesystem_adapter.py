from __future__ import annotations

from pathlib import Path
from typing import List
import shutil
import fnmatch

from percell.ports.driven.file_management_port import FileManagementPort


class LocalFileSystemAdapter(FileManagementPort):
    """Adapter implementing basic filesystem operations using stdlib."""

    def list_files(self, root: Path, patterns: List[str]) -> List[Path]:
        if not patterns:
            patterns = ["*"]
        root = Path(root)
        matches: List[Path] = []
        for path in root.rglob("*"):
            if not path.is_file():
                continue
            name = path.name
            for pat in patterns:
                if fnmatch.fnmatch(name, pat):
                    matches.append(path)
                    break
        return matches

    def copy(self, src: Path, dst: Path, overwrite: bool = False) -> None:
        src = Path(src)
        dst = Path(dst)
        dst.parent.mkdir(parents=True, exist_ok=True)
        if dst.exists() and not overwrite:
            return
        shutil.copy2(src, dst)

    def move(self, src: Path, dst: Path, overwrite: bool = False) -> None:
        src = Path(src)
        dst = Path(dst)
        dst.parent.mkdir(parents=True, exist_ok=True)
        if dst.exists():
            if overwrite:
                if dst.is_file():
                    dst.unlink()
                else:
                    shutil.rmtree(dst)
            else:
                return
        shutil.move(str(src), str(dst))

    def ensure_dir(self, path: Path) -> None:
        Path(path).mkdir(parents=True, exist_ok=True)


