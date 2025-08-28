from __future__ import annotations

from typing import Optional

from percell.core.config import Config
from percell.infrastructure.file_service import FileService
from percell.infrastructure.imagej_service import ImageJService
from percell.infrastructure.progress_reporter import AliveProgressReporter
from percell.services.module_runner import ModuleRunner
from percell.services.workflow_service import WorkflowService
from percell.services.cleanup_service import CleanupService


class ServiceFactory:
    """Lightweight factory providing shared service instances per pipeline run."""

    def __init__(self, config: Config) -> None:
        self._config = config
        self._file_service: Optional[FileService] = None
        self._imagej_service: Optional[ImageJService] = None
        self._module_runner: Optional[ModuleRunner] = None
        self._workflow_service: Optional[WorkflowService] = None
        self._cleanup_service: Optional[CleanupService] = None
        self._progress_reporter: Optional[AliveProgressReporter] = None

    def get_file_service(self) -> FileService:
        if self._file_service is None:
            self._file_service = FileService()
        return self._file_service

    def get_imagej_service(self) -> ImageJService:
        if self._imagej_service is None:
            imagej_path = self._config.get('imagej_path', '')
            self._imagej_service = ImageJService(imagej_path)
        return self._imagej_service

    def get_module_runner(self) -> ModuleRunner:
        if self._module_runner is None:
            self._module_runner = ModuleRunner()
        return self._module_runner

    def get_workflow_service(self) -> WorkflowService:
        if self._workflow_service is None:
            self._workflow_service = WorkflowService(self.get_module_runner())
        return self._workflow_service

    def get_cleanup_service(self) -> CleanupService:
        if self._cleanup_service is None:
            self._cleanup_service = CleanupService()
        return self._cleanup_service

    def get_progress_reporter(self) -> AliveProgressReporter:
        if self._progress_reporter is None:
            self._progress_reporter = AliveProgressReporter()
        return self._progress_reporter


__all__ = ["ServiceFactory"]


