"""
Metadata entity for Percell domain.

Represents metadata extracted from microscopy files and filenames.
"""

from dataclasses import dataclass
from typing import Optional, Dict, Any
from pathlib import Path


@dataclass
class Metadata:
    """
    Represents metadata for microscopy images.
    
    This entity encapsulates all metadata information that can be extracted
    from filenames, file paths, and image files themselves.
    """
    
    # Core identification
    condition: Optional[str] = None
    timepoint: Optional[str] = None
    region: Optional[str] = None
    channel: Optional[str] = None
    
    # File information
    filename: Optional[str] = None
    file_path: Optional[Path] = None
    file_extension: Optional[str] = None
    
    # Image properties
    width: Optional[int] = None
    height: Optional[int] = None
    channels: Optional[int] = None
    bit_depth: Optional[int] = None
    pixel_size_x: Optional[float] = None
    pixel_size_y: Optional[float] = None
    
    # Additional metadata
    extra_metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        """Initialize extra_metadata if not provided."""
        if self.extra_metadata is None:
            self.extra_metadata = {}
    
    def get_naming_convention(self) -> str:
        """
        Generate a standardized naming convention based on metadata.
        
        Returns:
            Standardized filename string
        """
        parts = []
        
        if self.condition:
            parts.append(f"cond_{self.condition}")
        if self.timepoint:
            parts.append(f"t{self.timepoint}")
        if self.region:
            parts.append(f"reg{self.region}")
        if self.channel:
            parts.append(f"ch{self.channel}")
            
        return "_".join(parts) if parts else "unknown"
    
    def is_complete(self) -> bool:
        """
        Check if metadata has all required fields.
        
        Returns:
            True if all core fields are present
        """
        return all([
            self.condition is not None,
            self.timepoint is not None,
            self.region is not None,
            self.channel is not None
        ])
    
    def merge(self, other: 'Metadata') -> 'Metadata':
        """
        Merge this metadata with another, preferring non-None values.
        
        Args:
            other: Another Metadata instance to merge with
            
        Returns:
            New Metadata instance with merged values
        """
        merged = Metadata()
        
        # Core fields
        merged.condition = self.condition or other.condition
        merged.timepoint = self.timepoint or other.timepoint
        merged.region = self.region or other.region
        merged.channel = self.channel or other.channel
        
        # File information
        merged.filename = self.filename or other.filename
        merged.file_path = self.file_path or other.file_path
        merged.file_extension = self.file_extension or other.file_extension
        
        # Image properties
        merged.width = self.width or other.width
        merged.height = self.height or other.height
        merged.channels = self.channels or other.channels
        merged.bit_depth = self.bit_depth or other.bit_depth
        merged.pixel_size_x = self.pixel_size_x or other.pixel_size_x
        merged.pixel_size_y = self.pixel_size_y or other.pixel_size_y
        
        # Merge extra metadata
        merged.extra_metadata = {**self.extra_metadata, **other.extra_metadata}
        
        return merged
