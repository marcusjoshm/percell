from __future__ import annotations

from pathlib import Path
from typing import Iterable, List, Optional, Sequence, Set
import re

import numpy as np
from skimage import io
from skimage.transform import downscale_local_mean
import tifffile

from percell.domain.ports import ProgressReporter


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

        all_files: List[Path] = list(input_path.glob("**/*.tif"))
        if not all_files:
            # Early exit: nothing to process
            return 0

        # Convert selection lists to sets; treat None, [] or ["all"] as no filter
        selected_conditions: Optional[Set[str]] = _normalize_selection(conditions)
        selected_regions: Optional[Set[str]] = _normalize_selection(regions)
        selected_timepoints: Optional[Set[str]] = _normalize_selection(timepoints)
        selected_channels: Optional[Set[str]] = _normalize_selection(channels)

        processed = 0

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
                current_condition = relative_path.parts[0] if len(relative_path.parts) > 0 else None
                if not current_condition:
                    continue
                if selected_conditions is not None and current_condition not in selected_conditions:
                    continue

                # Parse metadata from filename
                filename = file_path.name
                region = _parse_region(filename)
                timepoint = _match_one(r"(t\d+)", filename)
                channel = _match_one(r"(ch\d+)", filename)

                if selected_regions is not None and (not region or region not in selected_regions):
                    continue
                if selected_timepoints is not None and (not timepoint or timepoint not in selected_timepoints):
                    continue
                if selected_channels is not None and (not channel or channel not in selected_channels):
                    continue

                # Compute output path, preserving structure
                out_file = output_path / relative_path.parent / f"bin{bin_factor}x{bin_factor}_" + filename
                out_file.parent.mkdir(parents=True, exist_ok=True)

                # Read, bin, write
                image = io.imread(file_path)
                binned = downscale_local_mean(image, (bin_factor, bin_factor))
                tifffile.imwrite(out_file, binned.astype(image.dtype))
                processed += 1

                if self._progress:
                    try:
                        self._progress.advance(1)
                    except Exception:
                        pass
            except Exception:
                # Skip problematic files; errors should be logged by the caller if needed
                continue

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


