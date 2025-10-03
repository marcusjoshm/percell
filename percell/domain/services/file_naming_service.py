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

        Args:
            filename: Filename to parse.

        Returns:
            FileMetadata: Parsed metadata.
        """

        # Accept .tif/.tiff only
        _, ext = os.path.splitext(filename)
        if ext.lower() not in {".tif", ".tiff"}:
            raise NotImplementedError

        base = filename[: -len(ext)] if ext else filename

        # Patterns for tokens
        token_patterns = {
            "tile": r"_s(\d+)",
            "z_index": r"_z(\d+)",
            "channel": r"_ch(\d+)",
            "timepoint": r"_t(\d+)",
        }

        # Extract tokens without caring about order; record spans to remove
        spans = []
        values: Dict[str, object] = {}
        for key, pat in token_patterns.items():
            m = re.search(pat, base, re.IGNORECASE)
            if m:
                spans.append((m.start(), m.end()))
                val = m.group(1)
                if key == "z_index":
                    values[key] = int(val)
                elif key in ("channel", "timepoint"):
                    prefix = "ch" if key == "channel" else "t"
                    values[key] = f"{prefix}{val}"
                else:
                    # tile is not currently persisted in FileMetadata; we only strip it
                    pass

        # Remove found token substrings to get region/image name
        spans.sort(reverse=True)
        region = base
        for s, e in spans:
            region = region[:s] + region[e:]
        region = region.rstrip("_")

        return FileMetadata(
            original_name=filename,
            region=region or base,
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
        if metadata.region:
            parts.append(metadata.region)
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
        # Region presence approximated by some prefix before tokens
        base = filename[: -len(ext)] if ext else filename
        return bool(has_ch and has_t and len(base.split("_")) >= 3)

    def extract_metadata_from_name(self, filename: str) -> Dict[str, str]:
        """Extract raw metadata tokens from a filename.

        Args:
            filename: Filename to analyze.

        Returns:
            Mapping of metadata keys to string values.
        """

        # Handle ROI zip names like ROIs_<region>_chNN_tXX_rois.zip
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

        region = name
        if ch:
            region = region.replace(f"_{ch}", "")
        if t:
            region = region.replace(f"_{t}", "")
        region = region.rstrip("_")

        out: Dict[str, str] = {}
        if region:
            out["region"] = region
        if ch:
            out["channel"] = ch
        if t:
            out["timepoint"] = t
        return out


