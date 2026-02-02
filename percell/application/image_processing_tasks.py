from __future__ import annotations

"""Application-level helpers for image processing orchestration.

Provides orchestration functions that delegate to domain services for business logic.
"""

from pathlib import Path
from typing import Iterable, Optional, Set, List, Tuple
from percell.ports.driven.image_processing_port import ImageProcessingPort
from percell.ports.driven.file_management_port import FileManagementPort
from percell.ports.driven.progress_report_port import ProgressReportPort
from percell.domain import FileNamingService
from percell.domain.services.image_binning_service import ImageBinningService
import os
import shutil
import re as _re
import pandas as pd
import numpy as np

# Import metadata service for centralized metadata handling
from percell.domain.services.image_metadata_service import ImageMetadataService
from percell.domain.models import ImageMetadata
from percell.domain.utils.filesystem_filters import is_system_hidden_file

# Glob pattern for individual cell image files
_CELL_FILE_PATTERN = "CELL*.tif"


def _to_optional_set(values: Optional[Iterable[str]]) -> Optional[Set[str]]:
    """Convert an iterable to an optional set, handling 'all' keyword."""
    if not values:
        return None
    s = set(values)
    if {"all"}.issubset(s):
        return None
    return s

def _extract_tiff_metadata(
    image_path: Path,
    metadata_service: Optional[ImageMetadataService] = None
) -> Optional[ImageMetadata]:
    """Extract TIFF metadata from an image file using centralized service.

    Args:
        image_path: Path to the TIFF image file
        metadata_service: Metadata service instance (creates if not provided)

    Returns:
        ImageMetadata or None: Extracted metadata object, or None if extraction fails
    """
    if metadata_service is None:
        metadata_service = ImageMetadataService()

    try:
        metadata = metadata_service.extract_metadata(image_path)
        return metadata if metadata.has_resolution_info() else None
    except Exception as e:
        print(f"Error extracting metadata from {image_path.name}: {e}")
        return None


def _write_tiff_with_metadata(
    output_path: Path,
    image: np.ndarray,
    metadata: Optional[ImageMetadata] = None,
    metadata_service: Optional[ImageMetadataService] = None
) -> bool:
    """Write a TIFF image with metadata preservation using centralized service.

    Args:
        output_path: Path where to save the image
        image: Image data to save
        metadata: Metadata to preserve
        metadata_service: Metadata service instance (creates if not provided)

    Returns:
        bool: True if successful, False otherwise
    """
    if metadata_service is None:
        metadata_service = ImageMetadataService()

    try:
        return metadata_service.save_image_with_metadata(image, output_path, metadata)
    except Exception as e:
        print(f"Error writing {output_path.name} with metadata: {e}")
        return False


def bin_images(
    input_dir: str | Path,
    output_dir: str | Path,
    bin_factor: int = 4,
    conditions: Optional[Iterable[str]] = None,
    regions: Optional[Iterable[str]] = None,
    timepoints: Optional[Iterable[str]] = None,
    channels: Optional[Iterable[str]] = None,
    *,
    imgproc: Optional[ImageProcessingPort] = None,
    progress: Optional[ProgressReportPort] = None,
) -> int:
    """Bin images from input_dir to output_dir with optional filtering.

    This is an orchestration function that delegates business logic to
    ImageBinningService in the domain layer.

    Args:
        input_dir: Source directory containing images
        output_dir: Destination directory for binned images
        bin_factor: Binning factor (e.g., 4 for 4x4 binning)
        conditions: Conditions to include (None = all)
        regions: Regions to include (None = all)
        timepoints: Timepoints to include (None = all)
        channels: Channels to include (None = all)
        imgproc: Image processing port (creates adapter if not provided)
        progress: Progress reporting port (optional)

    Returns:
        Number of images successfully processed
    """
    input_path = Path(input_dir)
    output_path = Path(output_dir)

    # Convert iterables to sets
    selected_conditions = _to_optional_set(conditions)
    selected_regions = _to_optional_set(regions)
    selected_timepoints = _to_optional_set(timepoints)
    selected_channels = _to_optional_set(channels)

    # Create image processor if not provided
    if imgproc is None:
        from percell.adapters.pil_image_processing_adapter import PILImageProcessingAdapter
        imgproc = PILImageProcessingAdapter()

    # Create binning service with image processor
    binning_service = ImageBinningService(imgproc)

    # Delegate to domain service
    return binning_service.bin_images(
        input_path,
        output_path,
        bin_factor,
        selected_conditions,
        selected_regions,
        selected_timepoints,
        selected_channels,
    )


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


def _delete_single_item(item: Path, logger) -> bool:
    """Delete a single file or directory. Returns True if deleted successfully."""
    try:
        if item.is_file():
            item.unlink(missing_ok=True)
            return True
        if item.is_dir():
            shutil.rmtree(item, ignore_errors=True)
            return True
        return False
    except PermissionError as pe:
        logger.error(f"Permission denied deleting {item}: {pe}")
        return False
    except FileNotFoundError:
        # Race condition with ._ files on exFAT - already deleted
        return False
    except OSError as oe:
        # ENOENT (errno 2) can happen with ._ files - ignore it
        if oe.errno != 2:
            logger.error(f"OS error deleting {item}: {oe}")
        return False


def _clean_single_directory(dir_path: Path, name: str, size: int, logger) -> tuple[bool, int]:
    """Clean contents of a single directory. Returns (success, size_freed)."""
    try:
        items_deleted = sum(
            1 for item in dir_path.iterdir() if _delete_single_item(item, logger)
        )
        logger.info(f"Deleted {items_deleted} items from {name}")
        return True, int(size)
    except PermissionError as pe:
        logger.error(f"Permission denied accessing {dir_path}: {pe}")
        return False, 0
    except OSError as oe:
        logger.error(f"OS error accessing {dir_path}: {oe}")
        return False, 0
    except Exception as e:
        logger.error(f"Unexpected error cleaning {dir_path}: {type(e).__name__}: {e}")
        return False, 0


def cleanup_directories(
    output_dir: str | Path,
    delete_cells: bool = False,
    delete_masks: bool = False,
    delete_combined_masks: bool = False,
    delete_grouped_cells: bool = False,
    delete_grouped_masks: bool = False,
    dry_run: bool = False,
    force: bool = True,
    logger=None,
) -> tuple[int, int]:
    import logging
    if logger is None:
        logger = logging.getLogger(__name__)

    output_path = Path(output_dir)
    if not output_path.exists():
        logger.warning(f"Output directory does not exist: {output_path}")
        return 0, 0

    info = scan_cleanup_directories(
        output_dir,
        include_cells=delete_cells,
        include_masks=delete_masks,
        include_combined_masks=delete_combined_masks,
        include_grouped_cells=delete_grouped_cells,
        include_grouped_masks=delete_grouped_masks,
    )
    if not info:
        logger.warning("No directories found to clean up")
        return 0, 0
    if dry_run:
        logger.info("Dry run mode - no files will be deleted")
        return 0, 0

    emptied = 0
    freed = 0
    for name, meta in info.items():
        if not meta.get("exists"):
            logger.debug(f"Skipping {name}: directory does not exist")
            continue
        dir_path = Path(meta["path"])  # type: ignore[index]
        logger.info(f"Cleaning up directory: {dir_path}")
        size = meta.get("size_bytes", 0)
        success, size_freed = _clean_single_directory(dir_path, name, size, logger)
        if success:
            emptied += 1
            freed += size_freed

    return emptied, freed


