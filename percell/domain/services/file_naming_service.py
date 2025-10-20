"""File naming and parsing business rules.

Provides pure logic for parsing microscopy filenames and generating output
names according to PerCell conventions.
"""

from __future__ import annotations

import os
import re
from typing import Dict

from ..models import FileMetadata


class FileNamingService:
    """Encapsulates file naming conventions and parsing logic.

    Methods raise NotImplementedError and will be implemented during
    extraction in later steps.
    """

    def parse_microscopy_filename(self, filename: str) -> FileMetadata:
        """Parse a microscopy filename to extract metadata.

        Now handles multiple naming conventions:
        - Standard: "region_s1_t0_ch1_z5.tif"
        - Leica-style: "18h dTAG13_Merged_z00_ch00.tif"
        - Simple: "MyExperiment_ch00.tif"

        Args:
            filename: Filename to parse.

        Returns:
            FileMetadata: Parsed metadata.
        """

        # Accept .tif/.tiff only
        _, ext = os.path.splitext(filename)
        if ext.lower() not in {".tif", ".tiff"}:
            raise ValueError(f"Unsupported extension: {ext}")

        base = filename[: -len(ext)] if ext else filename

        # Enhanced patterns - more flexible matching
        # Match with or without underscore/space prefix, case insensitive
        token_patterns = {
            "tile": r"[_\s]?s(\d+)",
            "z_index": r"[_\s]?z(\d+)",
            "channel": r"[_\s]?ch(\d+)",
            "timepoint": r"[_\s]?t(\d+)",
        }

        # Extract tokens without caring about order; record spans to remove
        spans = []
        values: Dict[str, object] = {}
        for key, pat in token_patterns.items():
            m = re.search(pat, base, re.IGNORECASE)
            if m:
                # Record the full match span (including optional prefix)
                spans.append((m.start(), m.end()))
                val = m.group(1)
                if key == "z_index":
                    values[key] = int(val)
                elif key in ("channel", "timepoint"):
                    prefix = "ch" if key == "channel" else "t"
                    values[key] = f"{prefix}{val}"
                # tile is not persisted in FileMetadata

        # Remove found token substrings to get dataset/image name
        # Sort in reverse order to remove from end to start
        # (preserves earlier indices)
        spans.sort(reverse=True)
        dataset = base
        for s, e in spans:
            dataset = dataset[:s] + dataset[e:]

        # Clean up the dataset name
        dataset = dataset.strip("_").strip()

        # If dataset is empty, use the original base name
        if not dataset:
            dataset = base

        return FileMetadata(
            original_name=filename,
            dataset=dataset,
            channel=values.get("channel"),
            timepoint=values.get("timepoint"),
            z_index=values.get("z_index"),
            extension=ext,
        )

    def generate_output_filename(self, metadata: FileMetadata) -> str:
        """Generate a standardized output filename from metadata.

        Args:
            metadata: Structured metadata describing the file.

        Returns:
            Standardized filename string.
        """

        parts: list[str] = []
        if metadata.dataset:
            parts.append(metadata.dataset)
        if metadata.channel:
            parts.append(metadata.channel)
        if metadata.timepoint:
            parts.append(metadata.timepoint)
        name = "_".join(parts) if parts else (metadata.original_name or "output")
        ext = metadata.extension or ".tif"
        return f"{name}{ext}"

    def validate_naming_convention(self, filename: str) -> bool:
        """Validate that a filename adheres to expected conventions.

        Args:
            filename: Filename to validate.

        Returns:
            True if the name is valid, otherwise False.
        """

        # Must be tif/tiff
        _, ext = os.path.splitext(filename)
        if ext.lower() not in {".tif", ".tiff"}:
            return False
        # Require both channel and timepoint tokens
        has_ch = bool(re.search(r"_ch\d+", filename)) or bool(re.search(r"ch\d+", filename))
        has_t = bool(re.search(r"_t\d+", filename)) or bool(re.search(r"t\d+", filename))
        # Dataset presence approximated by some prefix before tokens
        base = filename[: -len(ext)] if ext else filename
        return bool(has_ch and has_t and len(base.split("_")) >= 3)

    def extract_metadata_from_name(self, filename: str) -> Dict[str, str]:
        """Extract raw metadata tokens from a filename.

        Args:
            filename: Filename to analyze.

        Returns:
            Mapping of metadata keys to string values.
        """

        # Handle ROI zip names like ROIs_<dataset>_chNN_tXX_rois.zip
        name = filename
        if name.startswith("ROIs_"):
            name = name[5:]
        name = re.sub(r"_rois\.zip$", "", name)
        name = re.sub(r"\.zip$", "", name)

        ch = None
        t = None
        # Match channel with underscore before and either underscore or end-of-string after
        m_ch = re.search(r"_(ch\d+)(?:_|$)", name)
        if m_ch:
            ch = m_ch.group(1)
        # Match timepoint with underscore before and either underscore or end-of-string after
        m_t = re.search(r"_(t\d+)(?:_|$)", name)
        if m_t:
            t = m_t.group(1)

        dataset = name
        if ch:
            dataset = dataset.replace(f"_{ch}", "")
        if t:
            dataset = dataset.replace(f"_{t}", "")
        dataset = dataset.rstrip("_")

        out: Dict[str, str] = {}
        if dataset:
            out["dataset"] = dataset
        if ch:
            out["channel"] = ch
        if t:
            out["timepoint"] = t
        return out


