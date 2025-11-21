from __future__ import annotations

"""Application helpers for ImageJ-driven tasks (macro creation and execution).

This module centralizes common ImageJ workflow operations previously embedded
in standalone module scripts, making them reusable by application stages.
"""

from pathlib import Path
from typing import Optional, List, Tuple
import re
import tempfile
import subprocess

from typing import Optional, List, Tuple
from percell.ports.driven.file_management_port import FileManagementPort
from percell.ports.driven.imagej_integration_port import ImageJIntegrationPort
from percell.domain.utils.filesystem_filters import is_system_hidden_file


def _normalize_path_for_imagej(p: str | Path) -> str:
    return str(p).replace("\\", "/")


def create_macro_with_parameters(
    macro_template_file: str | Path,
    input_dir: str | Path,
    output_dir: str | Path,
    channel: str,
    auto_close: bool = False,
) -> Optional[Path]:
    """Create a temporary macro file embedding parameters for execution.

    Returns the path to the temporary macro file or None on failure.
    """
    try:
        template_path = Path(macro_template_file)
        template_content = template_path.read_text()

        # Filter out ImageJ parameter annotations as we embed values directly
        lines = [ln for ln in template_content.split("\n") if not ln.strip().startswith("#@")]

        in_dir = _normalize_path_for_imagej(input_dir)
        out_dir = _normalize_path_for_imagej(output_dir)

        params = (
            "// Parameters embedded from application helper\n"
            f"input_dir = \"{in_dir}\";\n"
            f"output_dir = \"{out_dir}\";\n"
            f"channel = \"{channel}\";\n"
            f"auto_close = {str(bool(auto_close)).lower()};\n"
        )

        content = params + "\n" + "\n".join(lines)

        temp_file = tempfile.NamedTemporaryFile(mode="w", suffix=".ijm", delete=False)
        try:
            temp_path = Path(temp_file.name)
            temp_file.write(content)
        finally:
            temp_file.close()
        return temp_path
    except Exception:
        return None


def validate_resize_inputs(
    input_dir: str | Path,
    output_dir: str | Path,
    channel: str,
    *,
    fs: Optional[FileManagementPort] = None,
) -> bool:
    try:
        in_dir = Path(input_dir)
        if not in_dir.exists():
            return False
        # Simple content check; avoid heavy scans
        if not any(in_dir.iterdir()):
            return False
        if not str(channel).startswith("ch"):
            return False
        try:
            if fs is not None:
                fs.ensure_dir(Path(output_dir))
            else:
                Path(output_dir).mkdir(parents=True, exist_ok=True)
        except Exception:
            return False
        return True
    except Exception:
        return False


def run_imagej_macro(
    imagej_path: str | Path,
    macro_file: str | Path,
    auto_close: bool = False,
    *,
    imagej: Optional[ImageJIntegrationPort] = None,
) -> bool:
    import logging
    logger = logging.getLogger(__name__)

    try:
        if imagej is None:
            # Lazy import to avoid hard coupling when injected
            from percell.adapters.imagej_macro_adapter import ImageJMacroAdapter  # type: ignore
            imagej = ImageJMacroAdapter(Path(imagej_path))
        logger.debug(f"Running ImageJ macro: {macro_file}")
        rc = imagej.run_macro(Path(macro_file), [])
        logger.debug(f"ImageJ macro return code: {rc}")
        return rc == 0
    except Exception as e:
        logger.error(f"Exception running ImageJ macro: {e}")
        return False


def run_imagej_macro_interactive(imagej_path: str | Path, macro_file: str | Path) -> bool:
    """Run ImageJ in interactive mode using -macro so that UI-based macros execute.

    Returns True on zero exit code.
    """
    try:
        cmd = [str(imagej_path), "-macro", str(macro_file)]
        completed = subprocess.run(cmd)
        return completed.returncode == 0
    except Exception:
        return False


