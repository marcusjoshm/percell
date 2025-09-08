"""Intensity measurement and grouping algorithms.

Pure domain logic for computing intensity metrics and grouping cells by
brightness thresholds.
"""

from __future__ import annotations

from pathlib import Path
from typing import List, Tuple, Iterable, Union

import numpy as np

from ..models import AnalysisResult, CellMetrics, ROI, ThresholdParameters


class IntensityAnalysisService:
    """Provides per-cell intensity analysis algorithms."""

    def measure_cell_intensity(self, image: Union[np.ndarray, Path], rois: list[ROI]) -> list[CellMetrics]:
        """Measure intensity metrics for each ROI in an image.

        Accepts an in-memory image array (preferred) to keep IO out of the domain.
        A Path may be provided for backward compatibility, but will be read here
        as a convenience shim.

        Args:
            image: 2D grayscale image as ndarray (preferred) or a Path (legacy).
            rois: Regions of interest representing cells.

        Returns:
            List of per-cell metrics.
        """

        if isinstance(image, Path):
            # Backward-compatibility shim; prefer measure_cell_intensity_from_array.
            try:
                import tifffile  # type: ignore
            except Exception as exc:
                raise RuntimeError("tifffile is required to read image paths; prefer passing arrays") from exc
            img = tifffile.imread(str(image))
        else:
            img = image

        if img is None:
            raise ValueError("Image is None")

        # Ensure 2D grayscale for basic analysis
        if getattr(img, "ndim", 0) > 2:
            img = np.asarray(img).squeeze()

        metrics: List[CellMetrics] = []
        # NOTE: ROI geometry is not yet implemented; compute global stats per ROI as placeholder
        img_values = np.asarray(img).astype(np.float64)
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

    def measure_cell_intensity_from_array(self, image: np.ndarray, rois: list[ROI]) -> list[CellMetrics]:
        """Measure cell intensities from an in-memory array (strict, no IO)."""
        return self.measure_cell_intensity(image, rois)

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
        """Placeholder for thresholding which is handled by ImageJ.

        Domain layer does not compute threshold parameters; external tools
        (e.g., ImageJ) are responsible. This method is intentionally not
        implemented to keep thresholding out of business logic.
        """

        raise NotImplementedError("Thresholding is performed by ImageJ adapter, not the domain service")

    def analyze_binary_masks(self, mask_paths: list[Path]) -> AnalysisResult:
        """Analyze binary masks from paths (legacy convenience)."""
        try:
            import tifffile  # type: ignore
        except Exception as exc:
            raise RuntimeError("tifffile is required to read mask paths; prefer passing arrays") from exc
        masks = [np.asarray(tifffile.imread(str(p))) for p in mask_paths]
        return self.analyze_binary_masks_from_arrays(masks)

    def analyze_binary_masks_from_arrays(self, masks: Iterable[np.ndarray]) -> AnalysisResult:
        """Analyze binary masks from in-memory arrays (preferred, no IO)."""
        metrics: List[CellMetrics] = []
        for i, mask in enumerate(masks, start=1):
            arr = np.asarray(mask)
            area = float(np.count_nonzero(arr))
            mean_intensity = float(arr.mean()) if arr.size else 0.0
            metrics.append(
                CellMetrics(
                    cell_id=i,
                    area=area,
                    mean_intensity=mean_intensity,
                    integrated_intensity=float(arr.sum()),
                )
            )
        return AnalysisResult(metrics=metrics)


