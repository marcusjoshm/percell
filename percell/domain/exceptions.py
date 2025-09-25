"""Custom exception hierarchy for Percell application.

This module provides domain-specific exceptions to replace generic Exception
handling throughout the codebase.
"""

from __future__ import annotations


class PercellError(Exception):
    """Base exception for all Percell-specific errors."""
    pass


class ConfigurationError(PercellError):
    """Configuration-related errors."""
    pass


class FileSystemError(PercellError):
    """File system operation errors."""
    pass


class ValidationError(PercellError):
    """Data validation errors."""
    pass


class ExternalProcessError(PercellError):
    """External process execution errors."""

    def __init__(
        self,
        message: str,
        return_code: int | None = None,
        process_name: str | None = None
    ):
        super().__init__(message)
        self.return_code = return_code
        self.process_name = process_name


class ImageJError(ExternalProcessError):
    """ImageJ execution errors."""

    def __init__(self, message: str, return_code: int | None = None):
        super().__init__(message, return_code, "ImageJ")


class CellposeError(ExternalProcessError):
    """Cellpose execution errors."""

    def __init__(self, message: str, return_code: int | None = None):
        super().__init__(message, return_code, "Cellpose")


class NapariError(ExternalProcessError):
    """Napari execution errors."""

    def __init__(self, message: str, return_code: int | None = None):
        super().__init__(message, return_code, "Napari")


class DataSelectionError(ValidationError):
    """Data selection and filtering errors."""
    pass


class ImageProcessingError(PercellError):
    """Image processing operation errors."""
    pass


class WorkflowError(PercellError):
    """Workflow execution errors."""
    pass


class VisualizationError(PercellError):
    """Visualization operation errors."""
    pass
