from __future__ import annotations

"""Application-level helpers for pure image processing tasks.

Currently includes image binning functionality.
"""

from pathlib import Path
from typing import Iterable, Optional, Set, List, Tuple
from percell.ports.driven.image_processing_port import ImageProcessingPort
from percell.ports.driven.file_management_port import FileManagementPort
from percell.domain import FileNamingService
from percell.application.progress_api import progress_bar
import os
import shutil
import re as _re
import pandas as pd
import numpy as np

# Import metadata service for centralized metadata handling
from percell.domain.services.image_metadata_service import ImageMetadataService
from percell.domain.models import ImageMetadata


def _to_optional_set(values: Optional[Iterable[str]]) -> Optional[Set[str]]:
    if not values:
        return None
    s = set(values)
    if {"all"}.issubset(s):
        return None
    return s


# Create a global metadata service instance
_metadata_service = ImageMetadataService()

def _extract_tiff_metadata(image_path: Path) -> Optional[ImageMetadata]:
    """
    Extract TIFF metadata from an image file using centralized service.

    Args:
        image_path (Path): Path to the TIFF image file

    Returns:
        ImageMetadata or None: Extracted metadata object, or None if extraction fails
    """
    try:
        metadata = _metadata_service.extract_metadata(image_path)
        return metadata if metadata.has_resolution_info() else None
    except Exception as e:
        print(f"Error extracting metadata from {image_path.name}: {e}")
        return None