# ------------------------- Combine Masks -------------------------

def _get_mask_prefix(filename: str) -> str | None:
    parts = filename.split("_bin_")
    if len(parts) < 2:
        return None
    return parts[0]


def _find_mask_groups(mask_dir: Path) -> dict[str, list[Path]]:
    groups: dict[str, list[Path]] = {}
    # Filter out system metadata files (e.g., ._ files on exFAT)
    mask_files = [mf for mf in mask_dir.glob("*_bin_*.tif") if not is_system_hidden_file(mf)]
    for mask_file in mask_files:
        prefix = _get_mask_prefix(mask_file.name)
        if not prefix:
            continue
        groups.setdefault(prefix, []).append(mask_file)
    return groups


def _is_valid_subdir(path: Path) -> bool:
    """Check if path is a valid non-hidden directory."""
    return path.is_dir() and not is_system_hidden_file(path)


def _matches_region_filter(dir_name: str, regions_set: Optional[set]) -> bool:
    """Check if directory name matches any region in the filter set."""
    if regions_set is None:
        return True
    return any(region in dir_name for region in regions_set)


def _init_combined_mask(files: list[Path], prefix: str, imgproc):
    """Initialize combined mask array and extract metadata from first file."""
    first = imgproc.read_image(files[0])
    combined = np.zeros_like(first, dtype=np.uint8)
    print(f"Attempting to extract metadata from: {files[0].name}")
    reference_metadata = _extract_tiff_metadata(files[0])
    if reference_metadata:
        print(f"Successfully extracted metadata for group {prefix}")
    else:
        print(f"No metadata extracted for group {prefix}")
    return combined, reference_metadata


def _accumulate_masks(files: list[Path], combined: np.ndarray, imgproc) -> np.ndarray:
    """Accumulate all mask files into the combined array using maximum."""
    for f in files:
        try:
            img = imgproc.read_image(f)
            combined = np.maximum(combined, img.astype(np.uint8))
        except Exception:
            continue
    return combined


def _write_combined_mask(out_path: Path, combined: np.ndarray, metadata, imgproc) -> bool:
    """Write combined mask with metadata preservation, falling back to imgproc."""
    print(f"Writing combined mask: {out_path.name}")
    if metadata and metadata.has_resolution_info():
        print("Using metadata with resolution info")
    else:
        print("No metadata available for writing")

    if not _write_tiff_with_metadata(out_path, combined, metadata):
        print(f"Metadata write failed, falling back to imgproc.write_image for {out_path.name}")
        imgproc.write_image(out_path, combined)
    else:
        print(f"Successfully wrote {out_path.name} with metadata preservation")
    return True


def _process_mask_group(
    prefix: str, files: list[Path], out_condition: Path, imgproc
) -> bool:
    """Process a single mask group: combine files and write output."""
    if not files:
        return False
    try:
        combined, reference_metadata = _init_combined_mask(files, prefix, imgproc)
    except Exception as e:
        print(f"Error processing group {prefix}: {e}")
        return False

    combined = _accumulate_masks(files, combined, imgproc)
    out_path = out_condition / f"{prefix}.tif"

    try:
        return _write_combined_mask(out_path, combined, reference_metadata, imgproc)
    except Exception as e:
        print(f"Error writing {out_path.name}: {e}")
        return False


def _process_region_timepoint_dir(
    rt_dir: Path, out_condition: Path, imgproc
) -> bool:
    """Process all mask groups in a region/timepoint directory."""
    groups = _find_mask_groups(rt_dir)
    if not groups:
        return False

    out_condition.mkdir(parents=True, exist_ok=True)
    any_written = False
    for prefix, files in groups.items():
        if _process_mask_group(prefix, files, out_condition, imgproc):
            any_written = True
    return any_written


def combine_masks(
    input_dir: str | Path,
    output_dir: str | Path,
    channels: Optional[Iterable[str]] = None,
    regions: Optional[Iterable[str]] = None,
    *,
    imgproc: Optional[ImageProcessingPort] = None,
) -> bool:
    """Combine grouped binary masks into single masks under combined_masks.

    Args:
        input_dir: Directory containing grouped masks
        output_dir: Directory to write combined masks
        channels: Optional list of channels to filter by
        regions: Optional list of regions to filter by
        imgproc: Optional image processing adapter

    Returns True if at least one combined mask was written.
    Preserves TIFF metadata (resolution, units, etc.) from the first mask file
    in each group when writing the combined masks, if tifffile is available.
    """
    in_root = Path(input_dir)
    out_root = Path(output_dir)
    out_root.mkdir(parents=True, exist_ok=True)

    if imgproc is None:
        from percell.adapters.pil_image_processing_adapter import PILImageProcessingAdapter  # type: ignore
        imgproc = PILImageProcessingAdapter()

    regions_set = _to_optional_set(regions)
    any_written = False

    # Expect layout: input_dir/<condition>/<region_timepoint>
    for condition_dir in in_root.glob("*"):
        if not _is_valid_subdir(condition_dir):
            continue
        out_condition = out_root / condition_dir.name
        for rt_dir in condition_dir.glob("*"):
            if not _is_valid_subdir(rt_dir):
                continue
            if not _matches_region_filter(rt_dir.name, regions_set):
                continue
            if _process_region_timepoint_dir(rt_dir, out_condition, imgproc):
                any_written = True

    return any_written


# ------------------------- Group Cells -------------------------

def _filter_region_dirs_by_channels(
    region_dirs: list[Path], channels: Optional[Iterable[str]]
) -> list[Path]:
    """Filter region directories by channel names if channels are specified."""
    if not channels:
        return region_dirs
    filtered = [d for d in region_dirs if any(ch in str(d) for ch in channels)]
    return filtered if filtered else region_dirs


def _count_total_cells(region_dirs: list[Path]) -> int:
    """Count total cell files across all region directories."""
    total = 0
    for region_dir in region_dirs:
        cell_files = [cf for cf in region_dir.glob(_CELL_FILE_PATTERN) if not is_system_hidden_file(cf)]
        total += len(cell_files)
    return total


