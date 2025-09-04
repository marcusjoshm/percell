from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import numpy as np

from percell.adapters.factory import AdapterFactory, AdapterFactoryConfig
from percell.adapters.outbound.tifffile_image_adapter import TifffileImageAdapter
from percell.adapters.outbound.pandas_metadata_adapter import PandasMetadataAdapter
from percell.adapters.outbound.pathlib_filesystem_adapter import PathlibFilesystemAdapter
from percell.application.use_cases.group_cells import GroupCellsUseCase
from percell.application.use_cases.segment_cells import SegmentCellsUseCase
from percell.application.use_cases.track_rois import TrackROIsUseCase
from percell.domain.services.cell_grouping_service import CellGroupingService
from percell.domain.services.roi_tracking_service import ROITrackingService
from percell.ports.outbound.segmenter_port import SegmenterPort


@dataclass(frozen=True)
class AppConfig:
    imagej_path: Optional[Path] = None
    macro_dir: Optional[Path] = None
    image_adapter: str = "tifffile"
    metadata_store: str = "pandas"
    filesystem: str = "pathlib"
    macro_runner: str = "imagej"


class DummySegmenter(SegmenterPort):
    """Minimal default segmenter used by the container if none is provided.

    Produces a zero-valued mask of the same shape as the input image.
    """

    def segment(self, image: np.ndarray, parameters) -> np.ndarray:  # parameters unused for dummy
        return np.zeros_like(image, dtype=np.uint16)


class Container:
    """Simple dependency injection container wiring adapters, services, and use cases."""

    def __init__(self, config: Optional[AppConfig] = None, segmenter: Optional[SegmenterPort] = None) -> None:
        self.config = config or AppConfig()
        self._segmenter = segmenter or DummySegmenter()

        factory_cfg = AdapterFactoryConfig(
            image_adapter=self.config.image_adapter,  # type: ignore[arg-type]
            macro_runner=self.config.macro_runner,  # type: ignore[arg-type]
            metadata_store=self.config.metadata_store,  # type: ignore[arg-type]
            filesystem=self.config.filesystem,  # type: ignore[arg-type]
            imagej_path=self.config.imagej_path,
            macro_dir=self.config.macro_dir,
        )
        self._factory = AdapterFactory(factory_cfg)

    # --- Adapters ---
    def image_adapter(self) -> TifffileImageAdapter:
        return self._factory.build_image_reader()  # type: ignore[return-value]

    def metadata_adapter(self) -> PandasMetadataAdapter:
        return self._factory.build_metadata_store()  # type: ignore[return-value]

    def filesystem(self) -> PathlibFilesystemAdapter:
        return self._factory.build_filesystem()  # type: ignore[return-value]

    # --- Domain Services ---
    def cell_grouping_service(self) -> CellGroupingService:
        return CellGroupingService()

    def roi_tracking_service(self) -> ROITrackingService:
        return ROITrackingService()

    # --- Use Cases ---
    def group_cells_use_case(self) -> GroupCellsUseCase:
        return GroupCellsUseCase(
            grouping_service=self.cell_grouping_service(),
            image_reader=self.image_adapter(),
            image_writer=self.image_adapter(),
            metadata_store=self.metadata_adapter(),
            filesystem=self.filesystem(),
        )

    def segment_cells_use_case(self) -> SegmentCellsUseCase:
        return SegmentCellsUseCase(
            image_reader=self.image_adapter(),
            image_writer=self.image_adapter(),
            segmenter=self._segmenter,
            filesystem=self.filesystem(),
        )

    def track_rois_use_case(self, repo) -> TrackROIsUseCase:  # repo provided externally for flexibility
        return TrackROIsUseCase(
            tracker=self.roi_tracking_service(),
            repo=repo,
        )

_GLOBAL_CONTAINER: Container | None = None


def get_container(config: Optional[AppConfig] = None, segmenter: Optional[SegmenterPort] = None) -> Container:
    global _GLOBAL_CONTAINER
    if _GLOBAL_CONTAINER is None:
        _GLOBAL_CONTAINER = Container(config=config, segmenter=segmenter)
    return _GLOBAL_CONTAINER


