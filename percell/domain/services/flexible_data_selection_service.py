"""Flexible data selection service that works with any directory structure.

This service discovers files and metadata without assuming specific directory
organization. The only requirement is that the first directory level under root
contains project folders.
"""

from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Set, Tuple

from percell.domain.services.file_naming_service import FileNamingService
from percell.domain.models import FileMetadata, DatasetSelection


class FlexibleDataSelectionService:
    """Data selection that adapts to any directory structure."""

    def __init__(self) -> None:
        self._naming = FileNamingService()

    def discover_all_files(
        self, root: Path
    ) -> List[Tuple[Path, FileMetadata]]:
        """Discover all microscopy files and parse their metadata.

        Recursively scans for .tif/.tiff files and extracts metadata from
        filenames. Also captures path-based information.

        Args:
            root: Root directory to scan

        Returns:
            List of (filepath, metadata) tuples
        """
        results = []

        if not root.exists() or not root.is_dir():
            return results

        # Recursively find all TIF files
        for pattern in ["**/*.tif", "**/*.tiff"]:
            for file_path in root.glob(pattern):
                if not file_path.is_file():
                    continue

                try:
                    # Parse filename metadata
                    meta = self._naming.parse_microscopy_filename(
                        file_path.name
                    )

                    # Add path-based metadata
                    meta.full_path = file_path
                    meta.project_folder = self._extract_project_folder(
                        file_path, root
                    )
                    meta.relative_path = str(file_path.relative_to(root))

                    results.append((file_path, meta))

                except Exception as e:
                    # Log but don't fail on unparseable files
                    print(
                        f"Warning: Could not parse {file_path.name}: {e}"
                    )
                    continue

        return results

    def _extract_project_folder(
        self, file_path: Path, root: Path
    ) -> str:
        """Extract the project folder (first directory level under root).

        Args:
            file_path: Full path to file
            root: Root directory

        Returns:
            Name of project folder, or "root" if file is directly in root
        """
        try:
            relative = file_path.relative_to(root)
            if len(relative.parts) > 1:
                return relative.parts[0]
            return "root"
        except ValueError:
            return "unknown"

    def get_available_dimensions(
        self, files_meta: List[Tuple[Path, FileMetadata]]
    ) -> Dict[str, List[str]]:
        """Extract all available dimensions from discovered files.

        Dimensions are any metadata that can be used for grouping or
        filtering:
        - project_folder: First directory under root
        - dataset: Base filename (e.g., "18h dTAG13_Merged")
        - channel: Channel identifier (e.g., "ch00")
        - timepoint: Timepoint identifier (e.g., "t0")
        - z_index: Z-slice index (e.g., "0", "1", "2")

        Args:
            files_meta: List of (filepath, metadata) tuples

        Returns:
            Dict mapping dimension names to sorted lists of unique values
        """
        dimensions: Dict[str, Set[str]] = {
            "project_folder": set(),
            "dataset": set(),
            "channel": set(),
            "timepoint": set(),
            "z_index": set(),
        }

        for file_path, meta in files_meta:
            if meta.project_folder:
                dimensions["project_folder"].add(meta.project_folder)
            if meta.dataset:
                dimensions["dataset"].add(meta.dataset)
            if meta.channel:
                dimensions["channel"].add(meta.channel)
            if meta.timepoint:
                dimensions["timepoint"].add(meta.timepoint)
            if meta.z_index is not None:
                dimensions["z_index"].add(str(meta.z_index))

        # Convert sets to sorted lists
        return {k: sorted(list(v)) for k, v in dimensions.items()}

    def group_files(
        self,
        files_meta: List[Tuple[Path, FileMetadata]],
        group_by: List[str],
    ) -> Dict[Tuple[str, ...], List[Path]]:
        """Group files by specified dimensions.

        Example:
            group_by=['project_folder', 'timepoint'] will create groups:
            ('Clone 1 As', 't0'): [file1.tif, file2.tif, ...]
            ('Clone 1 As', 't1'): [file3.tif, file4.tif, ...]
            ('Clone 2 As', 't0'): [file5.tif, file6.tif, ...]

        Args:
            files_meta: List of (filepath, metadata) tuples
            group_by: List of dimension names to group by

        Returns:
            Dict mapping group keys (tuples) to lists of file paths
        """
        groups: Dict[Tuple[str, ...], List[Path]] = {}

        for file_path, meta in files_meta:
            # Build group key from requested dimensions
            key_parts = []
            for dim in group_by:
                value = getattr(meta, dim, None)
                # Convert to string, use "none" for missing values
                str_value = str(value) if value is not None else "none"
                key_parts.append(str_value)

            group_key = tuple(key_parts)

            if group_key not in groups:
                groups[group_key] = []
            groups[group_key].append(file_path)

        return groups

    def filter_files(
        self,
        files_meta: List[Tuple[Path, FileMetadata]],
        filters: Dict[str, List[str]],
    ) -> List[Path]:
        """Filter files by dimension values.

        Example:
            filters={'channel': ['ch00', 'ch01'], 'timepoint': ['t0']}
            Will return only files that are:
            - From channel ch00 OR ch01 AND
            - From timepoint t0

        Args:
            files_meta: List of (filepath, metadata) tuples
            filters: Dict mapping dimension names to lists of allowed
                     values

        Returns:
            List of file paths that match all filters
        """
        if not filters:
            return [fp for fp, _ in files_meta]

        result = []

        for file_path, meta in files_meta:
            include = True

            # Check each filter dimension
            for dim, allowed_values in filters.items():
                meta_value = getattr(meta, dim, None)

                # Convert to string for comparison
                str_value = (
                    str(meta_value) if meta_value is not None else None
                )

                # If this dimension doesn't match any allowed value,
                # exclude file
                if str_value not in allowed_values:
                    include = False
                    break

            if include:
                result.append(file_path)

        return result

    def validate_selection(
        self,
        files_meta: List[Tuple[Path, FileMetadata]],
        selection: DatasetSelection,
    ) -> bool:
        """Validate that a selection is possible with discovered files.

        Args:
            files_meta: List of discovered (filepath, metadata) tuples
            selection: User's selection to validate

        Returns:
            True if selection is valid, False otherwise
        """
        if not files_meta:
            return False

        available = self.get_available_dimensions(files_meta)

        # Check if requested dimension values exist
        dimension_filters = selection.dimension_filters

        for dim, requested_values in dimension_filters.items():
            available_values = available.get(dim, [])

            for value in requested_values:
                if value not in available_values:
                    print(
                        f"Warning: {dim}='{value}' not found in "
                        f"available values: {available_values}"
                    )
                    return False

        # Also check legacy fields for backward compatibility
        if selection.channels:
            if not set(selection.channels).issubset(
                set(available.get("channel", []))
            ):
                return False

        if selection.timepoints:
            if not set(selection.timepoints).issubset(
                set(available.get("timepoint", []))
            ):
                return False

        return True

    def get_dimension_summary(
        self, files_meta: List[Tuple[Path, FileMetadata]]
    ) -> str:
        """Generate a human-readable summary of discovered dimensions.

        Useful for logging and user feedback.

        Args:
            files_meta: List of discovered (filepath, metadata) tuples

        Returns:
            Formatted string summarizing discovered dimensions
        """
        dimensions = self.get_available_dimensions(files_meta)

        lines = [
            f"Discovered {len(files_meta)} files with the following "
            f"dimensions:"
        ]

        for dim, values in dimensions.items():
            if values:
                preview = ", ".join(values[:5])
                more = (
                    f" (and {len(values) - 5} more)"
                    if len(values) > 5
                    else ""
                )
                lines.append(
                    f"  {dim}: {len(values)} unique values - "
                    f"{preview}{more}"
                )
            else:
                lines.append(f"  {dim}: none found")

        return "\n".join(lines)
