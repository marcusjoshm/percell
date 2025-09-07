"""Data selection and channel configuration logic.

Pure domain logic for scanning datasets and validating selections.
"""

from __future__ import annotations

from pathlib import Path
from typing import Tuple

from ..models import DatasetSelection


class DataSelectionService:
    """Encapsulates dataset discovery and selection rules."""

    def scan_available_data(self, root: Path) -> list[Path]:
        """Scan a root directory for candidate data files.

        Args:
            root: Root directory containing raw microscopy data.

        Returns:
            List of discovered file paths.
        """

        raise NotImplementedError

    def parse_conditions_timepoints_regions(self, files: list[Path]) -> Tuple[list[str], list[str], list[str]]:
        """Parse condition/timepoint/region identifiers from file paths.

        Args:
            files: List of file paths to analyze.

        Returns:
            Tuple of (conditions, timepoints, regions).
        """

        raise NotImplementedError

    def validate_user_selections(self, selection: DatasetSelection) -> bool:
        """Validate that a user's selection is consistent with available data.

        Args:
            selection: Structured selection including filters.

        Returns:
            True if the selection is valid, otherwise False.
        """

        raise NotImplementedError

    def generate_file_lists(self, selection: DatasetSelection) -> list[Path]:
        """Generate concrete file lists based on a selection.

        Args:
            selection: Filters and root directory.

        Returns:
            Concrete file paths to process.
        """

        raise NotImplementedError


