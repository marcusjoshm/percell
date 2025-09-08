from __future__ import annotations

"""Application-level helpers for pure image processing tasks.

Currently includes image binning previously implemented in modules/bin_images.py.
"""

from pathlib import Path
from typing import Iterable, Optional, Set

from percell.adapters.pil_image_processing_adapter import PILImageProcessingAdapter
from percell.domain import FileNamingService


def _to_optional_set(values: Optional[Iterable[str]]) -> Optional[Set[str]]:
    if not values:
        return None
    s = set(values)
    if {"all"}.issubset(s):
        return None
    return s


def bin_images(
    input_dir: str | Path,
    output_dir: str | Path,
    bin_factor: int = 4,
    conditions: Optional[Iterable[str]] = None,
    regions: Optional[Iterable[str]] = None,
    timepoints: Optional[Iterable[str]] = None,
    channels: Optional[Iterable[str]] = None,
) -> int:
    """Bin images from input_dir to output_dir with optional filtering.

    Returns number of processed images.
    """
    input_path = Path(input_dir)
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    selected_conditions = _to_optional_set(conditions)
    selected_regions = _to_optional_set(regions)
    selected_timepoints = _to_optional_set(timepoints)
    selected_channels = _to_optional_set(channels)

    naming_service = FileNamingService()
    adapter = PILImageProcessingAdapter()

    processed_count = 0
    for file_path in input_path.glob("**/*.tif"):
        file_path = Path(file_path)

        try:
            rel = file_path.relative_to(input_path)
            current_condition = rel.parts[0] if rel.parts else None
            if not current_condition:
                continue
            if selected_conditions is not None and current_condition not in selected_conditions:
                continue

            meta = naming_service.parse_microscopy_filename(file_path.name)
            current_region = meta.region
            current_timepoint = meta.timepoint
            current_channel = meta.channel

            if selected_regions is not None and (not current_region or current_region not in selected_regions):
                continue
            if selected_timepoints is not None and (not current_timepoint or current_timepoint not in selected_timepoints):
                continue
            if selected_channels is not None and (not current_channel or current_channel not in selected_channels):
                continue

            out_file = output_path / rel.parent / f"bin4x4_{file_path.name}"
            out_file.parent.mkdir(parents=True, exist_ok=True)

            image = adapter.read_image(file_path)
            binned = adapter.bin_image(image, bin_factor)
            adapter.write_image(out_file, binned.astype(image.dtype))
            processed_count += 1
        except Exception:
            # Skip problematic files; upstream logs can indicate progress totals
            continue

    return processed_count


