from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, Iterable, Optional


class ImageProcessingService(ABC):
    @abstractmethod
    def run_macro(self, macro_path: str, params: Optional[Dict[str, str]] = None, *, headless: bool = False) -> int:
        """Run an ImageJ/Fiji macro and return the process return code."""


class FileSystemService(ABC):
    @abstractmethod
    def ensure_dir(self, directory: str) -> None:
        """Ensure a directory exists."""

    @abstractmethod
    def copy_files(self, files: Iterable[str], destination_dir: str) -> int:
        """Copy files to destination, returning number of files copied."""


class ProgressReporter(ABC):
    @abstractmethod
    def start(self, title: Optional[str] = None) -> None:
        ...

    @abstractmethod
    def advance(self, delta: int = 1) -> None:
        ...

    @abstractmethod
    def stop(self) -> None:
        ...


