"""Intensity measurement and grouping algorithms.

Pure domain logic for computing intensity metrics and grouping cells by
brightness thresholds.
"""

from __future__ import annotations

from pathlib import Path

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

        raise NotImplementedError

    def group_cells_by_brightness(self, metrics: list[CellMetrics]) -> list[tuple[str, list[int]]]:
        """Group cells into brightness categories.

        Args:
            metrics: Per-cell metrics to group.

        Returns:
            A list of tuples of (group_label, member_cell_ids).
        """

        raise NotImplementedError

    def calculate_threshold_parameters(self, metrics: list[CellMetrics]) -> ThresholdParameters:
        """Compute threshold parameters from per-cell metrics.

        Args:
            metrics: Per-cell metrics used for threshold estimation.

        Returns:
            Calculated threshold parameters.
        """

        raise NotImplementedError

    def analyze_binary_masks(self, mask_paths: list[Path]) -> AnalysisResult:
        """Analyze binary masks to produce aggregated results.

        Args:
            mask_paths: Paths to binary mask images.

        Returns:
            Aggregated analysis result.
        """

        raise NotImplementedError


