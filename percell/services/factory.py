from __future__ import annotations

from typing import Optional

from percell.core.config import Config
from percell.infrastructure.file_service import FileService
from percell.infrastructure.imagej_service import ImageJService


class ServiceFactory:
    """Lightweight factory providing shared service instances per pipeline run."""

    def __init__(self, config: Config) -> None:
        self._config = config
        self._file_service: Optional[FileService] = None
        self._imagej_service: Optional[ImageJService] = None

    def get_file_service(self) -> FileService:
        if self._file_service is None:
            self._file_service = FileService()
        return self._file_service

    def get_imagej_service(self) -> ImageJService:
        if self._imagej_service is None:
            imagej_path = self._config.get('imagej_path', '')
            self._imagej_service = ImageJService(imagej_path)
        return self._imagej_service


__all__ = ["ServiceFactory"]


