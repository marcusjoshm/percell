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
import numpy as np


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


# ------------------------- Combine Masks -------------------------

def _get_mask_prefix(filename: str) -> str | None:
    parts = filename.split("_bin_")
    if len(parts) < 2:
        return None
    return parts[0]


def _find_mask_groups(mask_dir: Path) -> dict[str, list[Path]]:
    groups: dict[str, list[Path]] = {}
    for mask_file in mask_dir.glob("*_bin_*.tif"):
        prefix = _get_mask_prefix(mask_file.name)
        if not prefix:
            continue
        groups.setdefault(prefix, []).append(mask_file)
    return groups


def combine_masks(
    input_dir: str | Path,
    output_dir: str | Path,
    channels: Optional[Iterable[str]] = None,
) -> bool:
    """Combine grouped binary masks into single masks under combined_masks.

    Returns True if at least one combined mask was written.
    """
    in_root = Path(input_dir)
    out_root = Path(output_dir)
    out_root.mkdir(parents=True, exist_ok=True)

    adapter = PILImageProcessingAdapter()
    any_written = False

    # Expect layout: input_dir/<condition>/<region_timepoint>
    for condition_dir in in_root.glob("*"):
        if not condition_dir.is_dir():
            continue
        for rt_dir in condition_dir.glob("*"):
            if not rt_dir.is_dir():
                continue
            groups = _find_mask_groups(rt_dir)
            if not groups:
                continue
            out_condition = out_root / condition_dir.name
            out_condition.mkdir(parents=True, exist_ok=True)
            for prefix, files in groups.items():
                if not files:
                    continue
                # Read first to get shape/dtype
                try:
                    first = adapter.read_image(files[0])
                    combined = np.zeros_like(first, dtype=np.uint8)
                except Exception:
                    continue
                for f in files:
                    try:
                        img = adapter.read_image(f)
                        combined = np.maximum(combined, img.astype(np.uint8))
                    except Exception:
                        continue
                out_path = out_condition / f"{prefix}.tif"
                try:
                    adapter.write_image(out_path, combined)
                    any_written = True
                except Exception:
                    continue

    return any_written


# ------------------------- Group Cells -------------------------

def _find_cell_dirs(cells_dir: Path) -> list[Path]:
    dirs: list[Path] = []
    for condition_dir in cells_dir.glob("*"):
        if not condition_dir.is_dir() or condition_dir.name.startswith('.'):
            continue
        for region_dir in condition_dir.glob("*"):
            if not region_dir.is_dir() or region_dir.name.startswith('.'):
                continue
            if list(region_dir.glob("CELL*.tif")):
                dirs.append(region_dir)
    return dirs


def group_cells(
    cells_dir: str | Path,
    output_dir: str | Path,
    bins: int = 5,
    force_clusters: bool = True,
    channels: Optional[Iterable[str]] = None,
) -> bool:
    """Group cell images by simple intensity and write summed images per group.

    Produces files named "<region_dir_name>_bin_<i>.tif" under
    <output_dir>/<condition>/<region_dir_name>/ for i in 1..bins.
    """
    cells_root = Path(cells_dir)
    out_root = Path(output_dir)
    out_root.mkdir(parents=True, exist_ok=True)

    adapter = PILImageProcessingAdapter()
    any_written = False

    for region_dir in _find_cell_dirs(cells_root):
        if channels:
            # Skip dirs not matching any requested channels in path
            if not any(ch in str(region_dir) for ch in channels):
                continue

        condition = region_dir.parent.name
        out_condition = out_root / condition / region_dir.name
        out_condition.mkdir(parents=True, exist_ok=True)

        # Gather images and simple intensity metric
        cell_files = list(region_dir.glob("CELL*.tif"))
        if not cell_files:
            continue
        images: list[tuple[Path, np.ndarray, float]] = []
        for f in cell_files:
            try:
                img = adapter.read_image(f)
                metric = float(np.mean(img))
                images.append((f, img, metric))
            except Exception:
                continue
        if not images:
            continue

        # Sort by intensity and split into bins
        images.sort(key=lambda x: x[2])
        n = len(images)
        k = max(1, min(bins, n))
        base = n // k
        rem = n % k
        start = 0
        for i in range(k):
            size = base + (1 if i < rem else 0)
            end = start + size
            group = images[start:end]
            start = end
            if not group:
                continue
            # Sum images (resize not handled; assume uniform dims per dir)
            try:
                acc = None
                for _, img, _ in group:
                    gi = img.astype(np.float64)
                    if acc is None:
                        acc = gi
                    else:
                        acc = acc + gi
                if acc is None:
                    continue
                # Normalize to uint16 range for safety
                acc_min = np.min(acc)
                acc_max = np.max(acc)
                if acc_max > acc_min:
                    norm = (acc - acc_min) / (acc_max - acc_min)
                else:
                    norm = acc * 0
                out_img = (norm * 65535).astype(np.uint16)
                out_path = out_condition / f"{region_dir.name}_bin_{i+1}.tif"
                adapter.write_image(out_path, out_img)
                any_written = True
            except Exception:
                continue

    return any_written


# ------------------------- Duplicate ROIs for Channels -------------------------

def duplicate_rois_for_channels(
    roi_dir: str | Path,
    channels: Optional[Iterable[str]],
    verbose: bool = False,
) -> bool:
    """Duplicate ROI .zip files to match analysis channels by swapping channel token.

    ROI names are expected to contain a channel token like _chNN_. For each ROI file, copies
    will be created for each requested analysis channel (skipping the original if it already
    matches). Returns True if at least one copy was made or all requested channels already exist.
    """
    if not channels:
        return True
    roi_root = Path(roi_dir)
    if not roi_root.exists():
        return False
    roi_files = list(roi_root.rglob("*.zip"))
    if not roi_files:
        return False
    from percell.adapters.local_filesystem_adapter import LocalFileSystemAdapter
    fs = LocalFileSystemAdapter()

    import re as _re

    successful = 0
    channels_already_exist: set[str] = set()
    channels_processed: set[str] = set()

    for rf in roi_files:
        m = _re.search(r"_ch\d+_", rf.name)
        if not m:
            continue
        src_channel = m.group(0).strip("_")
        if src_channel in channels:
            channels_already_exist.add(src_channel)
        for target in channels:
            if target == src_channel:
                continue
            new_name = _re.sub(r"_ch\d+_", f"_{target}_", rf.name)
            dst = rf.parent / new_name
            try:
                fs.copy(rf, dst, overwrite=True)
                successful += 1
                channels_processed.add(target)
            except Exception:
                continue

    all_available = channels_already_exist.union(channels_processed)
    missing = set(channels) - all_available
    if missing:
        return False
    return successful > 0 or bool(channels_already_exist)