def resize_rois(
    input_dir: str | Path,
    output_dir: str | Path,
    imagej_path: str | Path,
    channel: str,
    macro_path: str | Path,
    auto_close: bool = True,
    *,
    imagej: Optional[ImageJIntegrationPort] = None,
    fs: Optional[FileManagementPort] = None,
) -> bool:
    if not validate_resize_inputs(input_dir, output_dir, channel, fs=fs):
        return False

    temp_macro: Optional[Path] = create_macro_with_parameters(
        macro_template_file=macro_path,
        input_dir=input_dir,
        output_dir=output_dir,
        channel=channel,
        auto_close=auto_close,
    )
    if not temp_macro:
        return False

    try:
        ok = run_imagej_macro(imagej_path, temp_macro, auto_close, imagej=imagej)
        return ok
    finally:
        try:
            Path(temp_macro).unlink(missing_ok=True)
        except Exception:
            pass


def create_measure_macro_with_parameters(
    macro_template_file: str | Path,
    roi_file: str | Path,
    image_file: str | Path,
    csv_file: str | Path,
    auto_close: bool = False,
) -> Optional[Path]:
    """Create a temporary macro for ROI-area measurement embedding parameters."""
    try:
        template_path = Path(macro_template_file)
        template_content = template_path.read_text()

        roi_clean = _normalize_path_for_imagej(roi_file)
        img_clean = _normalize_path_for_imagej(image_file)
        csv_clean = _normalize_path_for_imagej(csv_file)
        auto_str = str(bool(auto_close)).lower()

        # Replace parameter declaration markers with assignments
        content = (
            template_content
            .replace('#@ String roi_file', f'roi_file = "{roi_clean}";')
            .replace('#@ String image_file', f'image_file = "{img_clean}";')
            .replace('#@ String csv_file', f'csv_file = "{csv_clean}";')
            .replace('#@ Boolean auto_close', f'auto_close = {auto_str};')
        )

        temp_file = tempfile.NamedTemporaryFile(mode="w", suffix=".ijm", delete=False)
        try:
            temp_path = Path(temp_file.name)
            temp_file.write(content)
        finally:
            temp_file.close()
        return temp_path
    except Exception:
        return None


def find_roi_image_pairs(input_dir: str | Path, output_dir: str | Path) -> List[Tuple[str, str, str]]:
    """Discover (roi_zip, image_path, csv_output_path) tuples for measurement."""
    pairs: List[Tuple[str, str, str]] = []
    try:
        input_path = Path(input_dir)
        output_path = Path(output_dir)

        roi_files = list(output_path.glob("ROIs/**/*.zip"))
        # Filter out system metadata files (e.g., ._ files on exFAT)
        roi_files = [rf for rf in roi_files if not is_system_hidden_file(rf)]
        filtered: List[Path] = []
        for rf in roi_files:
            name = rf.name
            if name.endswith("_rois.zip"):
                filtered.append(rf)
        roi_files = filtered

        for roi_file in roi_files:
            roi_name = roi_file.name
            if roi_name.startswith("ROIs_") and roi_name.endswith("_rois.zip"):
                base_name = roi_name[5:-9]
            elif roi_name.endswith("_rois.zip"):
                base_name = roi_name[:-9]
            elif roi_name.endswith(".zip"):
                base_name = roi_name[:-4]
            else:
                continue

            found_match = False
            for ext in [".tif", ".tiff", ".png", ".jpg"]:
                patterns = [
                    f"**/{base_name}{ext}",
                    f"**/*{base_name}*{ext}",
                ]
                for pattern in patterns:
                    for img in input_path.glob(pattern):
                        condition_name = roi_file.parent.name
                        roi_stem = roi_file.stem
                        roi_dir_name = roi_stem[5:] if roi_stem.startswith("ROIs_") else roi_stem
                        if roi_dir_name.endswith("_rois"):
                            roi_dir_name = roi_dir_name[:-5]
                        csv_filename = f"{condition_name}_{roi_dir_name}_cell_area.csv"
                        csv_path = output_path / "analysis" / csv_filename
                        csv_path.parent.mkdir(parents=True, exist_ok=True)
                        pairs.append((str(roi_file), str(img), str(csv_path)))
                        found_match = True
                        break
                    if found_match:
                        break
                if found_match:
                    break
        return pairs
    except Exception:
        return pairs


