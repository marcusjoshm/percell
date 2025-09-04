from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable, List, Sequence, Tuple

import numpy as np
from scipy.optimize import linear_sum_assignment


@dataclass(frozen=True)
class ROI:
    """Minimal ROI value object used for matching.

    This abstraction intentionally avoids I/O details. Geometry is represented
    as either polygon vertices (x, y) or rectangle-like parameters.
    """

    id: int
    x: Sequence[float] | None = None
    y: Sequence[float] | None = None
    left: float | None = None
    top: float | None = None
    width: float | None = None
    height: float | None = None
    right: float | None = None
    bottom: float | None = None


class ROITrackingService:
    """Pure domain service for ROI tracking and matching logic."""

    def match_rois(
        self,
        source_rois: Sequence[ROI],
        target_rois: Sequence[ROI],
        max_distance: float | None = None,
    ) -> Dict[int, int]:
        """Match ROIs from source to target using Hungarian algorithm.

        Returns a mapping of source ROI id -> target ROI id. If max_distance
        is provided, matches with distance greater than max_distance are
        discarded from the result.
        """

        if not source_rois or not target_rois:
            return {}

        source_centers = [self._get_centroid(roi) for roi in source_rois]
        target_centers = [self._get_centroid(roi) for roi in target_rois]

        cost = self._build_cost_matrix(source_centers, target_centers)
        row_idx, col_idx = linear_sum_assignment(cost)

        matches: Dict[int, int] = {}
        for i, j in zip(row_idx, col_idx):
            if max_distance is not None and cost[i, j] > max_distance:
                continue
            matches[source_rois[i].id] = target_rois[j].id

        return matches

    def _get_centroid(self, roi: ROI) -> Tuple[float, float]:
        """Calculate centroid for ROI as polygon or rectangle."""
        if roi.x is not None and roi.y is not None:
            x = list(roi.x)
            y = list(roi.y)
            if not x or not y or len(x) != len(y):
                raise ValueError("Invalid polygon coordinates")
            # Ensure closed polygon
            if x[0] != x[-1] or y[0] != y[-1]:
                x.append(x[0])
                y.append(y[0])
            return self._polygon_centroid(x, y)

        rect_keys = (roi.left, roi.top, roi.width, roi.height)
        if all(v is not None for v in rect_keys):
            assert roi.left is not None and roi.top is not None
            assert roi.width is not None and roi.height is not None
            return (roi.left + roi.width / 2.0, roi.top + roi.height / 2.0)

        alt_rect = (roi.left, roi.top, roi.right, roi.bottom)
        if all(v is not None for v in alt_rect):
            assert roi.left is not None and roi.top is not None
            assert roi.right is not None and roi.bottom is not None
            w = roi.right - roi.left
            h = roi.bottom - roi.top
            return (roi.left + w / 2.0, roi.top + h / 2.0)

        raise ValueError("ROI lacks sufficient geometry for centroid computation")

    def _polygon_centroid(self, x: Sequence[float], y: Sequence[float]) -> Tuple[float, float]:
        """Compute centroid via shoelace formula with fallback for near-zero area."""
        area_twice = 0.0
        centroid_x_twelfth = 0.0
        centroid_y_twelfth = 0.0
        n = len(x) - 1
        for i in range(n):
            cross = x[i] * y[i + 1] - x[i + 1] * y[i]
            area_twice += cross
            centroid_x_twelfth += (x[i] + x[i + 1]) * cross
            centroid_y_twelfth += (y[i] + y[i + 1]) * cross

        area = area_twice * 0.5
        if abs(area) < 1e-8:
            return (float(sum(x[:-1]) / n), float(sum(y[:-1]) / n))

        cx = centroid_x_twelfth / (6.0 * area)
        cy = centroid_y_twelfth / (6.0 * area)
        return (float(cx), float(cy))

    def _build_cost_matrix(
        self, source_centers: Sequence[Tuple[float, float]], target_centers: Sequence[Tuple[float, float]]
    ) -> np.ndarray:
        """Euclidean distance matrix between two point sets."""
        s = np.asarray(source_centers, dtype=float)
        t = np.asarray(target_centers, dtype=float)
        # (S, 1, 2) - (1, T, 2) => (S, T, 2)
        diff = s[:, None, :] - t[None, :, :]
        return np.sqrt(np.sum(diff * diff, axis=2))


