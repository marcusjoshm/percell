"""Data selection and channel configuration logic.

Pure domain logic for scanning datasets and validating selections.
"""

from __future__ import annotations

from pathlib import Path
from typing import Tuple
import os
from .file_naming_service import FileNamingService

from ..models import DatasetSelection


class DataSelectionService:
    """Encapsulates dataset discovery and selection rules."""

    def __init__(self) -> None:
        self._naming = FileNamingService()

    def scan_available_data(self, root: Path) -> list[Path]:
        """Scan a root directory for candidate data files.

        Args:
            root: Root directory containing raw microscopy data.

        Returns:
            List of discovered file paths.
        """
        if not root.exists() or not root.is_dir():
            return []
        files: list[Path] = []
        for p in root.rglob("*.tif"):
            if p.is_file():
                files.append(p)
        for p in root.rglob("*.tiff"):
            if p.is_file():
                files.append(p)
        return files

    def parse_conditions_timepoints_regions(self, files: list[Path]) -> Tuple[list[str], list[str], list[str]]:
        """Parse condition/timepoint/region identifiers from file paths.

        Args:
            files: List of file paths to analyze.

        Returns:
            Tuple of (conditions, timepoints, regions).
        """
        conditions: set[str] = set()
        timepoints: set[str] = set()
        regions: set[str] = set()
        for f in files:
            try:
                # Condition from path's first component under root is not available here;
                # derive from immediate parent as a reasonable heuristic.
                if f.parent and f.parent.name:
                    conditions.add(f.parent.name)
                meta = self._naming.parse_microscopy_filename(f.name)
                if meta.timepoint:
                    timepoints.add(meta.timepoint)
                if meta.region:
                    regions.add(meta.region)
            except Exception:
                continue
        return sorted(conditions), sorted(timepoints), sorted(regions)

    def validate_user_selections(self, selection: DatasetSelection) -> bool:
        """Validate that a user's selection is consistent with available data.

        Args:
            selection: Structured selection including filters.

        Returns:
            True if the selection is valid, otherwise False.
        """
        # Basic validation: paths exist and selected filters are present in discovered sets
        if not selection.root.exists() or not selection.root.is_dir():
            return False
        files = self.scan_available_data(selection.root)
        return self.validate_user_selections_from_files(selection, files)

    def validate_user_selections_from_files(self, selection: DatasetSelection, files: list[Path]) -> bool:
        """Validate selections using a provided file list (no filesystem scanning)."""
        if not files:
            return False
        conditions, timepoints, regions = self.parse_conditions_timepoints_regions(files)
        if selection.conditions and not set(selection.conditions).issubset(set(conditions)):
            return False
        if selection.timepoints and not set(selection.timepoints).issubset(set(timepoints)):
            return False
        if selection.regions and not set(selection.regions).issubset(set(regions)):
            return False
        if selection.channels:
            # Validate channels by checking at least one file contains each channel
            found_channels: set[str] = set()
            for f in files:
                try:
                    meta = self._naming.parse_microscopy_filename(f.name)
                    if meta.channel:
                        found_channels.add(meta.channel)
                except Exception:
                    continue
            if not set(selection.channels).issubset(found_channels):
                return False
        return True

    def generate_file_lists(self, selection: DatasetSelection) -> list[Path]:
        """Generate concrete file lists based on a selection.

        Args:
            selection: Filters and root directory.

        Returns:
            Concrete file paths to process.
        """
        files = self.scan_available_data(selection.root)
        return self.generate_file_lists_from_files(selection, files)

    def generate_file_lists_from_files(self, selection: DatasetSelection, files: list[Path]) -> list[Path]:
        """Generate file list from provided files (no filesystem scanning)."""
        result: list[Path] = []
        for f in files:
            try:
                # Condition filter
                condition_ok = True
                if selection.conditions:
                    condition_ok = f.parent.name in set(selection.conditions)
                if not condition_ok:
                    continue
                meta = self._naming.parse_microscopy_filename(f.name)
                # Region filter
                if selection.regions and (not meta.region or meta.region not in selection.regions):
                    continue
                # Timepoint filter
                if selection.timepoints and (not meta.timepoint or meta.timepoint not in selection.timepoints):
                    continue
                # Channel filter
                if selection.channels and (not meta.channel or meta.channel not in selection.channels):
                    continue
                result.append(f)
            except Exception:
                continue
        return result


