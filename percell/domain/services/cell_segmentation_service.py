"""Segmentation strategy rules and parameter preparation (no actual segmentation)."""

from __future__ import annotations

from typing import List, Tuple

from ..models import (
    ChannelConfig,
    ROI,
    ImageDimensions,
    SegmentationParameters,
    SegmentationPreferences,
    ValidationResult,
)


class CellSegmentationService:
    """Encodes business rules for segmentation strategy and validation.

    This service does not invoke external tools. It decides binning, channel
    selection, ROI scaling, parameter preparation, and output validation.
    """

    def calculate_binning_factor(self, image_dims: ImageDimensions, performance_target: str = "balanced") -> int:
        """Decide binning factor based on image size and performance target.

        Business rule:
        - For very large images (>4096 on either side), use 4x if performance_target != "quality".
        - For large images (>2048), use 2x unless target is "quality".
        - Never reduce below effective size 512x512.
        """

        width, height = image_dims.width, image_dims.height
        target = (performance_target or "balanced").lower()
        if max(width, height) > 4096 and target != "quality":
            return 4
        if max(width, height) > 2048 and target != "quality":
            return 2
        return 1

    def determine_segmentation_channel(self, available: List[ChannelConfig], experiment_type: str | None = None) -> ChannelConfig | None:
        """Select the optimal channel for segmentation.

        Business rule preference: nucleus > membrane > cytoplasm > first available.
        """

        role_order = ["nucleus", "membrane", "cytoplasm"]
        # Prefer explicitly marked primary
        primaries = [c for c in available if getattr(c, "is_primary", False)]
        if primaries:
            return primaries[0]
        # Prefer by semantic role
        for role in role_order:
            for c in available:
                if (c.role or "").lower() == role:
                    return c
        # Fallback: first channel
        return available[0] if available else None

    def calculate_roi_scaling(self, roi: ROI, binning_factor: int, original_dims: ImageDimensions) -> ROI:
        """Scale ROI polygon coordinates from binned to original image space.

        Business rule: simple uniform scaling by binning_factor.
        """

        if not roi.polygon or binning_factor in (0, 1):
            return roi
        scale = float(binning_factor)
        scaled = [(int(x * scale), int(y * scale)) for (x, y) in roi.polygon]
        return ROI(id=roi.id, label=roi.label, polygon=scaled, mask_path=roi.mask_path)

    def validate_segmentation_results(
        self,
        rois: List[ROI],
        expected_cell_count_range: Tuple[int, int] = (1, 10000),
        expected_cell_size_range: Tuple[float, float] = (10.0, 1e6),
    ) -> ValidationResult:
        """Validate that ROI outputs meet basic biological expectations.

        Returns ValidationResult with issues when constraints are violated.
        """

        issues: List[str] = []
        count = len(rois)
        if not (expected_cell_count_range[0] <= count <= expected_cell_count_range[1]):
            issues.append(f"cell_count_out_of_range:{count}")
        # If area available via polygon, approximate using bounding box polygon area (simple heuristic)
        for roi in rois:
            if roi.polygon and len(roi.polygon) >= 3:
                # Shoelace formula area
                area = 0.0
                pts = roi.polygon
                for i in range(len(pts)):
                    x1, y1 = pts[i]
                    x2, y2 = pts[(i + 1) % len(pts)]
                    area += x1 * y2 - x2 * y1
                area = abs(area) / 2.0
                if not (expected_cell_size_range[0] <= area <= expected_cell_size_range[1]):
                    issues.append(f"cell_area_out_of_range:{roi.id}")
        return ValidationResult(is_valid=len(issues) == 0, issues=issues)

    def prepare_segmentation_parameters(
        self,
        image_dims: ImageDimensions,
        preferences: SegmentationPreferences | None = None,
    ) -> SegmentationParameters:
        """Prepare parameters for external segmentation based on image and preferences.

        Applies institutional defaults that can be overridden via preferences.
        """

        prefs = preferences or SegmentationPreferences()
        # Defaults
        diameter = prefs.expected_cell_diameter if prefs.expected_cell_diameter else 25.0
        flow = 0.4 if prefs.performance_target != "fast" else 0.2
        prob = 0.0 if prefs.performance_target == "fast" else 0.0
        model = prefs.preferred_model or "nuclei"
        return SegmentationParameters(
            cell_diameter=diameter,
            flow_threshold=flow,
            probability_threshold=prob,
            model_type=model,
        )


