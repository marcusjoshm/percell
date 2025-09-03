"""
Dimensions value object for Percell domain.

Represents image dimensions with validation and utilities.
"""

from dataclasses import dataclass
from typing import Tuple, Optional


@dataclass(frozen=True)
class Dimensions:
    """
    Value object representing image dimensions.
    
    This immutable value object ensures dimensions are valid and provides
    useful utilities for dimension calculations.
    """
    
    width: int
    height: int
    channels: int = 1
    z_slices: int = 1
    timepoints: int = 1
    
    def __post_init__(self):
        """Validate dimensions during initialization."""
        if self.width <= 0:
            raise ValueError(f"Width must be positive, got {self.width}")
        if self.height <= 0:
            raise ValueError(f"Height must be positive, got {self.height}")
        if self.channels <= 0:
            raise ValueError(f"Channels must be positive, got {self.channels}")
        if self.z_slices <= 0:
            raise ValueError(f"Z-slices must be positive, got {self.z_slices}")
        if self.timepoints <= 0:
            raise ValueError(f"Timepoints must be positive, got {self.timepoints}")
    
    @classmethod
    def from_2d(cls, width: int, height: int) -> 'Dimensions':
        """
        Create 2D dimensions.
        
        Args:
            width: Image width
            height: Image height
            
        Returns:
            Dimensions instance for 2D image
        """
        return cls(width, height, 1, 1, 1)
    
    @classmethod
    def from_3d(cls, width: int, height: int, channels: int) -> 'Dimensions':
        """
        Create 3D dimensions (with channels).
        
        Args:
            width: Image width
            height: Image height
            channels: Number of channels
            
        Returns:
            Dimensions instance for 3D image
        """
        return cls(width, height, channels, 1, 1)
    
    @classmethod
    def from_shape(cls, shape: Tuple[int, ...]) -> 'Dimensions':
        """
        Create dimensions from numpy array shape.
        
        Args:
            shape: Array shape tuple
            
        Returns:
            Dimensions instance
        """
        if len(shape) == 2:
            height, width = shape
            return cls(width, height, 1, 1, 1)
        elif len(shape) == 3:
            # Could be (H, W, C) or (C, H, W)
            # Assume (H, W, C) if last dimension is small (likely channels)
            if shape[2] <= 4:
                height, width, channels = shape
            else:
                channels, height, width = shape
            return cls(width, height, channels, 1, 1)
        elif len(shape) == 4:
            # Could be (T, C, H, W) or (T, H, W, C) or (Z, C, H, W) etc.
            # This is ambiguous, so we'll make assumptions
            if shape[3] <= 4:  # Assume (T, H, W, C)
                timepoints, height, width, channels = shape
                return cls(width, height, channels, 1, timepoints)
            else:  # Assume (T, C, H, W)
                timepoints, channels, height, width = shape
                return cls(width, height, channels, 1, timepoints)
        elif len(shape) == 5:
            # Assume (T, Z, C, H, W)
            timepoints, z_slices, channels, height, width = shape
            return cls(width, height, channels, z_slices, timepoints)
        else:
            raise ValueError(f"Cannot create dimensions from shape {shape}")
    
    def get_2d_size(self) -> Tuple[int, int]:
        """Get 2D size as (width, height)."""
        return (self.width, self.height)
    
    def get_area(self) -> int:
        """Get area in pixels."""
        return self.width * self.height
    
    def get_total_pixels(self) -> int:
        """Get total number of pixels across all dimensions."""
        return self.width * self.height * self.channels * self.z_slices * self.timepoints
    
    def get_aspect_ratio(self) -> float:
        """Get aspect ratio (width / height)."""
        return self.width / self.height
    
    def is_square(self) -> bool:
        """Check if image is square."""
        return self.width == self.height
    
    def is_2d(self) -> bool:
        """Check if image is 2D (single channel, slice, timepoint)."""
        return self.channels == 1 and self.z_slices == 1 and self.timepoints == 1
    
    def is_multichannel(self) -> bool:
        """Check if image has multiple channels."""
        return self.channels > 1
    
    def is_3d_stack(self) -> bool:
        """Check if image is a 3D stack (multiple z-slices)."""
        return self.z_slices > 1
    
    def is_time_series(self) -> bool:
        """Check if image is a time series (multiple timepoints)."""
        return self.timepoints > 1
    
    def scale(self, factor: float) -> 'Dimensions':
        """
        Scale dimensions by a factor.
        
        Args:
            factor: Scaling factor
            
        Returns:
            New Dimensions with scaled width and height
        """
        new_width = max(1, int(self.width * factor))
        new_height = max(1, int(self.height * factor))
        return Dimensions(new_width, new_height, self.channels, self.z_slices, self.timepoints)
    
    def resize(self, new_width: int, new_height: int) -> 'Dimensions':
        """
        Create dimensions with new width and height.
        
        Args:
            new_width: New width
            new_height: New height
            
        Returns:
            New Dimensions with specified size
        """
        return Dimensions(new_width, new_height, self.channels, self.z_slices, self.timepoints)
    
    def crop(self, x: int, y: int, crop_width: int, crop_height: int) -> 'Dimensions':
        """
        Create dimensions for a cropped region.
        
        Args:
            x: Crop start x coordinate
            y: Crop start y coordinate
            crop_width: Crop width
            crop_height: Crop height
            
        Returns:
            New Dimensions for cropped region
        """
        # Ensure crop is within bounds
        actual_width = min(crop_width, self.width - x)
        actual_height = min(crop_height, self.height - y)
        actual_width = max(1, actual_width)
        actual_height = max(1, actual_height)
        
        return Dimensions(actual_width, actual_height, self.channels, self.z_slices, self.timepoints)
    
    def add_channel(self) -> 'Dimensions':
        """
        Add a channel.
        
        Returns:
            New Dimensions with one additional channel
        """
        return Dimensions(self.width, self.height, self.channels + 1, self.z_slices, self.timepoints)
    
    def remove_channel(self) -> 'Dimensions':
        """
        Remove a channel.
        
        Returns:
            New Dimensions with one fewer channel
            
        Raises:
            ValueError: If already at minimum channels (1)
        """
        if self.channels <= 1:
            raise ValueError("Cannot remove channel, already at minimum (1)")
        
        return Dimensions(self.width, self.height, self.channels - 1, self.z_slices, self.timepoints)
    
    def fits_in(self, other: 'Dimensions') -> bool:
        """
        Check if this dimension fits within another.
        
        Args:
            other: Other dimensions to check against
            
        Returns:
            True if this fits within other
        """
        return (self.width <= other.width and 
                self.height <= other.height and
                self.channels <= other.channels and
                self.z_slices <= other.z_slices and
                self.timepoints <= other.timepoints)
    
    def get_memory_estimate(self, bytes_per_pixel: int = 1) -> int:
        """
        Estimate memory usage in bytes.
        
        Args:
            bytes_per_pixel: Bytes per pixel (1 for 8-bit, 2 for 16-bit, etc.)
            
        Returns:
            Estimated memory usage in bytes
        """
        return self.get_total_pixels() * bytes_per_pixel
    
    def __str__(self) -> str:
        """String representation."""
        if self.is_2d():
            return f"{self.width}×{self.height}"
        elif self.channels > 1 and self.z_slices == 1 and self.timepoints == 1:
            return f"{self.width}×{self.height}×{self.channels}"
        else:
            return f"{self.width}×{self.height}×{self.channels}×{self.z_slices}×{self.timepoints}"
    
    def __repr__(self) -> str:
        """String representation for debugging."""
        return f"Dimensions({self.width}, {self.height}, {self.channels}, {self.z_slices}, {self.timepoints})"
    
    def __eq__(self, other) -> bool:
        """Equality comparison."""
        if isinstance(other, Dimensions):
            return (self.width == other.width and
                   self.height == other.height and
                   self.channels == other.channels and
                   self.z_slices == other.z_slices and
                   self.timepoints == other.timepoints)
        return False
    
    def __hash__(self) -> int:
        """Hash for use in sets and dictionaries."""
        return hash((self.width, self.height, self.channels, self.z_slices, self.timepoints))
