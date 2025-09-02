"""
Domain exceptions for business logic errors.
"""


class DomainError(Exception):
    """Base exception for domain errors."""
    pass


class ConfigurationError(DomainError):
    """Raised when configuration is invalid or missing."""
    pass


class FileSystemError(DomainError):
    """Raised when file system operations fail."""
    pass


class SubprocessError(DomainError):
    """Raised when subprocess execution fails."""
    pass


class StageExecutionError(DomainError):
    """Raised when stage execution fails."""
    pass


class ValidationError(DomainError):
    """Raised when validation fails."""
    pass


class ImageProcessingError(DomainError):
    """Raised when image processing operations fail."""
    pass
