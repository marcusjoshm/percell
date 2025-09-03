"""
Simple dependency container wiring ports to adapters.

This is a lightweight placeholder to avoid adding a third-party DI framework
yet. It can be replaced with dependency_injector or similar later.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from percell.adapters.outbound.storage.file_system_adapter import FileSystemAdapter
from percell.adapters.outbound.segmentation.cellpose_adapter import CellposeAdapter
from percell.adapters.outbound.image_processing.imagej_adapter import ImageJAdapter
from percell.adapters.outbound.metadata.metadata_adapter import FileNameMetadataAdapter
from percell.domain.services.workflow_orchestrator import WorkflowOrchestrator
from percell.domain.services.metadata_service import MetadataService
from percell.domain.services.image_binning_service import ImageBinningService
from percell.domain.services.roi_tracking_service import RoiTrackingService
from percell.domain.services.cell_grouping_service import CellGroupingService
from percell.domain.services.roi_processor import ROIProcessor
from percell.domain.value_objects.file_path import FilePath


@dataclass
class AppConfig:
    storage_base_path: Optional[str] = None
    cellpose_path: Optional[str] = None
    imagej_path: Optional[str] = None


class Container:
    def __init__(self, config: Optional[AppConfig] = None) -> None:
        self.config = config or AppConfig()

        # Instantiate adapters
        self.storage_adapter = FileSystemAdapter(
            base_path=FilePath.from_string(self.config.storage_base_path)
            if self.config.storage_base_path
            else None
        )
        self.cellpose_adapter = CellposeAdapter(
            cellpose_path=FilePath.from_string(self.config.cellpose_path)
            if self.config.cellpose_path
            else None
        )
        self.imagej_adapter = ImageJAdapter(
            imagej_path=FilePath.from_string(self.config.imagej_path)
            if self.config.imagej_path
            else None
        )
        self.metadata_adapter = FileNameMetadataAdapter()

    def workflow_orchestrator(self) -> WorkflowOrchestrator:
        return WorkflowOrchestrator(
            storage=self.storage_adapter,
            segmentation=self.cellpose_adapter,
            image_processing=self.imagej_adapter,
            metadata=self.metadata_adapter,
        )

    def metadata_service(self) -> MetadataService:
        return MetadataService(
            storage=self.storage_adapter,
            metadata_port=self.metadata_adapter,
        )

    def image_binning_service(self) -> ImageBinningService:
        return ImageBinningService(
            storage=self.storage_adapter,
            metadata_service=self.metadata_service(),
        )

    def roi_tracking_service(self) -> RoiTrackingService:
        return RoiTrackingService(
            storage=self.storage_adapter,
            metadata_service=self.metadata_service(),
        )

    def cell_grouping_service(self) -> CellGroupingService:
        return CellGroupingService(
            storage=self.storage_adapter,
            metadata_service=self.metadata_service(),
        )

    def roi_processor(self) -> ROIProcessor:
        return ROIProcessor(
            storage=self.storage_adapter,
            metadata_service=self.metadata_service(),
        )


