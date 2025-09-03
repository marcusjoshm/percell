"""
Intensity value object for Percell domain.

Represents pixel intensity values with validation and operations.
"""

from dataclasses import dataclass
from typing import Union, Optional
import numpy as np


@dataclass(frozen=True)
class Intensity:
    """
    Value object representing pixel intensity with validation.
    
    This immutable value object ensures intensity values are valid and provides
    useful operations for intensity calculations.
    """
    
    value: float
    bit_depth: int = 8
    
    def __post_init__(self):
        """Validate intensity value during initialization."""
        if not isinstance(self.value, (int, float, np.number)):
            raise ValueError(f"Intensity value must be numeric, got {type(self.value)}")
        
        if self.bit_depth not in [8, 16, 32]:
            raise ValueError(f"Bit depth must be 8, 16, or 32, got {self.bit_depth}")
        
        max_value = self.get_max_value()
        if self.value < 0 or self.value > max_value:
            raise ValueError(f"Intensity value {self.value} out of range for {self.bit_depth}-bit [0, {max_value}]")
        
        # Ensure value is stored as float
        object.__setattr__(self, 'value', float(self.value))
    
    def get_max_value(self) -> int:
        """Get maximum possible value for the bit depth."""
        return (2 ** self.bit_depth) - 1
    
    def get_min_value(self) -> int:
        """Get minimum possible value (always 0)."""
        return 0
    
    def normalize(self) -> float:
        """
        Normalize intensity to [0, 1] range.
        
        Returns:
            Normalized intensity value
        """
        return self.value / self.get_max_value()
    
    def to_8bit(self) -> 'Intensity':
        """
        Convert to 8-bit intensity.
        
        Returns:
            New Intensity object with 8-bit depth
        """
        if self.bit_depth == 8:
            return self
        
        normalized = self.normalize()
        new_value = normalized * 255
        return Intensity(new_value, 8)
    
    def to_16bit(self) -> 'Intensity':
        """
        Convert to 16-bit intensity.
        
        Returns:
            New Intensity object with 16-bit depth
        """
        if self.bit_depth == 16:
            return self
        
        normalized = self.normalize()
        new_value = normalized * 65535
        return Intensity(new_value, 16)
    
    def to_32bit(self) -> 'Intensity':
        """
        Convert to 32-bit intensity.
        
        Returns:
            New Intensity object with 32-bit depth
        """
        if self.bit_depth == 32:
            return self
        
        normalized = self.normalize()
        new_value = normalized * 4294967295
        return Intensity(new_value, 32)
    
    def add(self, other: Union['Intensity', float]) -> 'Intensity':
        """
        Add intensity values.
        
        Args:
            other: Intensity or numeric value to add
            
        Returns:
            New Intensity with sum (clamped to valid range)
        """
        if isinstance(other, Intensity):
            # Convert to same bit depth
            if other.bit_depth != self.bit_depth:
                if self.bit_depth > other.bit_depth:
                    other = other.to_16bit() if self.bit_depth == 16 else other.to_32bit()
                else:
                    self_converted = self.to_16bit() if other.bit_depth == 16 else self.to_32bit()
                    return self_converted.add(other)
            other_value = other.value
        else:
            other_value = float(other)
        
        new_value = min(self.value + other_value, self.get_max_value())
        return Intensity(new_value, self.bit_depth)
    
    def subtract(self, other: Union['Intensity', float]) -> 'Intensity':
        """
        Subtract intensity values.
        
        Args:
            other: Intensity or numeric value to subtract
            
        Returns:
            New Intensity with difference (clamped to valid range)
        """
        if isinstance(other, Intensity):
            # Convert to same bit depth
            if other.bit_depth != self.bit_depth:
                if self.bit_depth > other.bit_depth:
                    other = other.to_16bit() if self.bit_depth == 16 else other.to_32bit()
                else:
                    self_converted = self.to_16bit() if other.bit_depth == 16 else self.to_32bit()
                    return self_converted.subtract(other)
            other_value = other.value
        else:
            other_value = float(other)
        
        new_value = max(self.value - other_value, 0)
        return Intensity(new_value, self.bit_depth)
    
    def multiply(self, factor: float) -> 'Intensity':
        """
        Multiply intensity by a factor.
        
        Args:
            factor: Multiplication factor
            
        Returns:
            New Intensity with product (clamped to valid range)
        """
        new_value = min(self.value * factor, self.get_max_value())
        new_value = max(new_value, 0)
        return Intensity(new_value, self.bit_depth)
    
    def divide(self, divisor: float) -> 'Intensity':
        """
        Divide intensity by a value.
        
        Args:
            divisor: Division value
            
        Returns:
            New Intensity with quotient
            
        Raises:
            ValueError: If divisor is zero
        """
        if divisor == 0:
            raise ValueError("Cannot divide by zero")
        
        new_value = self.value / divisor
        new_value = min(new_value, self.get_max_value())
        new_value = max(new_value, 0)
        return Intensity(new_value, self.bit_depth)
    
    def ratio(self, other: 'Intensity') -> float:
        """
        Calculate ratio between this and another intensity.
        
        Args:
            other: Other intensity value
            
        Returns:
            Ratio value
            
        Raises:
            ValueError: If other intensity is zero
        """
        if other.value == 0:
            raise ValueError("Cannot calculate ratio with zero intensity")
        
        # Normalize both values to compare fairly
        self_norm = self.normalize()
        other_norm = other.normalize()
        
        return self_norm / other_norm
    
    def is_above_threshold(self, threshold: Union['Intensity', float]) -> bool:
        """
        Check if intensity is above a threshold.
        
        Args:
            threshold: Threshold value
            
        Returns:
            True if above threshold
        """
        if isinstance(threshold, Intensity):
            # Convert to same bit depth for comparison
            if threshold.bit_depth != self.bit_depth:
                if self.bit_depth > threshold.bit_depth:
                    threshold = threshold.to_16bit() if self.bit_depth == 16 else threshold.to_32bit()
                else:
                    # Compare normalized values
                    return self.normalize() > threshold.normalize()
            threshold_value = threshold.value
        else:
            threshold_value = float(threshold)
        
        return self.value > threshold_value
    
    def is_below_threshold(self, threshold: Union['Intensity', float]) -> bool:
        """
        Check if intensity is below a threshold.
        
        Args:
            threshold: Threshold value
            
        Returns:
            True if below threshold
        """
        return not self.is_above_threshold(threshold)
    
    def __str__(self) -> str:
        """String representation."""
        return f"{self.value:.1f} ({self.bit_depth}-bit)"
    
    def __repr__(self) -> str:
        """String representation for debugging."""
        return f"Intensity({self.value}, {self.bit_depth})"
    
    def __eq__(self, other) -> bool:
        """Equality comparison."""
        if isinstance(other, Intensity):
            # Compare normalized values for different bit depths
            return abs(self.normalize() - other.normalize()) < 1e-10
        elif isinstance(other, (int, float)):
            return abs(self.value - float(other)) < 1e-10
        return False
    
    def __lt__(self, other) -> bool:
        """Less than comparison."""
        if isinstance(other, Intensity):
            return self.normalize() < other.normalize()
        elif isinstance(other, (int, float)):
            return self.value < float(other)
        return NotImplemented
    
    def __le__(self, other) -> bool:
        """Less than or equal comparison."""
        return self < other or self == other
    
    def __gt__(self, other) -> bool:
        """Greater than comparison."""
        if isinstance(other, Intensity):
            return self.normalize() > other.normalize()
        elif isinstance(other, (int, float)):
            return self.value > float(other)
        return NotImplemented
    
    def __ge__(self, other) -> bool:
        """Greater than or equal comparison."""
        return self > other or self == other
    
    def __hash__(self) -> int:
        """Hash for use in sets and dictionaries."""
        return hash((round(self.normalize(), 10), self.bit_depth))
