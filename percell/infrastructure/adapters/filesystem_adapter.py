"""
File system adapter implementing FileSystemPort.

This adapter provides concrete implementations for file system operations
using the existing paths configuration system.
"""

import os
import shutil
from typing import Dict
from pathlib import Path

from percell.domain.ports import FileSystemPort
from percell.domain.exceptions import FileSystemError, ConfigurationError


class FileSystemAdapter(FileSystemPort):
    """Concrete implementation of FileSystemPort using pathlib and os."""
    
    def __init__(self, config):
        """Initialize with configuration that contains path mappings."""
        self.config = config
        self._path_config = getattr(config, 'paths', {})
    
    def get_path(self, path_key: str) -> Path:
        """Get a path by key from configuration."""
        if path_key not in self._path_config:
            raise ConfigurationError(f"Path key '{path_key}' not found in configuration")
        
        path_str = self._path_config[path_key]
        return Path(path_str)
    
    def get_path_str(self, path_key: str) -> str:
        """Get a path string by key from configuration."""
        return str(self.get_path(path_key))
    
    def path_exists(self, path_key: str) -> bool:
        """Check if a path exists."""
        try:
            path = self.get_path(path_key)
            return path.exists()
        except ConfigurationError:
            return False
    
    def ensure_executable(self, path_key: str) -> Path:
        """Ensure a path exists and is executable."""
        path = self.get_path(path_key)
        
        if not path.exists():
            raise FileSystemError(f"Path does not exist: {path}")
        
        if not os.access(path, os.X_OK):
            raise FileSystemError(f"Path is not executable: {path}")
        
        return path
    
    def list_all_paths(self) -> Dict[str, Path]:
        """List all configured paths."""
        return {key: Path(value) for key, value in self._path_config.items()}
    
    def create_directory(self, path: Path) -> None:
        """Create a directory if it doesn't exist."""
        try:
            path.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            raise FileSystemError(f"Failed to create directory {path}: {str(e)}") from e
    
    def file_exists(self, path: Path) -> bool:
        """Check if a file exists."""
        return path.is_file()
    
    def directory_exists(self, path: Path) -> bool:
        """Check if a directory exists."""
        return path.is_dir()