def measure_roi_areas(
    input_dir: str | Path,
    output_dir: str | Path,
    imagej_path: str | Path,
    macro_path: str | Path,
    auto_close: bool = True,
    *,
    imagej: Optional[ImageJIntegrationPort] = None,
) -> bool:
    try:
        pairs = find_roi_image_pairs(input_dir, output_dir)
        if not pairs:
            return True
        ok_any = False
        for roi_zip, img_path, csv_path in pairs:
            macro_file = create_measure_macro_with_parameters(
                macro_template_file=macro_path,
                roi_file=roi_zip,
                image_file=img_path,
                csv_file=csv_path,
                auto_close=auto_close,
            )
            if not macro_file:
                continue
            try:
                if run_imagej_macro(imagej_path, macro_file, auto_close, imagej=imagej):
                    if Path(csv_path).exists():
                        ok_any = True
                else:
                    break
            finally:
                try:
                    Path(macro_file).unlink(missing_ok=True)
                except Exception:
                    pass
        return ok_any or not pairs
    except Exception:
        return False


# ------------------------- Analyze Cell Masks -------------------------

def create_analyze_macro_with_parameters(
    macro_template_file: str | Path,
    mask_paths: List[str | Path],
    csv_file: str | Path,
    auto_close: bool = False,
) -> Optional[Path]:
    try:
        template = Path(macro_template_file).read_text()
        lines = [ln for ln in template.split("\n") if not ln.strip().startswith("#@")]
        norm_masks = [ _normalize_path_for_imagej(p) for p in mask_paths ]
        masks_list = ";".join(norm_masks)
        csv_clean = _normalize_path_for_imagej(csv_file)
        params = (
            "// Parameters embedded from application helper\n"
            f"mask_files_list = \"{masks_list}\";\n"
            f"csv_file = \"{csv_clean}\";\n"
            f"auto_close = {str(bool(auto_close)).lower()};\n"
        )
        content = params + "\n" + "\n".join(lines)
        tmp = tempfile.NamedTemporaryFile(mode="w", suffix=".ijm", delete=False)
        try:
            tmp_path = Path(tmp.name)
            tmp.write(content)
        finally:
            tmp.close()
        return tmp_path
    except Exception:
        return None

def find_mask_files(
    input_dir: str | Path,
    regions: Optional[List[str]] = None,
    timepoints: Optional[List[str]] = None,
    max_files: int = 9999999999999,
) -> dict[str, List[str]]:
    import os, re, glob
    mask_files_by_dir: dict[str, List[str]] = {}
    target_regions: List[str] = []
    target_timepoints: List[str] = []
    total_files_collected = 0
    if regions:
        for r in regions:
            if isinstance(r, str) and " " in r:
                target_regions.extend([s.strip() for s in r.split()])
            else:
                target_regions.append(r)
    if timepoints:
        for t in timepoints:
            if isinstance(t, str) and " " in t:
                target_timepoints.extend([s.strip() for s in t.split()])
            else:
                target_timepoints.append(t)
    for extension in ["tif", "tiff"]:
        if total_files_collected >= max_files:
            break
        pattern = os.path.join(str(input_dir), "**", f"MASK_CELL*.{extension}")
        for mask_path in glob.glob(pattern, recursive=True):
            parent_dir = os.path.dirname(mask_path)
            dir_name = os.path.basename(parent_dir)
            region = None
            timepoint = None
            m = re.match(r"(R_\d+)_(t\d+)", dir_name)
            if m:
                region = m.group(1)
                timepoint = m.group(2)
            elif "_" in dir_name:
                m2 = re.match(r"(.+?)_(t\d+)$", dir_name)
                if m2:
                    region = m2.group(1)
                    timepoint = m2.group(2)
            if region is None or timepoint is None:
                tp = re.search(r"(t\d+)", dir_name)
                if tp:
                    timepoint = tp.group(1)
                    left = dir_name.split(timepoint)[0].strip("_")
                    region = left or None
            if region is None or timepoint is None:
                continue
            if target_regions:
                if not any(region in tr or tr in region for tr in target_regions):
                    continue
            if target_timepoints and timepoint not in target_timepoints:
                continue
            
            # Check if we've reached the maximum number of files
            if total_files_collected >= max_files:
                break
                
            files = mask_files_by_dir.setdefault(parent_dir, [])
            files.append(mask_path)
            total_files_collected += 1
    return mask_files_by_dir


