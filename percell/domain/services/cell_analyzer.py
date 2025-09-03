"""
CellAnalyzer

Pure domain service for analyzing cells and ROIs: intensity stats, area,
colocalization metrics, and simple grouping helpers.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable, List, Optional, Sequence, Tuple
import numpy as np

from percell.domain.entities.cell import Cell
from percell.domain.entities.roi import ROI


@dataclass
class IntensityStats:
    mean: float
    std: float
    min: float
    max: float


class CellAnalyzer:
    """Core analysis algorithms for cells and ROIs."""

    def calculate_intensity_statistics(self, image: np.ndarray, roi: Optional[ROI] = None) -> IntensityStats:
        """
        Calculate intensity statistics for an image, optionally within an ROI.
        """
        if image is None:
            raise ValueError("image must not be None")
        data = np.asarray(image)
        if data.ndim > 2:
            data = np.mean(data, axis=-1)
        if roi and roi.bounding_box:
            x, y, w, h = roi.bounding_box
            x = max(0, x)
            y = max(0, y)
            w = max(0, w)
            h = max(0, h)
            data = data[y:y + h, x:x + w]
        values = data.astype(np.float64).ravel()
        values = values[np.isfinite(values)]
        if values.size == 0:
            return IntensityStats(0.0, 0.0, 0.0, 0.0)
        return IntensityStats(
            mean=float(np.mean(values)),
            std=float(np.std(values)),
            min=float(np.min(values)),
            max=float(np.max(values)),
        )

    def measure_cell_area(self, cell: Cell) -> float:
        if cell.roi is None:
            return 0.0
        if cell.roi.area is not None:
            return float(cell.roi.area)
        return float(cell.roi.calculate_area())

    def group_cells_by_intensity(self, cells: Sequence[Cell], channel: str, num_groups: int) -> Dict[int, List[Cell]]:
        """
        Group cells into bins by their mean intensity for the given channel.
        Uses quantile-based binning for robustness.
        """
        if num_groups <= 0 or len(cells) == 0:
            return {}
        intensities: List[float] = []
        for cell in cells:
            val = cell.get_channel_measurement(channel, "mean_intensity")
            intensities.append(float(val) if val is not None else 0.0)
        arr = np.asarray(intensities, dtype=np.float64)
        # Compute quantile edges (unique and sorted)
        quantiles = np.linspace(0.0, 1.0, num_groups + 1)
        edges = np.unique(np.quantile(arr, quantiles))
        if edges.size <= 1:
            # All zeros or constant; everything in one group 0
            return {0: list(cells)}
        # Digitize into bins
        # Rightmost bin inclusive
        bin_indices = np.digitize(arr, edges[1:-1], right=True)
        groups: Dict[int, List[Cell]] = {}
        for idx, cell in enumerate(cells):
            g = int(bin_indices[idx])
            groups.setdefault(g, []).append(cell)
        return groups

    def calculate_colocalization(self, channel_a: np.ndarray, channel_b: np.ndarray, roi: Optional[ROI] = None) -> float:
        """
        Compute a simple Pearson correlation coefficient between two channels,
        optionally within an ROI bounding box. Returns 0.0 if insufficient data.
        """
        if channel_a is None or channel_b is None:
            return 0.0
        a = np.asarray(channel_a)
        b = np.asarray(channel_b)
        if a.shape != b.shape:
            # Basic safety: crop to common min shape
            h = min(a.shape[0], b.shape[0])
            w = min(a.shape[1], b.shape[1])
            a = a[:h, :w]
            b = b[:h, :w]
        if a.ndim > 2:
            a = np.mean(a, axis=-1)
        if b.ndim > 2:
            b = np.mean(b, axis=-1)
        if roi and roi.bounding_box:
            x, y, w, h = roi.bounding_box
            a = a[y:y + h, x:x + w]
            b = b[y:y + h, x:x + w]
        va = a.astype(np.float64).ravel()
        vb = b.astype(np.float64).ravel()
        mask = np.isfinite(va) & np.isfinite(vb)
        va = va[mask]
        vb = vb[mask]
        if va.size < 2:
            return 0.0
        # Pearson correlation
        va = va - va.mean()
        vb = vb - vb.mean()
        denom = np.sqrt(np.sum(va ** 2) * np.sum(vb ** 2))
        if denom == 0:
            return 0.0
        return float(np.sum(va * vb) / denom)