def _load_cell_images(
    region_dir: Path, imgproc: ImageProcessingPort
) -> tuple[list[tuple[Path, np.ndarray, float]], Optional[ImageMetadata]]:
    """Load cell images from a region directory with intensity metrics.

    Returns:
        Tuple of (list of (path, image, metric), reference_metadata)
    """
    cell_files = [cf for cf in region_dir.glob(_CELL_FILE_PATTERN) if not is_system_hidden_file(cf)]
    images: list[tuple[Path, np.ndarray, float]] = []
    reference_metadata = None

    for f in cell_files:
        try:
            img = imgproc.read_image(f)
            metric = float(np.mean(img))
            images.append((f, img, metric))
            if reference_metadata is None:
                reference_metadata = _extract_tiff_metadata(f)
        except Exception:
            continue

    return images, reference_metadata


def _sum_group_images(group: list[tuple[Path, np.ndarray, float]]) -> Optional[np.ndarray]:
    """Sum images in a group and normalize to uint16.

    Returns:
        Normalized uint16 image or None if group is empty.
    """
    if not group:
        return None

    acc = None
    for _, img, _ in group:
        gi = img.astype(np.float64)
        if acc is None:
            acc = gi
        else:
            acc = acc + gi

    if acc is None:
        return None

    acc_min = np.min(acc)
    acc_max = np.max(acc)
    if acc_max > acc_min:
        norm = (acc - acc_min) / (acc_max - acc_min)
    else:
        norm = acc * 0

    return (norm * 65535).astype(np.uint16)


def _record_group_metadata(
    rows: list[dict[str, object]],
    group: list[tuple[Path, np.ndarray, float]],
    bin_index: int,
) -> None:
    """Record metadata rows for cells assigned to a bin."""
    group_metrics = [metric for _, __, metric in group]
    group_mean = float(np.mean(group_metrics)) if group_metrics else 0.0

    for path_obj, __, ___ in group:
        rows.append({
            'cell_id': path_obj.name,
            'group_id': bin_index + 1,
            'group_name': f"bin_{bin_index + 1}",
            'group_mean_auc': group_mean,
        })


def _write_group_csv(out_condition: Path, region_name: str, rows: list[dict[str, object]]) -> None:
    """Write group metadata to CSV file."""
    if not rows:
        return
    try:
        import pandas as _pd
        csv_path = out_condition / f"{region_name}_cell_groups.csv"
        _pd.DataFrame(rows).to_csv(csv_path, index=False)
    except Exception:
        pass


def _process_region_bins(
    images: list[tuple[Path, np.ndarray, float]],
    bins: int,
    out_condition: Path,
    region_name: str,
    reference_metadata: Optional[ImageMetadata],
    imgproc: ImageProcessingPort,
    rows: list[dict[str, object]],
) -> bool:
    """Process a region's images into bins and write summed images.

    Returns:
        True if any image was written successfully.
    """
    images.sort(key=lambda x: x[2])
    n = len(images)
    k = max(1, min(bins, n))
    base = n // k
    rem = n % k
    start = 0
    any_written = False

    for i in range(k):
        size = base + (1 if i < rem else 0)
        end = start + size
        group = images[start:end]
        start = end

        if not group:
            continue

        _record_group_metadata(rows, group, i)

        try:
            out_img = _sum_group_images(group)
            if out_img is None:
                continue

            out_path = out_condition / f"{region_name}_bin_{i + 1}.tif"
            print(f"Saving grouped image: {out_path.name} (shape: {out_img.shape}, dtype: {out_img.dtype})")

            if not _write_tiff_with_metadata(out_path, out_img, reference_metadata):
                imgproc.write_image(out_path, out_img)
            any_written = True
        except Exception:
            continue

    return any_written


def _find_cell_dirs(cells_dir: Path) -> list[Path]:
    dirs: list[Path] = []
    for condition_dir in cells_dir.glob("*"):
        if not condition_dir.is_dir() or is_system_hidden_file(condition_dir):
            continue
        for region_dir in condition_dir.glob("*"):
            if not region_dir.is_dir() or is_system_hidden_file(region_dir):
                continue
            # Filter out system metadata files when checking for CELL files
            cell_files = [cf for cf in region_dir.glob(_CELL_FILE_PATTERN) if not is_system_hidden_file(cf)]
            if cell_files:
                dirs.append(region_dir)
    return dirs


def _create_progress_context(
    progress: Optional[ProgressReportPort], regions_count: int, title: str
):
    """Create a progress context manager for region processing."""
    if progress:
        return progress.create_progress_bar(total=regions_count, title=title, manual=False)
    from contextlib import nullcontext
    print(title)
    return nullcontext(lambda _: None)


def _process_single_region(
    region_dir: Path,
    out_root: Path,
    bins: int,
    imgproc: ImageProcessingPort,
) -> bool:
    """Process a single region directory: load images, bin them, write outputs.

    Returns:
        True if any image was written successfully.
    """
    out_condition = out_root / region_dir.parent.name / region_dir.name
    out_condition.mkdir(parents=True, exist_ok=True)

    images, reference_metadata = _load_cell_images(region_dir, imgproc)
    if not images:
        return False

    rows: list[dict[str, object]] = []
    any_written = _process_region_bins(
        images, bins, out_condition, region_dir.name, reference_metadata, imgproc, rows
    )

    _write_group_csv(out_condition, region_dir.name, rows)
    return any_written


def group_cells(
    cells_dir: str | Path,
    output_dir: str | Path,
    bins: int = 5,
    force_clusters: bool = True,
    channels: Optional[Iterable[str]] = None,
    *,
    imgproc: Optional[ImageProcessingPort] = None,
    progress: Optional[ProgressReportPort] = None,
) -> bool:
    """Group cell images by simple intensity and write summed images per group.

    Produces files named "<region_dir_name>_bin_<i>.tif" under
    <output_dir>/<condition>/<region_dir_name>/ for i in 1..bins.

    Preserves TIFF metadata (resolution, units, etc.) from the first cell image
    in each region when writing the summed images, if tifffile is available.
    """
    cells_root = Path(cells_dir)
    out_root = Path(output_dir)
    out_root.mkdir(parents=True, exist_ok=True)

    if imgproc is None:
        from percell.adapters.pil_image_processing_adapter import PILImageProcessingAdapter
        imgproc = PILImageProcessingAdapter()

    region_dirs = _find_cell_dirs(cells_root)
    region_dirs = _filter_region_dirs_by_channels(region_dirs, channels)
    total_cells = _count_total_cells(region_dirs)

    regions_count = len(region_dirs)
    title = f"Grouping {total_cells} cells into {bins} bins across {regions_count} regions"
    progress_ctx = _create_progress_context(progress, regions_count, title)

    any_written = False
    with progress_ctx as update:
        for region_dir in region_dirs:
            if _process_single_region(region_dir, out_root, bins, imgproc):
                any_written = True
            update(1)

    return any_written