def _analysis_csv_filename(dir_path: str | Path, output_dir: str | Path) -> Path:
    d = Path(dir_path)
    condition = d.parent.name
    mask_dir = d.name
    return Path(output_dir) / f"{condition}_{mask_dir}_particle_analysis.csv"

def analyze_masks(
    input_dir: str | Path,
    output_dir: str | Path,
    imagej_path: str | Path,
    macro_path: str | Path,
    regions: Optional[List[str]] = None,
    timepoints: Optional[List[str]] = None,
    max_files: int = 9999999999999,
    auto_close: bool = True,
    *,
    imagej: Optional[ImageJIntegrationPort] = None,
) -> bool:
    import logging
    logger = logging.getLogger(__name__)

    logger.info(f"analyze_masks called with: input_dir={input_dir}, regions={regions}, timepoints={timepoints}")

    groups = find_mask_files(input_dir, max_files=max_files, regions=regions, timepoints=timepoints)
    logger.info(f"find_mask_files returned {len(groups)} groups with {sum(len(v) for v in groups.values())} total masks")

    if not groups:
        logger.error("No groups found by find_mask_files")
        return False

    any_ok = False
    group_num = 0
    for dir_path, mask_paths in groups.items():
        group_num += 1
        logger.info(f"Processing group {group_num}/{len(groups)}: {Path(dir_path).name} ({len(mask_paths)} masks)")

        csv_file = _analysis_csv_filename(dir_path, output_dir)
        logger.info(f"  CSV output: {csv_file}")
        csv_file.parent.mkdir(parents=True, exist_ok=True)

        macro_file = create_analyze_macro_with_parameters(macro_path, mask_paths, csv_file, auto_close)
        if not macro_file:
            logger.error(f"  Failed to create macro file for group {group_num}")
            continue

        logger.info(f"  Created macro file: {macro_file}")
        logger.info(f"  Running ImageJ macro...")

        try:
            if run_imagej_macro(imagej_path, macro_file, auto_close, imagej=imagej):
                logger.info(f"  ImageJ macro succeeded for group {group_num}")
                any_ok = True
            else:
                logger.error(f"  ImageJ macro failed for group {group_num} - stopping early")
                # early stop if ImageJ failing consistently
                break
        finally:
            try:
                Path(macro_file).unlink(missing_ok=True)
            except Exception:
                pass

    logger.info(f"analyze_masks completed: any_ok={any_ok}")
    return any_ok


# ------------------------- Create Cell Masks -------------------------

def _extract_tokens_from_roi_name(filename: str) -> dict[str, str]:
    from percell.domain import FileNamingService
    svc = FileNamingService()
    tokens = svc.extract_metadata_from_name(filename)
    return tokens


def _find_matching_mask_for_roi(roi_file: Path, mask_dir: Path) -> Optional[Path]:
    condition = roi_file.parent.name
    condition_mask_dir = mask_dir / condition
    if not condition_mask_dir.exists():
        return None
    tokens = _extract_tokens_from_roi_name(roi_file.name)
    region = tokens.get("region", "")
    channel = tokens.get("channel", "")
    timepoint = tokens.get("timepoint", "")
    patterns = [
        f"MASK_{region}_{channel}_{timepoint}.tif",
        f"MASK_{region}_{channel}_{timepoint}.tiff",
        f"MASK_{region}_{channel}_*.tif",
        f"MASK_*{channel}*.tif",
    ]
    for pat in patterns:
        matches = list(condition_mask_dir.glob(pat))
        if matches:
            return matches[0]
    return None


