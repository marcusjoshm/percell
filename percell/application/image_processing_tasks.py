from __future__ import annotations

"""Application-level helpers for pure image processing tasks.

Currently includes image binning previously implemented in modules/bin_images.py.
"""

from pathlib import Path
from typing import Iterable, Optional, Set

from percell.adapters.pil_image_processing_adapter import PILImageProcessingAdapter
from percell.domain import FileNamingService
import os
import shutil


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


# ------------------------- Cleanup Directories -------------------------

def get_directory_size(path: Path) -> int:
    total = 0
    try:
        if path.exists() and path.is_dir():
            for dirpath, _, filenames in os.walk(path):
                for filename in filenames:
                    fp = os.path.join(dirpath, filename)
                    try:
                        total += os.path.getsize(fp)
                    except OSError:
                        continue
    except Exception:
        return total
    return total


def format_size(size_bytes: int) -> str:
    units = ["B", "KB", "MB", "GB", "TB"]
    size = float(size_bytes)
    for unit in units:
        if size < 1024.0:
            return f"{size:.2f} {unit}"
        size /= 1024.0
    return f"{size:.2f} PB"


def scan_cleanup_directories(
    output_dir: str | Path,
    include_cells: bool = True,
    include_masks: bool = True,
    include_combined_masks: bool = False,
    include_grouped_cells: bool = False,
    include_grouped_masks: bool = False,
) -> dict[str, dict]:
    output_path = Path(output_dir)
    dir_config = {
        "cells": include_cells,
        "masks": include_masks,
        "combined_masks": include_combined_masks,
        "grouped_cells": include_grouped_cells,
        "grouped_masks": include_grouped_masks,
    }
    directories_info: dict[str, dict] = {}
    for name, enabled in dir_config.items():
        if not enabled:
            continue
        dir_path = output_path / name
        size_bytes = get_directory_size(dir_path) if dir_path.exists() else 0
        directories_info[name] = {
            "path": str(dir_path),
            "exists": dir_path.exists(),
            "size_bytes": size_bytes,
            "size_formatted": format_size(size_bytes),
        }
    return directories_info


def cleanup_directories(
    output_dir: str | Path,
    delete_cells: bool = False,
    delete_masks: bool = False,
    delete_combined_masks: bool = False,
    delete_grouped_cells: bool = False,
    delete_grouped_masks: bool = False,
    dry_run: bool = False,
    force: bool = True,
) -> tuple[int, int]:
    output_path = Path(output_dir)
    if not output_path.exists():
        return 0, 0
    info = scan_cleanup_directories(
        output_dir,
        include_cells=delete_cells,
        include_masks=delete_masks,
        include_combined_masks=delete_combined_masks,
        include_grouped_cells=delete_grouped_cells,
        include_grouped_masks=delete_grouped_masks,
    )
    if not info or dry_run:
        return 0, 0
    emptied = 0
    freed = 0
    for name, meta in info.items():
        if not meta.get("exists"):
            continue
        dir_path = Path(meta["path"])  # type: ignore[index]
        try:
            size = meta.get("size_bytes", 0)
            for item in dir_path.iterdir():
                if item.is_file():
                    item.unlink()
                elif item.is_dir():
                    shutil.rmtree(item)
            emptied += 1
            freed += int(size)
        except Exception:
            continue
    return emptied, freed


