from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, Iterable, Optional, Any, List, Callable, Iterator


class ImageProcessingService(ABC):
    @abstractmethod
    def run_macro(self, macro_path: str, params: Optional[Dict[str, str]] = None, *, headless: bool = False) -> int:
        """Run an ImageJ/Fiji macro and return the process return code."""


class FileSystemService(ABC):
    @abstractmethod
    def ensure_dir(self, directory: str) -> None:
        """Ensure a directory exists."""

    @abstractmethod
    def copy_files(self, files: Iterable[str], destination_dir: str) -> int:
        """Copy files to destination, returning number of files copied."""


class ProgressReporter(ABC):
    @abstractmethod
    def start(self, title: Optional[str] = None) -> None:
        """Start a progress indicator."""

    @abstractmethod
    def advance(self, delta: int = 1) -> None:
        """Advance the progress indicator."""

    @abstractmethod
    def stop(self) -> None:
        """Stop the progress indicator."""


class SubprocessPort(ABC):
    """Port for executing subprocess commands with progress reporting."""
    
    @abstractmethod
    def run_with_progress(
        self, 
        command: List[str], 
        title: Optional[str] = None,
        cwd: Optional[str] = None,
        env: Optional[Dict[str, str]] = None
    ) -> int:
        """Run a subprocess command with progress reporting."""
    
    @abstractmethod
    def run_simple(
        self, 
        command: List[str],
        cwd: Optional[str] = None,
        env: Optional[Dict[str, str]] = None
    ) -> int:
        """Run a subprocess command without progress reporting."""


class FileSystemPort(ABC):
    """Port for file system operations."""
    
    @abstractmethod
    def get_path(self, path_key: str) -> Path:
        """Get a path by key from configuration."""
    
    @abstractmethod
    def get_path_str(self, path_key: str) -> str:
        """Get a path string by key from configuration."""
    
    @abstractmethod
    def path_exists(self, path_key: str) -> bool:
        """Check if a path exists."""
    
    @abstractmethod
    def ensure_executable(self, path_key: str) -> Path:
        """Ensure a path exists and is executable."""
    
    @abstractmethod
    def list_all_paths(self) -> Dict[str, Path]:
        """List all configured paths."""
    
    @abstractmethod
    def create_directory(self, path: Path) -> None:
        """Create a directory if it doesn't exist."""
    
    @abstractmethod
    def file_exists(self, path: Path) -> bool:
        """Check if a file exists."""
    
    @abstractmethod
    def directory_exists(self, path: Path) -> bool:
        """Check if a directory exists."""


class ConfigurationPort(ABC):
    """Port for configuration management."""
    
    @abstractmethod
    def get_config(self) -> Any:
        """Get the current configuration."""
    
    @abstractmethod
    def create_default_config(self) -> Any:
        """Create a default configuration."""
    
    @abstractmethod
    def validate_software_paths(self, config: Any) -> bool:
        """Validate software paths in configuration."""
    
    @abstractmethod
    def detect_software_paths(self) -> Dict[str, str]:
        """Detect available software paths."""


class LoggingPort(ABC):
    """Port for logging operations."""
    
    @abstractmethod
    def get_logger(self, name: str) -> Any:
        """Get a logger instance."""
    
    @abstractmethod
    def create_logger(self, name: str, level: Optional[str] = None) -> Any:
        """Create a new logger instance."""
    
    @abstractmethod
    def log_info(self, message: str) -> None:
        """Log an info message."""
    
    @abstractmethod
    def log_warning(self, message: str) -> None:
        """Log a warning message."""
    
    @abstractmethod
    def log_error(self, message: str) -> None:
        """Log an error message."""
    
    @abstractmethod
    def log_debug(self, message: str) -> None:
        """Log a debug message."""


class StageRegistryPort(ABC):
    """Port for stage registration and execution."""
    
    @abstractmethod
    def register_stage(self, stage_name: str, stage_class: type) -> None:
        """Register a stage class."""
    
    @abstractmethod
    def get_stage_registry(self) -> Dict[str, type]:
        """Get the stage registry."""
    
    @abstractmethod
    def execute_stage(self, stage_name: str, **kwargs) -> Any:
        """Execute a stage by name."""