def _create_output_dir_for_roi(roi_file: Path, output_base_dir: Path) -> Path:
    condition = roi_file.parent.name
    tokens = _extract_tokens_from_roi_name(roi_file.name)
    region = tokens.get("region", "")
    channel = tokens.get("channel", "")
    timepoint = tokens.get("timepoint", "")
    out_dir = output_base_dir / condition / f"{region}_{channel}_{timepoint}"
    out_dir.mkdir(parents=True, exist_ok=True)
    return out_dir


def create_masks_macro_with_parameters(
    macro_template_file: str | Path,
    roi_file: str | Path,
    mask_file: str | Path,
    output_dir: str | Path,
    auto_close: bool = True,
) -> Optional[Path]:
    try:
        template = Path(macro_template_file).read_text()
        lines = [ln for ln in template.split("\n") if not ln.strip().startswith("#@")]
        roi_clean = _normalize_path_for_imagej(roi_file)
        mask_clean = _normalize_path_for_imagej(mask_file)
        out_clean = _normalize_path_for_imagej(output_dir)
        params = (
            "// Parameters embedded from application helper\n"
            f"roi_file = \"{roi_clean}\";\n"
            f"mask_file = \"{mask_clean}\";\n"
            f"output_dir = \"{out_clean}\";\n"
            f"auto_close = {str(bool(auto_close)).lower()};\n"
        )
        content = params + "\n" + "\n".join(lines)
        tmp = tempfile.NamedTemporaryFile(mode="w", suffix=".ijm", delete=False)
        try:
            tmp_path = Path(tmp.name)
            tmp.write(content)
        finally:
            tmp.close()
        return tmp_path
    except Exception:
        return None


def create_cell_masks(
    roi_dir: str | Path,
    mask_dir: str | Path,
    output_dir: str | Path,
    imagej_path: str | Path,
    macro_path: str | Path,
    channels: Optional[List[str]] = None,
    auto_close: bool = True,
    *,
    imagej: Optional[ImageJIntegrationPort] = None,
) -> bool:
    roi_root = Path(roi_dir)
    mask_root = Path(mask_dir)
    out_root = Path(output_dir)
    out_root.mkdir(parents=True, exist_ok=True)

    # Collect ROI zips grouped by condition
    roi_files: List[Path] = []
    for condition_dir in roi_root.glob("*"):
        if condition_dir.is_dir() and not is_system_hidden_file(condition_dir):
            # Filter out system metadata files (e.g., ._ files on exFAT)
            zip_files = [zf for zf in condition_dir.glob("*.zip") if not is_system_hidden_file(zf)]
            roi_files.extend(zip_files)

    if channels:
        filtered: List[Path] = []
        for rf in roi_files:
            name = rf.name
            # Expect pattern contains _chNN_
            m = re.search(r"_(ch\d+)_", name)
            if m and m.group(1) in channels:
                filtered.append(rf)
        roi_files = filtered

    any_success = False
    for roi_file in roi_files:
        mask_file = _find_matching_mask_for_roi(roi_file, mask_root)
        if not mask_file:
            continue
        out_dir = _create_output_dir_for_roi(roi_file, out_root)
        macro_file = create_masks_macro_with_parameters(
            macro_template_file=macro_path,
            roi_file=roi_file,
            mask_file=mask_file,
            output_dir=out_dir,
            auto_close=auto_close,
        )
        if not macro_file:
            continue
        try:
            if run_imagej_macro(imagej_path, macro_file, auto_close, imagej=imagej):
                # consider success if any MASK_CELL files exist
                if list(out_dir.glob("MASK_CELL*.tif")) or list(out_dir.glob("MASK_CELL*.tiff")):
                    any_success = True
        finally:
            try:
                Path(macro_file).unlink(missing_ok=True)
            except Exception:
                pass

    return any_success


# ------------------------- Extract Cells -------------------------

