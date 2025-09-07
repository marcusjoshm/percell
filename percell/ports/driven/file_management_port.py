from __future__ import annotations

from pathlib import Path
from typing import Protocol, List


class FileManagementPort(Protocol):
    """Driven port for filesystem operations (scan/copy/move)."""

    def list_files(self, root: Path, patterns: List[str]) -> List[Path]:
        ...

    def copy(self, src: Path, dst: Path, overwrite: bool = False) -> None:
        ...

    def move(self, src: Path, dst: Path, overwrite: bool = False) -> None:
        ...

    def ensure_dir(self, path: Path) -> None:
        ...

    def ensure_executable(self, path: Path) -> None:
        ...


