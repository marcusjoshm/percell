from __future__ import annotations

import shutil
from pathlib import Path
from typing import List, Optional

from percell.ports.outbound.filesystem_port import FilesystemPort


class PathlibFilesystemAdapter(FilesystemPort):
    """Filesystem adapter backed by pathlib and shutil."""

    def exists(self, path: Path) -> bool:
        return Path(path).exists()

    def ensure_dir(self, path: Path) -> None:
        Path(path).mkdir(parents=True, exist_ok=True)

    def list_files(self, directory: Path, pattern: str = "*") -> List[Path]:
        d = Path(directory)
        return [p for p in d.glob(pattern) if p.is_file()]

    def list_dirs(self, directory: Path) -> List[Path]:
        d = Path(directory)
        return [p for p in d.iterdir() if p.is_dir()]

    def glob(self, pattern: str, root: Optional[Path] = None) -> List[Path]:
        base = Path(root) if root is not None else Path.cwd()
        return list(base.glob(pattern))

    def remove_file(self, path: Path) -> None:
        try:
            Path(path).unlink(missing_ok=True)
        except TypeError:
            # Python < 3.8 fallback
            p = Path(path)
            if p.exists():
                p.unlink()

    def remove_dir(self, path: Path, recursive: bool = False) -> None:
        p = Path(path)
        if not p.exists():
            return
        if recursive:
            shutil.rmtree(p)
        else:
            p.rmdir()


