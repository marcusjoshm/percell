from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from percell.application.use_cases.track_rois import TrackROIsUseCase


@dataclass(frozen=True)
class TrackROIsCommand:
    """Command encapsulating parameters to track ROIs between two archives."""

    zip_t0: Path
    zip_t1: Path
    output_zip: Path
    max_distance: Optional[float] = None

    def execute(self, use_case: TrackROIsUseCase):
        return use_case.execute(self.zip_t0, self.zip_t1, self.output_zip, self.max_distance)