def _find_raw_image_for_roi(roi_file: Path, raw_data_dir: Path) -> Optional[Path]:
    import logging
    logger = logging.getLogger(__name__)

    condition = roi_file.parent.name
    condition_dir = raw_data_dir / condition

    logger.info(f"[DEBUG] _find_raw_image_for_roi called for ROI: {roi_file.name}")
    logger.info(f"[DEBUG] Condition: {condition}")
    logger.info(f"[DEBUG] Condition directory: {condition_dir}")
    logger.info(f"[DEBUG] Condition directory exists: {condition_dir.exists()}")

    if not condition_dir.exists():
        logger.error(f"[DEBUG] Condition directory does not exist: {condition_dir}")
        return None

    tokens = _extract_tokens_from_roi_name(roi_file.name)
    region = tokens.get("region", "")
    channel = tokens.get("channel", "")
    timepoint = tokens.get("timepoint", "")

    logger.info(f"[DEBUG] Extracted tokens - region: '{region}', channel: '{channel}', timepoint: '{timepoint}'")

    # Try multiple pattern variations to match raw data files
    patterns = [
        f"{region}_{timepoint}_{channel}.tif",  # Most common: Region_t00_ch00.tif
        f"{region}_{channel}_{timepoint}.tif",  # Alternative: Region_ch00_t00.tif
    ]

    logger.info(f"[DEBUG] Trying patterns: {patterns}")

    for pattern in patterns:
        search_pattern = f"**/{pattern}"
        logger.info(f"[DEBUG] Searching with pattern: {search_pattern}")
        matches = list(condition_dir.glob(search_pattern))
        logger.info(f"[DEBUG] Found {len(matches)} matches for pattern '{pattern}'")
        if matches:
            logger.info(f"[DEBUG] Matched file: {matches[0]}")
            return matches[0]

    # Fallback: broader search for partial matches
    logger.info(f"[DEBUG] No exact matches, trying fallback partial matching")
    # Filter out system metadata files (e.g., ._ files on exFAT)
    all_tifs = [tf for tf in condition_dir.glob("**/*.tif") if not is_system_hidden_file(tf)]
    logger.info(f"[DEBUG] Found {len(all_tifs)} total TIF files in condition directory")

    for file in all_tifs:
        name = file.name
        ok_region = region in name
        ok_channel = channel in name if channel else True
        ok_time = timepoint in name if timepoint else True
        logger.info(f"[DEBUG] Checking file: {name} - region:{ok_region}, channel:{ok_channel}, time:{ok_time}")
        if ok_region and ok_channel and ok_time:
            logger.info(f"[DEBUG] Partial match found: {file}")
            return file

    logger.error(f"[DEBUG] No matching raw image found for ROI: {roi_file.name}")
    return None


def _create_cells_output_dir_for_roi(roi_file: Path, output_base_dir: Path) -> Path:
    condition = roi_file.parent.name
    tokens = _extract_tokens_from_roi_name(roi_file.name)
    region = tokens.get("region", "")
    channel = tokens.get("channel", "")
    timepoint = tokens.get("timepoint", "")
    out_dir = output_base_dir / condition / f"{region}_{channel}_{timepoint}"
    out_dir.mkdir(parents=True, exist_ok=True)
    return out_dir


def create_extract_macro_with_parameters(
    macro_template_file: str | Path,
    roi_file: str | Path,
    image_file: str | Path,
    output_dir: str | Path,
    auto_close: bool = True,
) -> Optional[Path]:
    try:
        template = Path(macro_template_file).read_text()
        lines = [ln for ln in template.split("\n") if not ln.strip().startswith("#@")]
        roi_clean = _normalize_path_for_imagej(roi_file)
        img_clean = _normalize_path_for_imagej(image_file)
        out_clean = _normalize_path_for_imagej(output_dir)
        params = (
            "// Parameters embedded from application helper\n"
            f"roi_file = \"{roi_clean}\";\n"
            f"image_file = \"{img_clean}\";\n"
            f"output_dir = \"{out_clean}\";\n"
            f"auto_close = {str(bool(auto_close)).lower()};\n"
        )
        content = params + "\n" + "\n".join(lines)
        tmp = tempfile.NamedTemporaryFile(mode="w", suffix=".ijm", delete=False)
        try:
            tmp_path = Path(tmp.name)
            tmp.write(content)
        finally:
            tmp.close()
        return tmp_path
    except Exception:
        return None


