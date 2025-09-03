"""
File system adapter implementing FileSystemPort.

This adapter provides concrete implementations for file system operations
using the existing paths configuration system.
"""

import os
import shutil
from typing import Dict, Iterable, Iterator, Tuple
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
    
    def path_exists(self, path_or_key: str) -> bool:
        """Check if a path exists. Accepts either a filesystem path or a configured key."""
        try:
            p = Path(path_or_key)
            # If it's an absolute path or looks like a path, check directly
            if p.is_absolute() or p.exists() or os.sep in path_or_key:
                return p.exists()
            # Fallback: treat as config key
            path = self.get_path(path_or_key)
            return path.exists()
        except Exception:
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

    # Convenience to mirror callers expecting plural form
    def create_directories(self, path: str) -> None:
        try:
            Path(path).mkdir(parents=True, exist_ok=True)
        except Exception as e:
            raise FileSystemError(f"Failed to create directory {path}: {str(e)}") from e
    
    def file_exists(self, path: Path) -> bool:
        """Check if a file exists."""
        return path.is_file()
    
    def directory_exists(self, path: Path) -> bool:
        """Check if a directory exists."""
        return path.is_dir()

    # Additional helpers used by application services
    def is_directory(self, path: str) -> bool:
        try:
            return Path(path).is_dir()
        except Exception:
            return False

    def list_directory(self, path: str) -> Iterable[str]:
        try:
            return [entry.name for entry in Path(path).iterdir()]
        except Exception as e:
            raise FileSystemError(f"Failed to list directory {path}: {e}") from e

    def walk_directory(self, root: str) -> Iterator[Tuple[str, list, list]]:
        try:
            return os.walk(root)
        except Exception as e:
            raise FileSystemError(f"Failed to walk directory {root}: {e}") from e

    def read_file(self, path: Path | str, *, binary: bool = False) -> bytes | str:
        try:
            p = Path(path)
            mode = 'rb' if binary else 'r'
            with open(p, mode) as f:
                return f.read()
        except Exception as e:
            raise FileSystemError(f"Failed to read file {path}: {e}") from e

    def write_file(self, path: Path | str, data: bytes | str, *, binary: bool = False) -> None:
        try:
            p = Path(path)
            p.parent.mkdir(parents=True, exist_ok=True)
            mode = 'wb' if binary else 'w'
            with open(p, mode) as f:
                f.write(data)
        except Exception as e:
            raise FileSystemError(f"Failed to write file {path}: {e}") from e

    def copy_file(self, src: Path | str, dst: Path | str) -> None:
        try:
            src_p = Path(src)
            dst_p = Path(dst)
            dst_p.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src_p, dst_p)
        except Exception as e:
            raise FileSystemError(f"Failed to copy file {src} -> {dst}: {e}") from e
