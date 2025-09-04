from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, List, Tuple

from percell.domain.services.roi_tracking_service import ROI


class ROIRepositoryPort(ABC):
    """Driven port for reading/writing ROI archives (e.g., ImageJ ROI .zip files)."""

    @abstractmethod
    def load_rois(self, zip_path: Path) -> Tuple[List[ROI], List[str], Dict[str, bytes]]:
        """Load ROIs and raw bytes from a zip.

        Returns (rois, names, bytes_map) where:
        - rois: list of ROI domain objects; ids should be stable indices (0..n-1)
        - names: ROI entry names in the zip (same order/length as rois)
        - bytes_map: mapping from ROI name to its raw bytes
        """

    @abstractmethod
    def save_reordered(self, output_zip_path: Path, names_in_order: List[str], bytes_map: Dict[str, bytes]) -> None:
        """Write a new zip (or overwrite existing) with ROIs in the provided order."""


