from __future__ import annotations

"""Application helpers for ImageJ-driven tasks (macro creation and execution).

This module centralizes common ImageJ workflow operations previously embedded
in standalone module scripts, making them reusable by application stages.
"""

from pathlib import Path
from typing import Optional, List, Tuple
import re
import tempfile

from percell.adapters.local_filesystem_adapter import LocalFileSystemAdapter
from percell.adapters.imagej_macro_adapter import ImageJMacroAdapter


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


def validate_resize_inputs(input_dir: str | Path, output_dir: str | Path, channel: str) -> bool:
    try:
        in_dir = Path(input_dir)
        if not in_dir.exists():
            return False
        # Simple content check; avoid heavy scans
        if not any(in_dir.iterdir()):
            return False
        if not str(channel).startswith("ch"):
            return False
        LocalFileSystemAdapter().ensure_dir(Path(output_dir))
        return True
    except Exception:
        return False


def run_imagej_macro(imagej_path: str | Path, macro_file: str | Path, auto_close: bool = False) -> bool:
    try:
        adapter = ImageJMacroAdapter(Path(imagej_path))
        rc = adapter.run_macro(Path(macro_file), [])
        return rc == 0
    except Exception:
        return False


def resize_rois(
    input_dir: str | Path,
    output_dir: str | Path,
    imagej_path: str | Path,
    channel: str,
    macro_path: str | Path,
    auto_close: bool = True,
) -> bool:
    if not validate_resize_inputs(input_dir, output_dir, channel):
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
        ok = run_imagej_macro(imagej_path, temp_macro, auto_close)
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
                if run_imagej_macro(imagej_path, macro_file, auto_close):
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
    max_files: int = 50,
    regions: Optional[List[str]] = None,
    timepoints: Optional[List[str]] = None,
) -> dict[str, List[str]]:
    import os, re, glob
    mask_files_by_dir: dict[str, List[str]] = {}
    target_regions: List[str] = []
    target_timepoints: List[str] = []
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
            files = mask_files_by_dir.setdefault(parent_dir, [])
            if len(files) < max_files:
                files.append(mask_path)
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
    max_files: int = 50,
    auto_close: bool = True,
) -> bool:
    groups = find_mask_files(input_dir, max_files=max_files, regions=regions, timepoints=timepoints)
    if not groups:
        return False
    any_ok = False
    for dir_path, mask_paths in groups.items():
        csv_file = _analysis_csv_filename(dir_path, output_dir)
        csv_file.parent.mkdir(parents=True, exist_ok=True)
        macro_file = create_analyze_macro_with_parameters(macro_path, mask_paths, csv_file, auto_close)
        if not macro_file:
            continue
        try:
            if run_imagej_macro(imagej_path, macro_file, auto_close):
                any_ok = True
            else:
                # early stop if ImageJ failing consistently
                break
        finally:
            try:
                Path(macro_file).unlink(missing_ok=True)
            except Exception:
                pass
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
) -> bool:
    roi_root = Path(roi_dir)
    mask_root = Path(mask_dir)
    out_root = Path(output_dir)
    out_root.mkdir(parents=True, exist_ok=True)

    # Collect ROI zips grouped by condition
    roi_files: List[Path] = []
    for condition_dir in roi_root.glob("*"):
        if condition_dir.is_dir() and not condition_dir.name.startswith('.'):
            roi_files.extend(condition_dir.glob("*.zip"))

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
            if run_imagej_macro(imagej_path, macro_file, auto_close):
                # consider success if any MASK_CELL files exist
                if list(out_dir.glob("MASK_CELL*.tif")) or list(out_dir.glob("MASK_CELL*.tiff")):
                    any_success = True
        finally:
            try:
                Path(macro_file).unlink(missing_ok=True)
            except Exception:
                pass

    return any_success