# ------------------------- Duplicate ROIs for Channels -------------------------

# Regex pattern for channel token in ROI filenames
_ROI_CHANNEL_PATTERN = r"_ch\d+_"


def _copy_roi_to_channel(
    rf: Path, target: str, fs: FileManagementPort
) -> bool:
    """Copy a single ROI file with a new channel token. Returns True on success."""
    import re as _re
    new_name = _re.sub(_ROI_CHANNEL_PATTERN, f"_{target}_", rf.name)
    dst = rf.parent / new_name
    try:
        fs.copy(rf, dst, overwrite=True)  # type: ignore[call-arg]
        return True
    except Exception:
        return False


def _process_roi_file(
    rf: Path,
    channels: Iterable[str],
    fs: FileManagementPort,
    channels_already_exist: set[str],
    channels_processed: set[str],
) -> int:
    """Process a single ROI file, copying it for each target channel.

    Returns:
        Number of successful copies made.
    """
    import re as _re
    m = _re.search(_ROI_CHANNEL_PATTERN, rf.name)
    if not m:
        return 0

    src_channel = m.group(0).strip("_")
    if src_channel in channels:
        channels_already_exist.add(src_channel)

    successful = 0
    for target in channels:
        if target == src_channel:
            continue
        if _copy_roi_to_channel(rf, target, fs):
            successful += 1
            channels_processed.add(target)

    return successful


