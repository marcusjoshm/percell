"""
ROI (Region of Interest) entity for Percell domain.

Represents a region of interest in microscopy images.
"""

from dataclasses import dataclass
from typing import List, Tuple, Optional, Dict, Any
import numpy as np


@dataclass
class ROI:
    """
    Represents a Region of Interest in microscopy images.
    
    This entity encapsulates all information about a segmented region,
    including its coordinates, properties, and measurements.
    """
    
    # Identification
    roi_id: str
    name: Optional[str] = None
    
    # Geometric properties
    coordinates: List[Tuple[int, int]] = None  # List of (x, y) points
    bounding_box: Optional[Tuple[int, int, int, int]] = None  # (x, y, width, height)
    area: Optional[float] = None
    perimeter: Optional[float] = None
    centroid: Optional[Tuple[float, float]] = None
    
    # Classification
    cell_type: Optional[str] = None
    group: Optional[str] = None
    
    # Measurements
    measurements: Dict[str, float] = None
    
    # Metadata
    channel: Optional[str] = None
    z_slice: Optional[int] = None
    timepoint: Optional[str] = None
    
    # Additional properties
    properties: Dict[str, Any] = None
    
    def __post_init__(self):
        """Initialize default values."""
        if self.coordinates is None:
            self.coordinates = []
        if self.measurements is None:
            self.measurements = {}
        if self.properties is None:
            self.properties = {}
    
    def calculate_area(self) -> float:
        """
        Calculate the area of the ROI using the shoelace formula.
        
        Returns:
            Area in pixels squared
        """
        if len(self.coordinates) < 3:
            return 0.0
        
        # Shoelace formula
        x_coords = [point[0] for point in self.coordinates]
        y_coords = [point[1] for point in self.coordinates]
        
        area = 0.5 * abs(sum(x_coords[i] * y_coords[i + 1] - x_coords[i + 1] * y_coords[i] 
                            for i in range(-1, len(x_coords) - 1)))
        
        self.area = area
        return area
    
    def calculate_centroid(self) -> Tuple[float, float]:
        """
        Calculate the centroid of the ROI.
        
        Returns:
            Tuple of (x, y) centroid coordinates
        """
        if not self.coordinates:
            return (0.0, 0.0)
        
        x_sum = sum(point[0] for point in self.coordinates)
        y_sum = sum(point[1] for point in self.coordinates)
        count = len(self.coordinates)
        
        centroid = (x_sum / count, y_sum / count)
        self.centroid = centroid
        return centroid
    
    def calculate_bounding_box(self) -> Tuple[int, int, int, int]:
        """
        Calculate the bounding box of the ROI.
        
        Returns:
            Tuple of (x, y, width, height)
        """
        if not self.coordinates:
            return (0, 0, 0, 0)
        
        x_coords = [point[0] for point in self.coordinates]
        y_coords = [point[1] for point in self.coordinates]
        
        min_x, max_x = min(x_coords), max(x_coords)
        min_y, max_y = min(y_coords), max(y_coords)
        
        bbox = (min_x, min_y, max_x - min_x, max_y - min_y)
        self.bounding_box = bbox
        return bbox
    
    def is_inside_point(self, x: int, y: int) -> bool:
        """
        Check if a point is inside the ROI using ray casting algorithm.
        
        Args:
            x: X coordinate
            y: Y coordinate
            
        Returns:
            True if point is inside the ROI
        """
        if not self.coordinates:
            return False
        
        n = len(self.coordinates)
        inside = False
        
        p1x, p1y = self.coordinates[0]
        for i in range(1, n + 1):
            p2x, p2y = self.coordinates[i % n]
            if y > min(p1y, p2y):
                if y <= max(p1y, p2y):
                    if x <= max(p1x, p2x):
                        if p1y != p2y:
                            xinters = (y - p1y) * (p2x - p1x) / (p2y - p1y) + p1x
                        if p1x == p2x or x <= xinters:
                            inside = not inside
            p1x, p1y = p2x, p2y
        
        return inside
    
    def scale(self, scale_factor: float) -> 'ROI':
        """
        Create a scaled version of this ROI.
        
        Args:
            scale_factor: Factor to scale by
            
        Returns:
            New scaled ROI instance
        """
        scaled_coords = [(int(x * scale_factor), int(y * scale_factor)) 
                        for x, y in self.coordinates]
        
        scaled_roi = ROI(
            roi_id=f"{self.roi_id}_scaled",
            name=f"{self.name}_scaled" if self.name else None,
            coordinates=scaled_coords,
            cell_type=self.cell_type,
            group=self.group,
            channel=self.channel,
            z_slice=self.z_slice,
            timepoint=self.timepoint,
            measurements=self.measurements.copy(),
            properties=self.properties.copy()
        )
        
        # Recalculate geometric properties
        scaled_roi.calculate_area()
        scaled_roi.calculate_centroid()
        scaled_roi.calculate_bounding_box()
        
        return scaled_roi
    
    def add_measurement(self, name: str, value: float) -> None:
        """
        Add a measurement to this ROI.
        
        Args:
            name: Measurement name
            value: Measurement value
        """
        self.measurements[name] = value
    
    def get_measurement(self, name: str) -> Optional[float]:
        """
        Get a measurement value by name.
        
        Args:
            name: Measurement name
            
        Returns:
            Measurement value or None if not found
        """
        return self.measurements.get(name)
