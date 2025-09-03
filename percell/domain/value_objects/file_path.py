"""
FilePath value object for Percell domain.

Represents file paths with validation and utilities.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Optional, List
import os


@dataclass(frozen=True)
class FilePath:
    """
    Value object representing a file path with validation.
    
    This immutable value object ensures file paths are valid and provides
    useful utilities for path manipulation.
    """
    
    path: Path
    
    def __post_init__(self):
        """Validate the path during initialization."""
        if not isinstance(self.path, Path):
            object.__setattr__(self, 'path', Path(self.path))
    
    @classmethod
    def from_string(cls, path_str: str) -> 'FilePath':
        """
        Create FilePath from string.
        
        Args:
            path_str: Path as string
            
        Returns:
            FilePath instance
        """
        return cls(Path(path_str))
    
    @classmethod
    def from_parts(cls, *parts: str) -> 'FilePath':
        """
        Create FilePath from path parts.
        
        Args:
            parts: Path components
            
        Returns:
            FilePath instance
        """
        return cls(Path(*parts))
    
    def exists(self) -> bool:
        """Check if the path exists."""
        return self.path.exists()
    
    def is_file(self) -> bool:
        """Check if the path is a file."""
        return self.path.is_file()
    
    def is_directory(self) -> bool:
        """Check if the path is a directory."""
        return self.path.is_dir()
    
    def is_absolute(self) -> bool:
        """Check if the path is absolute."""
        return self.path.is_absolute()
    
    def get_parent(self) -> 'FilePath':
        """Get parent directory."""
        return FilePath(self.path.parent)
    
    def get_name(self) -> str:
        """Get filename."""
        return self.path.name
    
    def get_stem(self) -> str:
        """Get filename without extension."""
        return self.path.stem
    
    def get_suffix(self) -> str:
        """Get file extension."""
        return self.path.suffix
    
    def get_suffixes(self) -> List[str]:
        """Get all file extensions."""
        return self.path.suffixes
    
    def join(self, *parts: str) -> 'FilePath':
        """
        Join with additional path parts.
        
        Args:
            parts: Path parts to join
            
        Returns:
            New FilePath with joined parts
        """
        return FilePath(self.path / Path(*parts))
    
    def with_name(self, name: str) -> 'FilePath':
        """
        Create new path with different filename.
        
        Args:
            name: New filename
            
        Returns:
            New FilePath with different name
        """
        return FilePath(self.path.with_name(name))
    
    def with_suffix(self, suffix: str) -> 'FilePath':
        """
        Create new path with different extension.
        
        Args:
            suffix: New file extension
            
        Returns:
            New FilePath with different extension
        """
        return FilePath(self.path.with_suffix(suffix))
    
    def with_stem(self, stem: str) -> 'FilePath':
        """
        Create new path with different stem (filename without extension).
        
        Args:
            stem: New filename stem
            
        Returns:
            New FilePath with different stem
        """
        return FilePath(self.path.with_stem(stem))
    
    def resolve(self) -> 'FilePath':
        """Get absolute, resolved path."""
        return FilePath(self.path.resolve())
    
    def relative_to(self, other: 'FilePath') -> 'FilePath':
        """
        Get path relative to another path.
        
        Args:
            other: Base path
            
        Returns:
            Relative path
        """
        return FilePath(self.path.relative_to(other.path))
    
    def is_relative_to(self, other: 'FilePath') -> bool:
        """
        Check if this path is relative to another path.
        
        Args:
            other: Base path to check against
            
        Returns:
            True if this path is under the other path
        """
        try:
            self.path.relative_to(other.path)
            return True
        except ValueError:
            return False
    
    def mkdir(self, parents: bool = False, exist_ok: bool = False) -> None:
        """
        Create directory.
        
        Args:
            parents: Create parent directories
            exist_ok: Don't raise error if directory exists
        """
        self.path.mkdir(parents=parents, exist_ok=exist_ok)
    
    def unlink(self, missing_ok: bool = False) -> None:
        """
        Remove file.
        
        Args:
            missing_ok: Don't raise error if file doesn't exist
        """
        self.path.unlink(missing_ok=missing_ok)
    
    def get_size(self) -> Optional[int]:
        """
        Get file size in bytes.
        
        Returns:
            File size or None if file doesn't exist
        """
        try:
            return self.path.stat().st_size
        except (OSError, FileNotFoundError):
            return None
    
    def get_modification_time(self) -> Optional[float]:
        """
        Get file modification time.
        
        Returns:
            Modification time as timestamp or None if file doesn't exist
        """
        try:
            return self.path.stat().st_mtime
        except (OSError, FileNotFoundError):
            return None
    
    def is_image_file(self) -> bool:
        """Check if the file is an image based on extension."""
        image_extensions = {'.tif', '.tiff', '.png', '.jpg', '.jpeg', '.bmp', '.gif'}
        return self.get_suffix().lower() in image_extensions
    
    def is_roi_file(self) -> bool:
        """Check if the file is an ROI file."""
        return self.get_suffix().lower() == '.zip'
    
    def is_config_file(self) -> bool:
        """Check if the file is a configuration file."""
        config_extensions = {'.json', '.yaml', '.yml', '.ini', '.cfg'}
        return self.get_suffix().lower() in config_extensions
    
    def __str__(self) -> str:
        """String representation."""
        return str(self.path)
    
    def __repr__(self) -> str:
        """String representation for debugging."""
        return f"FilePath('{self.path}')"
    
    def __eq__(self, other) -> bool:
        """Equality comparison."""
        if isinstance(other, FilePath):
            return self.path == other.path
        elif isinstance(other, (str, Path)):
            return self.path == Path(other)
        return False
    
    def __hash__(self) -> int:
        """Hash for use in sets and dictionaries."""
        return hash(self.path)
    
    def __lt__(self, other) -> bool:
        """Less than comparison for sorting."""
        if isinstance(other, FilePath):
            return str(self.path) < str(other.path)
        return str(self.path) < str(other)
