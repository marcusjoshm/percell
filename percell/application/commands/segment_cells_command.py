from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from percell.application.use_cases.segment_cells import SegmentCellsUseCase
from percell.domain.value_objects.processing import SegmentationParameters


@dataclass(frozen=True)
class SegmentCellsCommand:
    """Command encapsulating parameters to segment all images in a directory."""

    input_dir: Path
    output_dir: Path
    parameters: SegmentationParameters

    def execute(self, use_case: SegmentCellsUseCase):
        return use_case.execute(self.input_dir, self.output_dir, self.parameters)