def extract_cells(
    roi_dir: str | Path,
    raw_data_dir: str | Path,
    output_dir: str | Path,
    imagej_path: str | Path,
    macro_path: str | Path,
    regions: Optional[List[str]] = None,
    timepoints: Optional[List[str]] = None,
    conditions: Optional[List[str]] = None,
    channels: Optional[List[str]] = None,
    auto_close: bool = True,
    *,
    imagej: Optional[ImageJIntegrationPort] = None,
) -> bool:
    import logging
    logger = logging.getLogger(__name__)

    logger.info(f"[DEBUG] extract_cells called with:")
    logger.info(f"[DEBUG]   roi_dir: {roi_dir}")
    logger.info(f"[DEBUG]   raw_data_dir: {raw_data_dir}")
    logger.info(f"[DEBUG]   output_dir: {output_dir}")
    logger.info(f"[DEBUG]   regions: {regions}")
    logger.info(f"[DEBUG]   timepoints: {timepoints}")
    logger.info(f"[DEBUG]   conditions: {conditions}")
    logger.info(f"[DEBUG]   channels: {channels}")

    roi_root = Path(roi_dir)
    raw_root = Path(raw_data_dir)
    out_root = Path(output_dir)
    out_root.mkdir(parents=True, exist_ok=True)

    logger.info(f"[DEBUG] ROI root exists: {roi_root.exists()}")
    logger.info(f"[DEBUG] Raw data root exists: {raw_root.exists()}")

    # Gather ROI zips under all conditions
    roi_files: List[Path] = []
    for condition_dir in roi_root.glob("*"):
        if condition_dir.is_dir() and not is_system_hidden_file(condition_dir):
            # Filter out system metadata files (e.g., ._ files on exFAT)
            zips = [zf for zf in condition_dir.glob("*.zip") if not is_system_hidden_file(zf)]
            logger.info(f"[DEBUG] Found {len(zips)} ZIP files in condition: {condition_dir.name}")
            roi_files.extend(zips)

    logger.info(f"[DEBUG] Total ROI files found before filtering: {len(roi_files)}")
    for rf in roi_files[:5]:  # Show first 5
        logger.info(f"[DEBUG]   - {rf.name}")

    # Filter by conditions/regions/timepoints/channels as needed
    if conditions:
        before = len(roi_files)
        roi_files = [rf for rf in roi_files if rf.parent.name in conditions]
        logger.info(f"[DEBUG] After conditions filter: {before} -> {len(roi_files)}")
    if regions:
        before = len(roi_files)
        roi_files = [rf for rf in roi_files if any(r in rf.name for r in regions)]
        logger.info(f"[DEBUG] After regions filter: {before} -> {len(roi_files)}")
    if timepoints:
        before = len(roi_files)
        roi_files = [rf for rf in roi_files if any(t in rf.name for t in timepoints)]
        logger.info(f"[DEBUG] After timepoints filter: {before} -> {len(roi_files)}")
    if channels:
        before = len(roi_files)
        roi_files = [rf for rf in roi_files if any(ch in rf.name for ch in channels)]
        logger.info(f"[DEBUG] After channels filter: {before} -> {len(roi_files)}")

    logger.info(f"[DEBUG] Total ROI files after all filters: {len(roi_files)}")

    if not roi_files:
        logger.error(f"[DEBUG] No ROI files found after filtering! Returning False.")
        return False

    any_success = False
    processed_count = 0
    skipped_count = 0

    for roi_file in roi_files:
        logger.info(f"[DEBUG] Processing ROI file {processed_count + 1}/{len(roi_files)}: {roi_file.name}")
        img_file = _find_raw_image_for_roi(roi_file, raw_root)
        if not img_file:
            logger.warning(f"[DEBUG] No matching raw image found for {roi_file.name}, skipping")
            skipped_count += 1
            continue

        logger.info(f"[DEBUG] Found matching raw image: {img_file}")
        out_dir = _create_cells_output_dir_for_roi(roi_file, out_root)
        logger.info(f"[DEBUG] Output directory: {out_dir}")

        macro_file = create_extract_macro_with_parameters(
            macro_template_file=macro_path,
            roi_file=roi_file,
            image_file=img_file,
            output_dir=out_dir,
            auto_close=auto_close,
        )
        if not macro_file:
            logger.error(f"[DEBUG] Failed to create macro file for {roi_file.name}")
            skipped_count += 1
            continue

        logger.info(f"[DEBUG] Created macro file: {macro_file}")

        try:
            logger.info(f"[DEBUG] Running ImageJ macro...")
            if run_imagej_macro(imagej_path, macro_file, auto_close, imagej=imagej):
                cells = list(out_dir.glob("CELL*.tif"))
                logger.info(f"[DEBUG] ImageJ macro completed. Found {len(cells)} extracted cell files")
                if cells:
                    any_success = True
                    processed_count += 1
                else:
                    logger.warning(f"[DEBUG] No CELL*.tif files created")
                    skipped_count += 1
            else:
                logger.error(f"[DEBUG] ImageJ macro execution failed")
                skipped_count += 1
        finally:
            try:
                Path(macro_file).unlink(missing_ok=True)
            except Exception:
                pass

    logger.info(f"[DEBUG] extract_cells summary: processed={processed_count}, skipped={skipped_count}, any_success={any_success}")
    return any_success