def duplicate_rois_for_channels(
    roi_dir: str | Path,
    channels: Optional[Iterable[str]],
    verbose: bool = False,
    *,
    fs: Optional[FileManagementPort] = None,
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

    if fs is None:
        from percell.adapters.local_filesystem_adapter import LocalFileSystemAdapter
        fs = LocalFileSystemAdapter()

    channels_already_exist: set[str] = set()
    channels_processed: set[str] = set()
    successful = 0

    for rf in roi_files:
        successful += _process_roi_file(
            rf, channels, fs, channels_already_exist, channels_processed
        )

    all_available = channels_already_exist.union(channels_processed)
    missing = set(channels) - all_available
    if missing:
        return False

    return successful > 0 or bool(channels_already_exist)


# ------------------------- Include Group Metadata -------------------------

def _read_csv_robust(file_path: Path) -> pd.DataFrame | None:
    for enc in ['utf-8', 'utf-8-sig', 'latin-1', 'cp1252', 'iso-8859-1']:
        try:
            return pd.read_csv(file_path, encoding=enc)
        except UnicodeDecodeError:
            continue
        except Exception:
            continue
    return None


def _find_group_metadata_files(grouped_cells_dir: Path) -> list[Path]:
    return [p for p in grouped_cells_dir.rglob("*_cell_groups.csv") if not p.name.startswith('._')]


def _find_analysis_file(analysis_dir: Path, output_dir: Path | None) -> Path | None:
    if output_dir is not None:
        dish_name = output_dir.name.replace('_analysis_', '').replace('/', '_')
        dish_file = analysis_dir / f"{dish_name}_combined_analysis.csv"
        if dish_file.exists() and not is_system_hidden_file(dish_file):
            return dish_file
    for pattern in ["*combined*.csv", "*combined_analysis.csv", "combined_results.csv"]:
        matches = [f for f in analysis_dir.glob(pattern) if not is_system_hidden_file(f)]
        if matches:
            matches.sort(key=lambda f: f.stat().st_size, reverse=True)
            return matches[0]
    csvs = [f for f in analysis_dir.glob("*.csv") if not is_system_hidden_file(f)]
    if csvs:
        csvs.sort(key=lambda f: f.stat().st_size, reverse=True)
        return csvs[0]
    return None


def _filter_metadata_by_channels(
    metadata_files: list[Path], channels: Optional[Iterable[str]]
) -> list[Path]:
    """Filter metadata files by channel names if specified."""
    if not channels:
        return metadata_files
    filtered = [p for p in metadata_files if any(ch in str(p) for ch in channels)]
    return filtered if filtered else metadata_files


def _load_single_metadata_file(p: Path) -> Optional[pd.DataFrame]:
    """Load a single metadata file and add region/condition columns."""
    df = _read_csv_robust(p)
    if df is None:
        return None

    parent = p.parent
    region = parent.name
    condition = parent.parent.name if parent.parent.name != "grouped_cells" else ""

    df = df.copy()
    df['region'] = region
    if condition:
        df['condition'] = condition
    return df


def _load_and_augment_metadata(metadata_files: list[Path]) -> Optional[pd.DataFrame]:
    """Load all metadata files and combine into a single DataFrame."""
    frames = [_load_single_metadata_file(p) for p in metadata_files]
    frames = [f for f in frames if f is not None]
    if not frames:
        return None
    return pd.concat(frames, ignore_index=True)


def _clean_cell_id_value(x: object) -> str:
    """Clean a cell ID value by removing common prefixes/suffixes."""
    s = str(x) if isinstance(x, str) else str(x)
    return s.replace('CELL', '').replace('.tif', '').strip()


def _derive_meta_cell_id(meta_df: pd.DataFrame) -> pd.DataFrame:
    """Derive cell_id_clean column in metadata DataFrame."""
    for col in ['cell_id', 'cell', 'filename']:
        if col in meta_df.columns:
            meta_df['cell_id_clean'] = meta_df[col].apply(_clean_cell_id_value)
            break
    return meta_df


def _extract_cell_id_from_analysis(x: object) -> str:
    """Extract cell ID from analysis DataFrame column value."""
    s = str(x)
    m = _re.search(r"CELL(\d+)[a-zA-Z]*$", s)
    if m:
        return m.group(1)
    if '_' in s:
        last = s.split('_')[-1]
        if any(c.isdigit() for c in last):
            return ''.join(c for c in last if c.isdigit())
        return last
    digits = ''.join(c for c in s if c.isdigit())
    return digits or s


def _derive_analysis_cell_id(ana_df: pd.DataFrame) -> tuple[pd.DataFrame, bool]:
    """Derive cell_id_clean column in analysis DataFrame.

    Returns:
        Tuple of (DataFrame, success). success is False if no ID column found.
    """
    id_columns = ['Label', 'Slice', 'ROI', 'Name', 'Filename', 'Title', 'Image']
    id_column = next((c for c in id_columns if c in ana_df.columns), None)
    if id_column is None:
        return ana_df, False
    ana_df['cell_id_clean'] = ana_df[id_column].apply(_extract_cell_id_from_analysis)
    return ana_df, True


def _merge_group_metadata(
    ana_df: pd.DataFrame,
    meta_df: pd.DataFrame,
    replace: bool,
) -> pd.DataFrame:
    """Merge group metadata into analysis DataFrame."""
    group_col_names = ['group_id', 'group_name', 'group_mean_auc']
    group_cols = [c for c in group_col_names if c in meta_df.columns]

    # Deduplicate metadata
    if 'cell_id_clean' in meta_df.columns and not meta_df.empty:
        meta_df = meta_df.drop_duplicates(subset=['cell_id_clean'], keep='first')

    existing_group_cols = [c for c in group_col_names if c in ana_df.columns]

    # Handle replacement of existing columns
    if existing_group_cols and replace:
        ana_df = ana_df.drop(columns=existing_group_cols)
        existing_group_cols = []

    # Merge appropriately
    if existing_group_cols and not replace:
        merged_df = _merge_new_columns_only(
            ana_df, meta_df, group_cols, existing_group_cols
        )
    else:
        merged_df = pd.merge(
            ana_df,
            meta_df[['cell_id_clean'] + group_cols],
            on='cell_id_clean',
            how='left',
        )

    # Cleanup temporary column
    if 'cell_id_clean' in merged_df.columns:
        merged_df = merged_df.drop(columns=['cell_id_clean'])

    return merged_df


def _merge_new_columns_only(
    ana_df: pd.DataFrame,
    meta_df: pd.DataFrame,
    group_cols: list[str],
    existing_cols: list[str],
) -> pd.DataFrame:
    """Merge only new columns that don't already exist."""
    new_cols = [c for c in group_cols if c not in existing_cols]
    if new_cols:
        temp = pd.merge(
            ana_df[['cell_id_clean']],
            meta_df[['cell_id_clean'] + new_cols],
            on='cell_id_clean',
            how='left',
        )
        for c in new_cols:
            ana_df[c] = temp[c]
    return ana_df.copy()


def _save_merged_results(
    merged_df: pd.DataFrame,
    analysis_file: Path,
    output_file: Optional[Path],
    out_dir: Optional[Path],
    overwrite: bool,
) -> None:
    """Save merged results to appropriate file(s)."""
    if overwrite:
        merged_df.to_csv(analysis_file, index=False)

    if output_file is not None:
        out_path = output_file
    elif out_dir is not None:
        out_path = out_dir / analysis_file.name
    else:
        out_path = analysis_file

    if str(out_path) != str(analysis_file):
        merged_df.to_csv(out_path, index=False)


def include_group_metadata(
    grouped_cells_dir: str | Path,
    analysis_dir: str | Path,
    output_dir: str | Path | None = None,
    output_file: str | Path | None = None,
    overwrite: bool = True,
    replace: bool = True,
    channels: Optional[Iterable[str]] = None,
) -> bool:
    """Include group metadata in analysis results.

    Merges cell grouping information from grouped_cells directory into
    the analysis CSV file.
    """
    grouped_dir = Path(grouped_cells_dir)
    analysis_path = Path(analysis_dir)
    out_dir = Path(output_dir) if output_dir is not None else None
    out_file = Path(output_file) if output_file is not None else None

    # Validate input directories
    if not grouped_dir.exists() or not analysis_path.exists():
        return False

    # Load metadata files
    metadata_files = _find_group_metadata_files(grouped_dir)
    metadata_files = _filter_metadata_by_channels(metadata_files, channels)
    if not metadata_files:
        return True  # No metadata is a no-op, not an error

    meta_df = _load_and_augment_metadata(metadata_files)
    if meta_df is None:
        return False

    # Load analysis file
    analysis_file = _find_analysis_file(analysis_path, out_dir)
    if analysis_file is None:
        return False

    ana_df = _read_csv_robust(analysis_file)
    if ana_df is None:
        return False

    # Derive cell IDs in both DataFrames
    meta_df = _derive_meta_cell_id(meta_df)
    ana_df, success = _derive_analysis_cell_id(ana_df)
    if not success:
        return False

    # Merge and save
    merged_df = _merge_group_metadata(ana_df, meta_df, replace)
    _save_merged_results(merged_df, analysis_file, out_file, out_dir, overwrite)

    return True


# ------------------------- Track ROIs Across Timepoints -------------------------

def _load_roi_dict(zip_file_path: str | Path):
    try:
        from read_roi import read_roi_zip  # type: ignore
    except Exception:
        return None
    try:
        return read_roi_zip(str(zip_file_path))
    except Exception:
        return None


def _load_roi_bytes(zip_file_path: str | Path):
    import zipfile
    roi_bytes: dict[str, bytes] = {}
    try:
        with zipfile.ZipFile(str(zip_file_path), 'r') as z:
            for name in z.namelist():
                key = name[:-4] if name.lower().endswith('.roi') else name
                roi_bytes[key] = z.read(name)
        return roi_bytes
    except Exception:
        return None


def _polygon_centroid(x: List[float], y: List[float]) -> Tuple[float, float]:
    area = 0.0
    cx = 0.0
    cy = 0.0
    n = len(x) - 1
    for i in range(n):
        cross = x[i] * y[i + 1] - x[i + 1] * y[i]
        area += cross
        cx += (x[i] + x[i + 1]) * cross
        cy += (y[i] + y[i + 1]) * cross
    area *= 0.5
    if abs(area) < 1e-8:
        return (float(sum(x[:-1]) / n), float(sum(y[:-1]) / n))
    cx /= (6 * area)
    cy /= (6 * area)
    return (float(cx), float(cy))


def _roi_center(roi: dict) -> Tuple[float, float]:
    if 'x' in roi and 'y' in roi:
        x = list(roi['x'])
        y = list(roi['y'])
        if x and y and (x[0] != x[-1] or y[0] != y[-1]):
            x.append(x[0])
            y.append(y[0])
        return _polygon_centroid(x, y)
    if all(k in roi for k in ['left', 'top', 'width', 'height']):
        return (float(roi['left'] + roi['width'] / 2), float(roi['top'] + roi['height'] / 2))
    if all(k in roi for k in ['left', 'top', 'right', 'bottom']):
        w = roi['right'] - roi['left']
        h = roi['bottom'] - roi['top']
        return (float(roi['left'] + w / 2), float(roi['top'] + h / 2))
    raise ValueError("Unexpected ROI format")


def _match_rois_with_distance(
    roi_list1: List[dict],
    roi_list2: List[dict],
    max_distance: Optional[float] = None
) -> Tuple[List[int], List[float]]:
    """Match ROIs between two frames with optional distance threshold.

    Returns:
        Tuple of (mapping indices, distances) where mapping[i] gives the index in roi_list2
        that matches roi_list1[i], or -1 if no match within max_distance.
    """
    try:
        from scipy.optimize import linear_sum_assignment  # type: ignore
    except Exception:
        # Fallback: simple sequential matching
        n = min(len(roi_list1), len(roi_list2))
        mapping = list(range(n))
        distances = [0.0] * n
        if len(roi_list2) > len(roi_list1):
            mapping.extend(list(range(n, len(roi_list2))))
            distances.extend([0.0] * (len(roi_list2) - n))
        return mapping, distances

    n1 = len(roi_list1)
    n2 = len(roi_list2)

    if n1 == 0 or n2 == 0:
        return [], []

    # Calculate centers
    centers1 = [_roi_center(r) for r in roi_list1]
    centers2 = [_roi_center(r) for r in roi_list2]

    # Build cost matrix
    cost = np.zeros((n1, n2), dtype=np.float64)
    for i in range(n1):
        for j in range(n2):
            dx = centers1[i][0] - centers2[j][0]
            dy = centers1[i][1] - centers2[j][1]
            distance = np.hypot(dx, dy)
            cost[i, j] = distance

    # Find optimal assignment
    row_ind, col_ind = linear_sum_assignment(cost)

    # Build mapping and filter by distance threshold
    mapping = [-1] * n1  # -1 indicates no match
    distances = [float('inf')] * n1

    for i, j in zip(row_ind, col_ind):
        distance = cost[i, j]
        if max_distance is None or distance <= max_distance:
            mapping[i] = j
            distances[i] = distance

    return mapping, distances


def _load_single_timepoint(roi_file: Path) -> Optional[dict]:
    """Load ROI data for a single timepoint file.

    Returns:
        Dict with file, roi_dict, roi_bytes, rois, names, centers, roi_count
        or None if loading fails.
    """
    roi_dict = _load_roi_dict(roi_file)
    roi_bytes = _load_roi_bytes(roi_file)

    if roi_dict is None or roi_bytes is None:
        print(f"Warning: Could not load {roi_file.name}, skipping this file")
        return None

    items = list(roi_dict.items())
    rois = [it[1] for it in items]
    names = [it[0] for it in items]
    centers = [_roi_center(r) for r in rois]

    return {
        'file': roi_file,
        'roi_dict': roi_dict,
        'roi_bytes': roi_bytes,
        'rois': rois,
        'names': names,
        'centers': centers,
        'roi_count': len(rois)
    }


def _load_all_timepoints(roi_files: List[Path]) -> list[dict]:
    """Load ROI data for all timepoint files."""
    timepoint_data = []
    for roi_file in roi_files:
        tp_data = _load_single_timepoint(roi_file)
        if tp_data is not None:
            timepoint_data.append(tp_data)
    return timepoint_data


def _initialize_tracks(first_timepoint: dict) -> list[dict]:
    """Initialize tracks from the first timepoint."""
    tracks = []
    for roi_idx in range(first_timepoint['roi_count']):
        track = {
            'track_id': roi_idx,
            'timepoint_data': [(0, roi_idx, first_timepoint['centers'][roi_idx], 0.0)],
            'complete': True
        }
        tracks.append(track)
    return tracks


def _get_active_tracks(tracks: list[dict], prev_tp_idx: int, prev_tp: dict) -> tuple:
    """Get ROIs and indices from tracks active at the previous timepoint.

    Returns:
        Tuple of (prev_rois, track_indices)
    """
    prev_rois = []
    track_indices = []
    for track_idx, track in enumerate(tracks):
        if track['timepoint_data'][-1][0] == prev_tp_idx:
            prev_roi_idx = track['timepoint_data'][-1][1]
            prev_rois.append(prev_tp['rois'][prev_roi_idx])
            track_indices.append(track_idx)
    return prev_rois, track_indices


def _update_track_with_match(
    track: dict,
    tp_idx: int,
    matched_roi_idx: int,
    centroid: tuple,
    distance: float,
    max_distance: Optional[float],
) -> None:
    """Update a track with a matched ROI."""
    track['timepoint_data'].append((tp_idx, matched_roi_idx, centroid, distance))
    if max_distance is not None and distance > max_distance:
        track['complete'] = False


def _update_tracks_with_matches(
    tracks: list[dict],
    track_indices: list[int],
    mapping: list[int],
    distances: list[float],
    curr_tp: dict,
    tp_idx: int,
    max_distance: Optional[float],
) -> None:
    """Update all tracks based on matching results."""
    for i, track_idx in enumerate(track_indices):
        matched_roi_idx = mapping[i]
        if matched_roi_idx >= 0:
            _update_track_with_match(
                tracks[track_idx],
                tp_idx,
                matched_roi_idx,
                curr_tp['centers'][matched_roi_idx],
                distances[i],
                max_distance,
            )
        else:
            tracks[track_idx]['complete'] = False


def _create_new_tracks_for_unmatched(
    tracks: list[dict], mapping: list[int], curr_tp: dict, tp_idx: int
) -> None:
    """Create new tracks for unmatched ROIs in the current frame."""
    matched_indices = set(m for m in mapping if m >= 0)
    for roi_idx in range(curr_tp['roi_count']):
        if roi_idx not in matched_indices:
            new_track = {
                'track_id': len(tracks),
                'timepoint_data': [(tp_idx, roi_idx, curr_tp['centers'][roi_idx], 0.0)],
                'complete': False  # Can't be complete if it starts mid-series
            }
            tracks.append(new_track)


def _process_timepoint(
    tracks: list[dict],
    timepoint_data: list[dict],
    tp_idx: int,
    max_distance: Optional[float],
) -> None:
    """Process a single timepoint, updating tracks with matches."""
    prev_tp = timepoint_data[tp_idx - 1]
    curr_tp = timepoint_data[tp_idx]

    prev_rois, track_indices = _get_active_tracks(tracks, tp_idx - 1, prev_tp)

    if not prev_rois or not curr_tp['rois']:
        for track_idx in track_indices:
            tracks[track_idx]['complete'] = False
        return

    mapping, distances = _match_rois_with_distance(prev_rois, curr_tp['rois'], max_distance)
    _update_tracks_with_matches(
        tracks, track_indices, mapping, distances, curr_tp, tp_idx, max_distance
    )
    _create_new_tracks_for_unmatched(tracks, mapping, curr_tp, tp_idx)


def _calculate_track_statistics(tracks: list[dict], timepoint_data: list[dict]) -> dict:
    """Calculate summary statistics for tracking results."""
    complete_count = sum(1 for t in tracks if t['complete'])
    return {
        'total_timepoints': len(timepoint_data),
        'total_tracks': len(tracks),
        'complete_tracks': complete_count,
        'incomplete_tracks': len(tracks) - complete_count,
        'roi_counts_per_timepoint': [tp['roi_count'] for tp in timepoint_data],
    }


def _build_tracks_across_timepoints(
    roi_files: List[Path],
    max_distance: Optional[float] = None
) -> dict:
    """Build cell tracks across all timepoints.

    Returns dict with:
        'tracks': List of track dicts, each containing:
            - 'track_id': unique track ID
            - 'timepoint_data': List of (timepoint_idx, roi_idx, centroid, distance_to_prev)
            - 'complete': whether track appears in all frames
        'timepoint_info': List of dicts with metadata per timepoint
        'statistics': Summary statistics
    """
    empty_result = {'tracks': [], 'timepoint_info': [], 'statistics': {}}

    if not roi_files:
        return empty_result

    timepoint_data = _load_all_timepoints(roi_files)
    if not timepoint_data:
        return empty_result

    tracks = _initialize_tracks(timepoint_data[0])

    for tp_idx in range(1, len(timepoint_data)):
        _process_timepoint(tracks, timepoint_data, tp_idx, max_distance)

    statistics = _calculate_track_statistics(tracks, timepoint_data)

    return {
        'tracks': tracks,
        'timepoint_data': timepoint_data,
        'statistics': statistics
    }


def _generate_tracking_report(
    tracking_result: dict,
    output_path: Path
) -> None:
    """Generate a detailed tracking quality report."""
    stats = tracking_result['statistics']
    tracks = tracking_result['tracks']
    timepoint_data = tracking_result['timepoint_data']

    report_lines = []
    report_lines.append("=" * 80)
    report_lines.append("ROI TRACKING REPORT")
    report_lines.append("=" * 80)
    report_lines.append("")

    # Summary statistics
    report_lines.append("SUMMARY:")
    report_lines.append(f"  Total timepoints: {stats['total_timepoints']}")
    report_lines.append(f"  ROIs per timepoint: {stats['roi_counts_per_timepoint']}")
    report_lines.append(f"  Total tracks found: {stats['total_tracks']}")
    report_lines.append(f"  Complete tracks (present in all frames): {stats['complete_tracks']}")
    report_lines.append(f"  Incomplete tracks: {stats['incomplete_tracks']}")
    report_lines.append("")
    report_lines.append("ROI REORDERING:")
    report_lines.append("  ROIs have been reordered in the output files:")
    report_lines.append(f"    - ROIs 1-{stats['complete_tracks']}: Complete tracks (same cell across all timepoints)")
    report_lines.append(f"    - ROIs {stats['complete_tracks']+1}-{stats['total_tracks']}: Incomplete tracks (partial appearances)")
    report_lines.append("  After extraction, CELL1.tif, CELL2.tif, etc. will correspond to the same")
    report_lines.append("  biological cell across timepoints (for complete tracks).")
    report_lines.append("")

    # File information
    report_lines.append("FILES:")
    for i, tp in enumerate(timepoint_data):
        report_lines.append(f"  Timepoint {i}: {tp['file'].name} ({tp['roi_count']} ROIs)")
    report_lines.append("")

    # Complete tracks details
    complete_tracks = [t for t in tracks if t['complete']]
    report_lines.append(f"COMPLETE TRACKS ({len(complete_tracks)}):")
    if complete_tracks:
        for track in complete_tracks:
            track_id = track['track_id']
            avg_dist = np.mean([d for _, _, _, d in track['timepoint_data'][1:]])
            max_dist = max([d for _, _, _, d in track['timepoint_data'][1:]]) if len(track['timepoint_data']) > 1 else 0
            report_lines.append(f"  Track {track_id}: avg_distance={avg_dist:.2f}px, max_distance={max_dist:.2f}px")
    else:
        report_lines.append("  None - all tracks are incomplete")
    report_lines.append("")

    # Incomplete tracks details
    incomplete_tracks = [t for t in tracks if not t['complete']]
    report_lines.append(f"INCOMPLETE TRACKS ({len(incomplete_tracks)}):")
    if incomplete_tracks:
        for track in incomplete_tracks[:20]:  # Show first 20
            track_id = track['track_id']
            frames = [tp_idx for tp_idx, _, _, _ in track['timepoint_data']]
            report_lines.append(f"  Track {track_id}: present in frames {frames}")
        if len(incomplete_tracks) > 20:
            report_lines.append(f"  ... and {len(incomplete_tracks) - 20} more")
    else:
        report_lines.append("  None - all tracks are complete")
    report_lines.append("")

    report_lines.append("=" * 80)

    # Write report
    report_text = "\n".join(report_lines)
    output_path.write_text(report_text)

    # Also print to console
    print("\n" + report_text)


def _save_tracked_rois(
    tracking_result: dict,
    backup_dir: Path,
    replace_originals: bool = True
) -> bool:
    """Save tracked ROI sets, replacing original files with tracked versions.

    Args:
        tracking_result: Result from _build_tracks_across_timepoints
        backup_dir: Directory to save backup of original ROI files
        replace_originals: If True, replace original ROI files with tracked versions

    Returns:
        True if at least one set was saved successfully
    """
    timepoint_data = tracking_result['timepoint_data']
    tracks = tracking_result['tracks']

    if not timepoint_data or not tracks:
        return False

    success = False

    # Separate complete and incomplete tracks
    complete_tracks = [t for t in tracks if t['complete']]
    incomplete_tracks = [t for t in tracks if not t['complete']]

    # Sort each group by track_id
    complete_tracks.sort(key=lambda t: t['track_id'])
    incomplete_tracks.sort(key=lambda t: t['track_id'])

    # Combine: complete tracks first, then incomplete tracks
    all_tracks_ordered = complete_tracks + incomplete_tracks

    if not all_tracks_ordered:
        print(f"Warning: No tracks found")
        return False

    # For each timepoint, reorder and save ROIs
    for tp_idx, tp_data in enumerate(timepoint_data):
        original_file = tp_data['file']

        # Create backup if it doesn't exist
        if replace_originals:
            backup_dir.mkdir(parents=True, exist_ok=True)
            backup_file = backup_dir / original_file.name
            if not backup_file.exists():
                import shutil
                try:
                    shutil.copy2(original_file, backup_file)
                    print(f"  Backed up: {original_file.name}")
                except Exception as e:
                    print(f"  Warning: Failed to backup {original_file.name}: {e}")

        # Find which ROIs belong to each track at this timepoint
        roi_indices_to_keep = []
        for track in all_tracks_ordered:
            # Find this track's ROI index at this timepoint (if it exists)
            for frame_idx, roi_idx, _, _ in track['timepoint_data']:
                if frame_idx == tp_idx:
                    roi_indices_to_keep.append((track['track_id'], roi_idx))
                    break
            # Note: if track doesn't exist at this timepoint, nothing is added

        # Extract ROI bytes in track order (maintaining complete tracks first)
        roi_bytes_ordered = []
        for track_id, roi_idx in roi_indices_to_keep:
            roi_name = tp_data['names'][roi_idx]
            roi_byte_data = tp_data['roi_bytes'].get(roi_name)
            if roi_byte_data:
                roi_bytes_ordered.append(roi_byte_data)

        # Save the reordered ROI set (replace original or save to new location)
        output_file = original_file if replace_originals else backup_dir / original_file.name
        if _save_zip_from_bytes(roi_bytes_ordered, output_file):
            success = True
            print(f"  Reordered: {original_file.name} ({len(roi_bytes_ordered)} ROIs)")
        else:
            print(f"  Warning: Failed to save {output_file.name}")

    # Report what was saved
    if complete_tracks:
        print(f"  → {len(complete_tracks)} complete tracks (present in all {len(timepoint_data)} timepoints)")
    if incomplete_tracks:
        print(f"  → {len(incomplete_tracks)} incomplete tracks (partial timepoints)")

    return success


def _save_zip_from_bytes(roi_bytes_list: List[bytes], output_zip_path: str | Path) -> bool:
    import zipfile
    try:
        with zipfile.ZipFile(str(output_zip_path), 'w') as z:
            for i, data in enumerate(roi_bytes_list):
                name = f"ROI_{i+1:03d}.roi"
                z.writestr(name, data)
        return True
    except Exception:
        return False


def find_roi_files_for_timepoints(directory: str | Path, timepoints: List[str]) -> dict[str, List[Path]]:
    """Find all ROI zip files for each condition/region across timepoints.

    Returns dict mapping region_key -> list of ROI files ordered by timepoint.
    """
    root = Path(directory)

    # Find all ROI files for all timepoints
    all_roi_files = {}
    for tp in timepoints:
        files = list(root.rglob(f"*{tp}*_rois.zip"))
        all_roi_files[tp] = files
        print(f"  Found {len(files)} ROI files for timepoint '{tp}'")

    if not all_roi_files:
        return {}

    # Collect all unique region keys across ALL timepoints (not just first)
    all_region_keys = set()
    for tp in timepoints:
        for roi_file in all_roi_files.get(tp, []):
            ref_path_str = str(roi_file)
            region_key = ref_path_str.replace(tp, "TIMEPOINT")
            all_region_keys.add(region_key)

    # Group by region (everything except timepoint identifier)
    region_groups = {}

    # Process each unique region key
    for region_key in sorted(all_region_keys):
        # Find corresponding files for all timepoints
        file_sequence = []
        for tp in timepoints:
            expected_path = region_key.replace("TIMEPOINT", tp)
            matching_file = None
            for candidate in all_roi_files.get(tp, []):
                if str(candidate) == expected_path:
                    matching_file = candidate
                    break
            if matching_file:
                file_sequence.append(matching_file)
            else:
                # Missing timepoint - still track what we have
                file_sequence.append(None)

        # Only include if we have files for multiple timepoints
        valid_files = [f for f in file_sequence if f is not None]
        if len(valid_files) >= 2:
            region_groups[region_key] = file_sequence

    return region_groups


def track_rois(
    input_dir: str | Path,
    timepoints: List[str],
    recursive: bool = True,
    max_distance: Optional[float] = 50.0,
    backup_subdir: str = "roi_backups"
) -> bool:
    """Track ROIs across timepoints and reorder them for consistent cell identification.

    This implements a hybrid tracking approach that:
    1. Builds tracks across all timepoints using distance-based matching
    2. Identifies complete tracks (cells present in all frames with distance ≤ threshold)
    3. Reorders ROIs within zip files so that:
       - ROIs 1-N: Complete tracks (same cell across all timepoints, distance ≤ threshold)
       - ROIs N+1-M: Incomplete tracks (missing from some frames OR distance > threshold)
    4. Replaces original ROI files with reordered versions
    5. Backs up original ROI files to roi_backups/ directory
    6. Generates a detailed tracking quality report

    After tracking, CELL1.tif will correspond to the same biological cell across
    all timepoints (for complete tracks).

    Args:
        input_dir: Directory containing ROI zip files
        timepoints: List of timepoint identifiers (e.g., ['t00', 't01', 't02', 't03'])
        recursive: Whether to search recursively (default True)
        max_distance: Maximum distance threshold for matching ROIs in pixels
                     (default 50.0). Only ROIs within this distance across
                     all timepoints are marked as complete tracks.
                     Set to None for unlimited distance (not recommended)
        backup_subdir: Name of subdirectory for backup of original ROI files

    Returns:
        True if tracking succeeded for at least one region
    """
    if not timepoints or len(timepoints) < 2:
        print("Tracking requires at least 2 timepoints")
        return True

    root = Path(input_dir)
    if not root.exists():
        print(f"Input directory does not exist: {input_dir}")
        return False

    # Find ROI file groups
    region_groups = find_roi_files_for_timepoints(input_dir, timepoints)

    if not region_groups:
        print("No matching ROI files found across timepoints")
        return True  # Not an error, just nothing to track

    print(f"\nFound {len(region_groups)} region(s) to track across {len(timepoints)} timepoints")

    # Create backup directory at the root level
    backup_base = root / backup_subdir
    backup_base.mkdir(parents=True, exist_ok=True)

    any_success = False

    # Process each region
    for region_idx, (region_key, file_sequence) in enumerate(region_groups.items(), 1):
        # Filter out None entries (missing timepoints)
        valid_files = [f for f in file_sequence if f is not None]

        if len(valid_files) < 2:
            print(f"\nRegion {region_idx}: Skipping (less than 2 valid timepoints)")
            continue

        print(f"\nRegion {region_idx}/{len(region_groups)}: Processing {len(valid_files)} timepoints")
        print(f"  Files: {[f.name for f in valid_files]}")

        # Build tracks
        tracking_result = _build_tracks_across_timepoints(valid_files, max_distance)

        if not tracking_result['tracks']:
            print(f"  No tracks built, skipping")
            continue

        # Determine backup directory path (preserve original structure)
        first_file = valid_files[0]
        # Get relative path from input_dir to first file's parent
        try:
            rel_path = first_file.parent.relative_to(root)
            backup_dir = backup_base / rel_path
        except ValueError:
            # Files not under input_dir, use flat backup
            backup_dir = backup_base

        # Generate report in same directory as ROI files
        report_path = first_file.parent / "tracking_report.txt"
        _generate_tracking_report(tracking_result, report_path)

        # Save tracked ROIs (replaces originals, backs up to backup_dir)
        if _save_tracked_rois(tracking_result, backup_dir, replace_originals=True):
            any_success = True
        else:
            print(f"  Warning: Failed to save tracked ROIs for this region")

    if any_success:
        print(f"\n✓ Tracking complete!")
        print(f"  - Original ROI files have been REPLACED with tracked versions")
        print(f"  - Original ROI files backed up to: {backup_base}")
        print(f"  - Tracking reports saved alongside ROI files")
        print(f"\nCells are now tracked: CELL1.tif will be the same cell across timepoints")

    return any_success

