from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
from typing import List, Optional


class FilesystemPort(ABC):
    """Driven port abstracting basic filesystem operations for testability."""

    @abstractmethod
    def exists(self, path: Path) -> bool:
        """Return True if the path exists."""

    @abstractmethod
    def ensure_dir(self, path: Path) -> None:
        """Create directory (and parents) if missing."""

    @abstractmethod
    def list_files(self, directory: Path, pattern: str = "*") -> List[Path]:
        """List files in a directory matching a glob pattern."""

    @abstractmethod
    def list_dirs(self, directory: Path) -> List[Path]:
        """List immediate subdirectories in a directory."""

    @abstractmethod
    def glob(self, pattern: str, root: Optional[Path] = None) -> List[Path]:
        """Glob for files/dirs from an optional root (defaults to cwd)."""

    @abstractmethod
    def remove_file(self, path: Path) -> None:
        """Remove a file if it exists."""

    @abstractmethod
    def remove_dir(self, path: Path, recursive: bool = False) -> None:
        """Remove a directory; if recursive, remove contents too."""


