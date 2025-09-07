"""Intensity measurement and grouping algorithms.

Pure domain logic for computing intensity metrics and grouping cells by
brightness thresholds.
"""

from __future__ import annotations

from pathlib import Path
from typing import List, Tuple

import numpy as np

from ..models import AnalysisResult, CellMetrics, ROI, ThresholdParameters


class IntensityAnalysisService:
    """Provides per-cell intensity analysis algorithms."""

    def measure_cell_intensity(self, image_path: Path, rois: list[ROI]) -> list[CellMetrics]:
        """Measure intensity metrics for each ROI in an image.

        Args:
            image_path: Path to the image file.
            rois: Regions of interest representing cells.

        Returns:
            List of per-cell metrics.
        """

        try:
            import tifffile  # type: ignore
        except Exception as exc:
            raise RuntimeError("tifffile is required to measure intensities") from exc

        image = tifffile.imread(str(image_path))
        if image is None:
            raise ValueError(f"Failed to read image: {image_path}")

        # Ensure 2D grayscale for basic analysis
        if image.ndim > 2:
            image = np.asarray(image)
            image = image.squeeze()

        metrics: List[CellMetrics] = []
        # NOTE: ROI geometry is not yet implemented; compute global stats per ROI as placeholder
        img_values = image.astype(np.float64)
        mean_intensity = float(img_values.mean())
        area = float(img_values.size)
        integrated = float(img_values.sum())
        for idx, roi in enumerate(rois, start=1):
            cell_id = roi.id if roi.id is not None else idx
            metrics.append(
                CellMetrics(
                    cell_id=cell_id,
                    area=area,
                    mean_intensity=mean_intensity,
                    integrated_intensity=integrated,
                )
            )
        return metrics

    def group_cells_by_brightness(self, metrics: list[CellMetrics]) -> list[tuple[str, list[int]]]:
        """Group cells into brightness categories.

        Args:
            metrics: Per-cell metrics to group.

        Returns:
            A list of tuples of (group_label, member_cell_ids).
        """

        if not metrics:
            return [("empty", [])]
        intensities = np.array([m.mean_intensity for m in metrics], dtype=float)
        median = float(np.median(intensities))
        low_ids = [m.cell_id for m in metrics if m.mean_intensity <= median]
        high_ids = [m.cell_id for m in metrics if m.mean_intensity > median]
        return [("dim", low_ids), ("bright", high_ids)]

    def calculate_threshold_parameters(self, metrics: list[CellMetrics]) -> ThresholdParameters:
        """Compute threshold parameters from per-cell metrics.

        Args:
            metrics: Per-cell metrics used for threshold estimation.

        Returns:
            Calculated threshold parameters.
        """

        values = np.array([m.mean_intensity for m in metrics], dtype=float)
        if values.size == 0:
            return ThresholdParameters(method="otsu", lower=None, upper=None, params={})
        if values.size == 1:
            thr = float(values[0])
            return ThresholdParameters(method="otsu", lower=thr, upper=None, params={})

        # Compute Otsu threshold on 1D intensities
        hist, bin_edges = np.histogram(values, bins=256)
        hist = hist.astype(float)
        prob = hist / hist.sum() if hist.sum() > 0 else hist
        omega = np.cumsum(prob)
        mu = np.cumsum(prob * (bin_edges[:-1]))
        mu_t = mu[-1] if mu.size > 0 else 0.0
        sigma_b_sq = (mu_t * omega - mu) ** 2 / (omega * (1.0 - omega) + 1e-12)
        idx = int(np.nanargmax(sigma_b_sq)) if sigma_b_sq.size > 0 else 0
        threshold = float(bin_edges[idx])
        return ThresholdParameters(method="otsu", lower=threshold, upper=None, params={"bins": 256})

    def analyze_binary_masks(self, mask_paths: list[Path]) -> AnalysisResult:
        """Analyze binary masks to produce aggregated results.

        Args:
            mask_paths: Paths to binary mask images.

        Returns:
            Aggregated analysis result.
        """

        try:
            import tifffile  # type: ignore
        except Exception as exc:
            raise RuntimeError("tifffile is required to analyze masks") from exc

        metrics: List[CellMetrics] = []
        for i, p in enumerate(mask_paths, start=1):
            mask = tifffile.imread(str(p))
            mask = np.asarray(mask)
            # Consider any nonzero pixel as part of the cell
            area = float(np.count_nonzero(mask))
            mean_intensity = float(mask.mean()) if mask.size else 0.0
            metrics.append(
                CellMetrics(
                    cell_id=i,
                    area=area,
                    mean_intensity=mean_intensity,
                    integrated_intensity=float(mask.sum()),
                )
            )
        return AnalysisResult(metrics=metrics)