# ------------------------- Threshold Grouped Cells -------------------------

def create_threshold_macro_with_parameters(
    macro_template_file: str | Path,
    input_dir: str | Path,
    output_dir: str | Path,
    channels: Optional[List[str]] = None,
    auto_close: bool = True,
) -> Optional[Tuple[Path, Path]]:
    try:
        template = Path(macro_template_file).read_text()
        lines = [ln for ln in template.split("\n") if not ln.strip().startswith("#@")]
        in_clean = _normalize_path_for_imagej(input_dir).rstrip('/')
        out_clean = _normalize_path_for_imagej(output_dir).rstrip('/')
        flag_file = Path(output_dir) / "NEED_MORE_BINS.flag"
        flag_clean = _normalize_path_for_imagej(flag_file)

        # Insert channel filter logic
        channel_logic = ""
        if channels:
            conds = [f'indexOf(regionName, "{ch}") >= 0' for ch in channels]
            channel_logic = (
                "        // Check channel filter\n"
                "        channelMatch = false;\n"
                f"        if ({' || '.join(conds)}) {{ channelMatch = true; }}\n"
                "        if (!channelMatch) { continue; }\n"
            )

        params = (
            "// Parameters embedded from application helper\n"
            f"input_dir = \"{in_clean}\";\n"
            f"output_dir = \"{out_clean}\";\n"
            f"flag_file = \"{flag_clean}\";\n"
            f"auto_close = {str(bool(auto_close)).lower()};\n"
        )
        content = params + "\n" + "\n".join(lines)
        content = content.replace('        // CHANNEL_FILTER_PLACEHOLDER', channel_logic)
        tmp = tempfile.NamedTemporaryFile(mode="w", suffix=".ijm", delete=False)
        try:
            tmp_path = Path(tmp.name)
            tmp.write(content)
        finally:
            tmp.close()
        return tmp_path, flag_file
    except Exception:
        return None


def threshold_grouped_cells(
    input_dir: str | Path,
    output_dir: str | Path,
    imagej_path: str | Path,
    macro_path: str | Path,
    channels: Optional[List[str]] = None,
    auto_close: bool = True,
    *,
    imagej: Optional[ImageJIntegrationPort] = None,
) -> bool:
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    macro_flag = create_threshold_macro_with_parameters(
        macro_template_file=macro_path,
        input_dir=input_dir,
        output_dir=output_dir,
        channels=channels,
        auto_close=auto_close,
    )
    if not macro_flag:
        return False
    macro_file, flag_file = macro_flag
    try:
        # Run interactively so the user can adjust thresholds
        ok = run_imagej_macro_interactive(imagej_path, macro_file)
        # remove flag if present; we don't currently signal upstream
        try:
            Path(flag_file).unlink(missing_ok=True)
        except Exception:
            pass
        return ok
    finally:
        try:
            Path(macro_file).unlink(missing_ok=True)
        except Exception:
            pass


