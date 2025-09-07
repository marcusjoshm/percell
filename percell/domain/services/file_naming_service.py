"""File naming and parsing business rules.

Provides pure logic for parsing microscopy filenames and generating output
names according to PerCell conventions.
"""

from __future__ import annotations

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

        raise NotImplementedError

    def generate_output_filename(self, metadata: FileMetadata) -> str:
        """Generate a standardized output filename from metadata.

        Args:
            metadata: Structured metadata describing the file.

        Returns:
            Standardized filename string.
        """

        raise NotImplementedError

    def validate_naming_convention(self, filename: str) -> bool:
        """Validate that a filename adheres to expected conventions.

        Args:
            filename: Filename to validate.

        Returns:
            True if the name is valid, otherwise False.
        """

        raise NotImplementedError

    def extract_metadata_from_name(self, filename: str) -> Dict[str, str]:
        """Extract raw metadata tokens from a filename.

        Args:
            filename: Filename to analyze.

        Returns:
            Mapping of metadata keys to string values.
        """

        raise NotImplementedError


