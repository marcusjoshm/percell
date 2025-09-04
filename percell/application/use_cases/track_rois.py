from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import List

from percell.domain.services.roi_tracking_service import ROITrackingService, ROI
from percell.ports.outbound.roi_repository_port import ROIRepositoryPort


@dataclass(frozen=True)
class TrackROIsResult:
    output_zip_path: Path
    matched_count: int


class TrackROIsUseCase:
    """Use case that loads two ROI archives, computes matching, and writes reordered output."""

    def __init__(self, tracker: ROITrackingService, repo: ROIRepositoryPort) -> None:
        self.tracker = tracker
        self.repo = repo

    def execute(self, zip_t0: Path, zip_t1: Path, output_zip: Path, max_distance: float | None = None) -> TrackROIsResult:
        rois0, names0, _ = self.repo.load_rois(zip_t0)
        rois1, names1, bytes_map1 = self.repo.load_rois(zip_t1)

        # Build id -> index mapping for rois1 since ROI ids are preserved from repository
        id_to_index = {roi.id: idx for idx, roi in enumerate(rois1)}

        mapping = self.tracker.match_rois(rois0, rois1, max_distance=max_distance)
        # mapping: source_id -> target_id
        reordered_names: List[str] = []
        for roi0 in rois0:
            target_id = mapping.get(roi0.id)
            if target_id is None:
                continue
            idx = id_to_index[target_id]
            reordered_names.append(names1[idx])

        self.repo.save_reordered(output_zip, reordered_names, bytes_map1)
        return TrackROIsResult(output_zip_path=output_zip, matched_count=len(reordered_names))


