from __future__ import annotations

from pathlib import Path
from typing import Protocol, List

from ...domain.models import SegmentationParameters


class CellposeIntegrationPort(Protocol):
    """Driven port for invoking Cellpose segmentation."""

    def run_segmentation(
        self,
        images: List[Path],
        output_dir: Path,
        params: SegmentationParameters,
    ) -> List[Path]:
        """Run segmentation and return list of mask paths."""
        ...


