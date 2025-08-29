from __future__ import annotations

from pathlib import Path
from typing import Iterable, List, Optional, Sequence, Set
import re

import numpy as np
from skimage import io
from skimage.transform import downscale_local_mean
import tifffile

from percell.domain.ports import ProgressReporter
import logging


logger = logging.getLogger(__name__)


class ImageBinningService:
    """Domain service that performs image binning with filtering.

    This service encapsulates the logic previously implemented in
    percell.modules.bin_images.
    """

    def __init__(self, progress_reporter: Optional[ProgressReporter] = None) -> None:
        self._progress = progress_reporter

    def bin_images(
        self,
        input_dir: str,
        output_dir: str,
        *,
        bin_factor: int = 4,
        conditions: Optional[Sequence[str]] = None,
        regions: Optional[Sequence[str]] = None,
        timepoints: Optional[Sequence[str]] = None,
        channels: Optional[Sequence[str]] = None,
    ) -> int:
        input_path = Path(input_dir)
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        # Find TIFF images (both .tif and .tiff, case-insensitive)
        patterns = ["**/*.tif", "**/*.tiff", "**/*.TIF", "**/*.TIFF"]
        seen: Set[Path] = set()
        all_files: List[Path] = []
        for pat in patterns:
            for p in input_path.glob(pat):
                if p not in seen:
                    seen.add(p)
                    all_files.append(p)
        logger.info(f"[Binning] Input dir: {input_path} | Found files: {len(all_files)}")
        if not all_files:
            # Early exit: nothing to process
            return 0

        # Convert selection lists to sets; treat None, [] or ["all"] as no filter
        selected_conditions: Optional[Set[str]] = _normalize_selection(conditions)
        selected_regions: Optional[Set[str]] = _normalize_selection(regions)
        selected_timepoints: Optional[Set[str]] = _normalize_selection(timepoints)
        selected_channels: Optional[Set[str]] = _normalize_selection(channels)
        # Use exact channel tokens from Data Selection (e.g., 'ch01')
        normalized_channel_filters: Optional[Set[str]] = selected_channels
        logger.info(
            "[Binning] Filters -> conditions=%s regions=%s timepoints=%s channels=%s",
            selected_conditions, selected_regions, selected_timepoints, normalized_channel_filters,
        )

        processed = 0
        skipped_cond = skipped_region = skipped_time = skipped_chan = 0

        if self._progress:
            try:
                self._progress.start(title="Binning images")
            except Exception:
                pass

        for file_path in all_files:
            try:
                file_path = Path(file_path)
                # Determine condition (top-level directory)
                relative_path = file_path.relative_to(input_path)
                current_condition = relative_path.parts[0] if len(relative_path.parts) > 1 else None
                # Apply condition filter only when requested
                if selected_conditions is not None and (not current_condition or current_condition not in selected_conditions):
                    skipped_cond += 1
                    continue

                # Parse metadata from filename
                filename = file_path.name
                region = _parse_region(filename)
                timepoint = _match_one(r"(t\d+)", filename)
                # Extract channel exactly as 'chXX' (matches data selection)
                channel = _match_one(r"(ch\d+)", filename)

                if selected_regions is not None and (not region or region not in selected_regions):
                    skipped_region += 1
                    continue
                if selected_timepoints is not None and (not timepoint or timepoint not in selected_timepoints):
                    skipped_time += 1
                    continue
                if normalized_channel_filters is not None and (not channel or channel not in normalized_channel_filters):
                    logger.info(
                        "[Binning] Skip by channel | file=%s parsed=%s filters=%s",
                        filename, channel, normalized_channel_filters,
                    )
                    skipped_chan += 1
                    continue
                logger.info(
                    "[Binning] Accept file: %s | cond=%s region=%s time=%s channel=%s",
                    filename, current_condition, region, timepoint, channel,
                )

                # Compute output path, preserving structure
                out_file = output_path / relative_path.parent / (f"bin{bin_factor}x{bin_factor}_" + filename)
                logger.info("[Binning] Output path: %s", out_file)
                out_file.parent.mkdir(parents=True, exist_ok=True)

                # Read, bin, write
                image = io.imread(file_path)
                logger.info("[Binning] Read image: shape=%s dtype=%s", getattr(image, 'shape', None), getattr(image, 'dtype', None))
                binned = downscale_local_mean(image, (bin_factor, bin_factor))
                out_array = binned.astype(image.dtype, copy=False)
                tifffile.imwrite(out_file, out_array)
                logger.info("[Binning] Wrote: %s", out_file)
                processed += 1

                if self._progress:
                    try:
                        self._progress.advance(1)
                    except Exception:
                        pass
            except Exception as e:
                logger.exception("[Binning] Error processing %s: %s", file_path, e)
                continue

        logger.info(
            "[Binning] Summary -> processed=%d, skipped: cond=%d region=%d timepoint=%d channel=%d",
            processed, skipped_cond, skipped_region, skipped_time, skipped_chan,
        )

        if self._progress:
            try:
                self._progress.stop()
            except Exception:
                pass

        return processed


def _is_all(items: Optional[Sequence[str]]) -> bool:
    return bool(items) and set(items) == {"all"}


def _match_one(pattern: str, text: str) -> Optional[str]:
    m = re.search(pattern, text)
    return m.group(1) if m else None


def _parse_region(filename: str) -> Optional[str]:
    region_pattern = r"(.+?)_(ch\d+)_(t\d+)"
    m = re.search(region_pattern, filename)
    if m:
        return m.group(1)
    parts = filename.split("_")
    ch_index = -1
    for i, part in enumerate(parts):
        if part.startswith("ch"):
            ch_index = i
            break
    if ch_index > 0:
        return "_".join(parts[:ch_index])
    return None


__all__ = ["ImageBinningService"]


def _normalize_selection(items: Optional[Sequence[str]]) -> Optional[Set[str]]:
    if items is None or len(items) == 0 or _is_all(items):
        return None
    return set(items)


def _norm_channel_text(text: str) -> str:
    t = text.lower()
    # unify common separators
    t = t.replace("-", "_")
    # normalize tokens like ch01 -> ch1, channel01 -> ch1, c01 -> ch1
    t = re.sub(r"channel[_-]?(\d+)", r"ch\1", t)
    t = re.sub(r"\bc(\d+)\b", r"ch\1", t)
    t = re.sub(r"ch0+(\d)", r"ch\1", t)
    return t


def _normalize_channel_strings(chs: Optional[Set[str]]) -> Optional[Set[str]]:
    if not chs:
        return None
    norm: Set[str] = set()
    for c in chs:
        if not c:
            continue
        s = _norm_channel_text(c)
        # keep only token portion (e.g., extract 'ch1')
        m = re.search(r"ch\d+", s)
        if m:
            norm.add(m.group(0))
        else:
            norm.add(s)
    return norm or None