def _write_tiff_with_metadata(output_path: Path, image: np.ndarray, metadata: Optional[ImageMetadata] = None) -> bool:
    """
    Write a TIFF image with metadata preservation using centralized service.

    Args:
        output_path (Path): Path where to save the image
        image (np.ndarray): Image data to save
        metadata (ImageMetadata, optional): Metadata to preserve

    Returns:
        bool: True if successful, False otherwise
    """
    try:
        return _metadata_service.save_image_with_metadata(image, output_path, metadata)
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
    if imgproc is None:
        # Lazy import to avoid hard coupling when injected
        from percell.adapters.pil_image_processing_adapter import PILImageProcessingAdapter  # type: ignore
        imgproc = PILImageProcessingAdapter()

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

            image = imgproc.read_image(file_path)
            binned = imgproc.bin_image(image, bin_factor)
            imgproc.write_image(out_file, binned.astype(image.dtype))
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
    *,
    imgproc: Optional[ImageProcessingPort] = None,
) -> bool:
    """Combine grouped binary masks into single masks under combined_masks.

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
                # Read first to get shape/dtype and extract metadata
                try:
                    first = imgproc.read_image(files[0])
                    combined = np.zeros_like(first, dtype=np.uint8)
                    # Extract metadata from the first mask file for this group
                    print(f"Attempting to extract metadata from: {files[0].name}")
                    reference_metadata = _extract_tiff_metadata(files[0])
                    if reference_metadata:
                        print(f"Successfully extracted metadata for group {prefix}")
                    else:
                        print(f"No metadata extracted for group {prefix}")
                except Exception as e:
                    print(f"Error processing group {prefix}: {e}")
                    continue
                for f in files:
                    try:
                        img = imgproc.read_image(f)
                        combined = np.maximum(combined, img.astype(np.uint8))
                    except Exception:
                        continue
                out_path = out_condition / f"{prefix}.tif"
                try:
                    # Try to write with metadata preservation first
                    print(f"Writing combined mask: {out_path.name}")
                    if reference_metadata and reference_metadata.has_resolution_info():
                        print(f"Using metadata with resolution info")
                    else:
                        print("No metadata available for writing")
                    
                    if not _write_tiff_with_metadata(out_path, combined, reference_metadata):
                        print(f"Metadata write failed, falling back to imgproc.write_image for {out_path.name}")
                        # Fallback to original imgproc.write_image if tifffile fails
                        imgproc.write_image(out_path, combined)
                    else:
                        print(f"Successfully wrote {out_path.name} with metadata preservation")
                    any_written = True
                except Exception as e:
                    print(f"Error writing {out_path.name}: {e}")
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
    *,
    imgproc: Optional[ImageProcessingPort] = None,
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
        from percell.adapters.pil_image_processing_adapter import PILImageProcessingAdapter  # type: ignore
        imgproc = PILImageProcessingAdapter()
    any_written = False
    # Collect per-region group metadata rows as we assign cells to bins
    region_to_rows: dict[Path, list[dict[str, object]]] = {}

    # Find all cell directories first to know the total count
    region_dirs = _find_cell_dirs(cells_root)
    
    # Filter by channels if specified
    if channels:
        filtered_dirs = []
        for region_dir in region_dirs:
            if any(ch in str(region_dir) for ch in channels):
                filtered_dirs.append(region_dir)
        region_dirs = filtered_dirs if filtered_dirs else region_dirs

    # Count total cells for progress info
    total_cells = 0
    for region_dir in region_dirs:
        cell_files = list(region_dir.glob("CELL*.tif"))
        total_cells += len(cell_files)

    
    # Use alive_progress bar with manual mode for unknown total progress
    regions_count = len(region_dirs)
    title = f"Grouping {total_cells} cells into {bins} bins across {regions_count} regions"
    
    # Use progress_bar which will use the configured alive_progress settings
    with progress_bar(total=regions_count, title=title, manual=False) as update:
        for region_dir in region_dirs:
            condition = region_dir.parent.name
            out_condition = out_root / condition / region_dir.name
            out_condition.mkdir(parents=True, exist_ok=True)

            # Gather images and simple intensity metric
            cell_files = list(region_dir.glob("CELL*.tif"))
            if not cell_files:
                continue
            images: list[tuple[Path, np.ndarray, float]] = []
            reference_metadata = None  # Store metadata from first image for this region
            
            for f in cell_files:
                try:
                    img = imgproc.read_image(f)
                    metric = float(np.mean(img))
                    images.append((f, img, metric))
                    
                    # Extract metadata from the first image we successfully read
                    if reference_metadata is None:
                        reference_metadata = _extract_tiff_metadata(f)
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
                # Record metadata rows for cells in this group/bin
                rows = region_to_rows.setdefault(out_condition, [])
                group_metrics = [metric for _, __, metric in group]
                group_mean = float(np.mean(group_metrics)) if group_metrics else 0.0
                for path_obj, __, ___ in group:
                    rows.append({
                        'cell_id': path_obj.name,
                        'group_id': i + 1,
                        'group_name': f"bin_{i+1}",
                        'group_mean_auc': group_mean,
                    })
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

                    # Ensure clean image data without any ROI information
                    # The grouped images should be pure intensity data for thresholding
                    print(f"Saving grouped image: {out_path.name} (shape: {out_img.shape}, dtype: {out_img.dtype})")

                    # Try to write with metadata preservation first
                    if not _write_tiff_with_metadata(out_path, out_img, reference_metadata):
                        # Fallback to original imgproc.write_image if tifffile fails
                        imgproc.write_image(out_path, out_img)
                    any_written = True
                except Exception:
                    continue

            # After processing this region, write group metadata CSV if we collected rows
            rows = region_to_rows.get(out_condition)
            if rows:
                try:
                    import pandas as _pd
                    csv_path = out_condition / f"{region_dir.name}_cell_groups.csv"
                    _pd.DataFrame(rows).to_csv(csv_path, index=False)
                except Exception:
                    pass
            
            # Update progress after processing each region
            update(1)

    return any_written


# ------------------------- Duplicate ROIs for Channels -------------------------

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
        from percell.adapters.local_filesystem_adapter import LocalFileSystemAdapter  # type: ignore
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
                fs.copy(rf, dst, overwrite=True)  # type: ignore[call-arg]
                successful += 1
                channels_processed.add(target)
            except Exception:
                continue

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
        if dish_file.exists() and not dish_file.name.startswith('._'):
            return dish_file
    for pattern in ["*combined*.csv", "*combined_analysis.csv", "combined_results.csv"]:
        matches = [f for f in analysis_dir.glob(pattern) if not f.name.startswith('._')]
        if matches:
            matches.sort(key=lambda f: f.stat().st_size, reverse=True)
            return matches[0]
    csvs = [f for f in analysis_dir.glob("*.csv") if not f.name.startswith('._')]
    if csvs:
        csvs.sort(key=lambda f: f.stat().st_size, reverse=True)
        return csvs[0]
    return None


def include_group_metadata(
    grouped_cells_dir: str | Path,
    analysis_dir: str | Path,
    output_dir: str | Path | None = None,
    output_file: str | Path | None = None,
    overwrite: bool = True,
    replace: bool = True,
    channels: Optional[Iterable[str]] = None,
) -> bool:
    grouped_dir = Path(grouped_cells_dir)
    analysis_path = Path(analysis_dir)
    out_dir = Path(output_dir) if output_dir is not None else None

    metadata_files = _find_group_metadata_files(grouped_dir)
    if channels:
        mf: list[Path] = []
        for p in metadata_files:
            if any(ch in str(p) for ch in channels):
                mf.append(p)
        # If filtering removed all files, fall back to unfiltered list
        if mf:
            metadata_files = mf
    if not metadata_files:
        # No metadata available; treat as no-op so pipeline can continue
        return True

    # Load and augment metadata
    frames: list[pd.DataFrame] = []
    for p in metadata_files:
        df = _read_csv_robust(p)
        if df is None:
            continue
        parent = p.parent
        region = parent.name
        condition = parent.parent.name if parent.parent.name != "grouped_cells" else ""
        df = df.copy()
        df['region'] = region
        if condition:
            df['condition'] = condition
        frames.append(df)
    if not frames:
        # Nothing to merge; treat as no-op
        return True
    meta_df = pd.concat(frames, ignore_index=True)

    # Find analysis file
    analysis_file = _find_analysis_file(analysis_path, out_dir)
    if analysis_file is None:
        # No analysis to merge into; treat as no-op
        return True

    # Load analysis
    ana_df = _read_csv_robust(analysis_file)
    if ana_df is None:
        # Cannot read analysis; treat as no-op
        return True

    # Derive cell_id_clean in both frames
    # Derive a canonical id for metadata frame
    if 'cell_id' in meta_df.columns:
        meta_df['cell_id_clean'] = meta_df['cell_id'].apply(
            lambda x: str(x).replace('CELL', '').replace('.tif', '').strip() if isinstance(x, str) else str(x)
        )
    elif 'cell' in meta_df.columns:
        meta_df['cell_id_clean'] = meta_df['cell'].apply(lambda x: str(x).replace('CELL', '').replace('.tif', '').strip())
    elif 'filename' in meta_df.columns:
        meta_df['cell_id_clean'] = meta_df['filename'].apply(lambda x: str(x).replace('CELL', '').replace('.tif', '').strip())
    id_column = next((c for c in ['Label', 'Slice', 'ROI', 'Name', 'Filename', 'Title', 'Image'] if c in ana_df.columns), None)
    if id_column is None:
        # No compatible id column; treat as no-op
        return True
    def _extract_cell_id(x: object) -> str:
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
    ana_df['cell_id_clean'] = ana_df[id_column].apply(_extract_cell_id)

    # Choose group columns
    group_cols = [c for c in ['group_id', 'group_name', 'group_mean_auc'] if c in meta_df.columns]
    # Drop duplicate cell ids in meta
    if 'cell_id_clean' in meta_df.columns and not meta_df.empty:
        meta_df = meta_df.drop_duplicates(subset=['cell_id_clean'], keep='first')

    existing_group_cols = [c for c in ['group_id', 'group_name', 'group_mean_auc'] if c in ana_df.columns]
    if existing_group_cols and replace:
        ana_df = ana_df.drop(columns=existing_group_cols)
        existing_group_cols = []

    if existing_group_cols and not replace:
        new_cols = [c for c in group_cols if c not in existing_group_cols]
        if new_cols:
            temp = pd.merge(
                ana_df[['cell_id_clean']],
                meta_df[['cell_id_clean'] + new_cols],
                on='cell_id_clean',
                how='left',
            )
            for c in new_cols:
                ana_df[c] = temp[c]
        merged_df = ana_df.copy()
    else:
        merged_df = pd.merge(
            ana_df,
            meta_df[['cell_id_clean'] + group_cols],
            on='cell_id_clean',
            how='left',
        )

    # Basic duplicate cleanup
    for col in ['cell_id_clean']:
        if col in merged_df.columns:
            merged_df = merged_df.drop(columns=[col])

    # Save
    if overwrite:
        merged_df.to_csv(analysis_file, index=False)
    if output_file is not None:
        out_path = Path(output_file)
    elif out_dir is not None:
        out_path = Path(out_dir) / analysis_file.name
    else:
        out_path = analysis_file
    if str(out_path) != str(analysis_file):
        merged_df.to_csv(out_path, index=False)
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


def _match_rois(roi_list1: List[dict], roi_list2: List[dict]) -> List[int]:
    try:
        from scipy.optimize import linear_sum_assignment  # type: ignore
    except Exception:
        n = min(len(roi_list1), len(roi_list2))
        indices = list(range(n))
        if len(roi_list2) > len(roi_list1):
            indices.extend(list(range(n, len(roi_list2))))
        return indices

    n1 = len(roi_list1)
    n2 = len(roi_list2)
    n = min(n1, n2)
    roi_subset1 = roi_list1[:n]
    roi_subset2 = roi_list2[:n]
    centers1 = [_roi_center(r) for r in roi_subset1]
    centers2 = [_roi_center(r) for r in roi_subset2]
    cost = np.zeros((n, n), dtype=np.float64)
    for i in range(n):
        for j in range(n):
            dx = centers1[i][0] - centers2[j][0]
            dy = centers1[i][1] - centers2[j][1]
            cost[i, j] = np.hypot(dx, dy)
    row_ind, col_ind = linear_sum_assignment(cost)
    mapping = list(col_ind)
    if n2 > n1:
        mapping.extend(list(range(n, n2)))
    return mapping


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


def process_roi_pair(zip_file1: str | Path, zip_file2: str | Path) -> bool:
    roi_dict1 = _load_roi_dict(zip_file1)
    roi_dict2 = _load_roi_dict(zip_file2)
    if roi_dict1 is None or roi_dict2 is None:
        return False
    roi_bytes2 = _load_roi_bytes(zip_file2)
    if roi_bytes2 is None:
        return False
    items1 = list(roi_dict1.items())
    items2 = list(roi_dict2.items())
    rois1 = [it[1] for it in items1]
    rois2 = [it[1] for it in items2]
    names2 = [it[0] for it in items2]
    if not rois1 or not rois2:
        return False
    indices = _match_rois(rois1, rois2)
    reordered: List[bytes] = []
    for idx in indices:
        if 0 <= idx < len(names2):
            key = names2[idx]
            data = roi_bytes2.get(key)
            if data is not None:
                reordered.append(data)
    zip_file2_path = Path(zip_file2)
    backup = zip_file2_path.with_suffix(zip_file2_path.suffix + ".bak")
    try:
        if not backup.exists():
            zip_file2_path.replace(backup)
    except Exception:
        return False
    return _save_zip_from_bytes(reordered, zip_file2_path)


def find_roi_pairs(directory: str | Path, t0: str, t1: str) -> List[Tuple[Path, Path]]:
    root = Path(directory)
    t0_files = list(root.rglob(f"*{t0}*_rois.zip"))
    t1_files = {str(p): p for p in root.rglob(f"*{t1}*_rois.zip")}
    pairs: List[Tuple[Path, Path]] = []
    for f0 in t0_files:
        f0s = str(f0)
        if t0 not in f0s:
            continue
        expected = f0s.replace(t0, t1)
        match = t1_files.get(expected)
        if match is not None:
            pairs.append((f0, match))
    return pairs


def track_rois(input_dir: str | Path, timepoints: List[str], recursive: bool = True) -> bool:
    if not timepoints or len(timepoints) < 2:
        return True
    t0, t1 = timepoints[0], timepoints[1]
    pairs = find_roi_pairs(input_dir, t0, t1)
    if not pairs:
        return True
    ok_any = False
    for a, b in pairs:
        if process_roi_pair(a, b):
            ok_any = True
    return ok_any or True

