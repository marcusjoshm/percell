"""
Image entity for Percell domain.

Represents microscopy images with their properties and data.
"""

from dataclasses import dataclass
from typing import Optional, List, Tuple, Any
import numpy as np
from pathlib import Path

from .metadata import Metadata
from .roi import ROI


@dataclass
class Image:
    """
    Represents a microscopy image with its data and properties.
    
    This entity encapsulates image data, metadata, and associated ROIs.
    """
    
    # Core properties
    image_id: str
    data: Optional[np.ndarray] = None
    metadata: Optional[Metadata] = None
    
    # File information
    file_path: Optional[Path] = None
    
    # Image properties
    width: Optional[int] = None
    height: Optional[int] = None
    channels: Optional[int] = None
    bit_depth: Optional[int] = None
    
    # Associated ROIs
    rois: List[ROI] = None
    
    # Processing state
    is_preprocessed: bool = False
    preprocessing_steps: List[str] = None
    
    def __post_init__(self):
        """Initialize default values."""
        if self.rois is None:
            self.rois = []
        if self.preprocessing_steps is None:
            self.preprocessing_steps = []
        
        # Extract properties from data if available
        if self.data is not None:
            self._extract_properties_from_data()
    
    def _extract_properties_from_data(self) -> None:
        """Extract image properties from numpy array data."""
        if self.data is None:
            return
        
        if len(self.data.shape) == 2:
            self.height, self.width = self.data.shape
            self.channels = 1
        elif len(self.data.shape) == 3:
            if self.data.shape[2] <= 4:  # Assume channels last
                self.height, self.width, self.channels = self.data.shape
            else:  # Assume channels first
                self.channels, self.height, self.width = self.data.shape
        
        self.bit_depth = self._infer_bit_depth()
    
    def _infer_bit_depth(self) -> int:
        """Infer bit depth from data type."""
        if self.data is None:
            return 8
        
        dtype_map = {
            np.uint8: 8,
            np.uint16: 16,
            np.uint32: 32,
            np.float32: 32,
            np.float64: 64
        }
        
        return dtype_map.get(self.data.dtype.type, 8)
    
    def add_roi(self, roi: ROI) -> None:
        """
        Add an ROI to this image.
        
        Args:
            roi: ROI to add
        """
        self.rois.append(roi)
    
    def remove_roi(self, roi_id: str) -> bool:
        """
        Remove an ROI by ID.
        
        Args:
            roi_id: ID of ROI to remove
            
        Returns:
            True if ROI was removed, False if not found
        """
        for i, roi in enumerate(self.rois):
            if roi.roi_id == roi_id:
                del self.rois[i]
                return True
        return False
    
    def get_roi(self, roi_id: str) -> Optional[ROI]:
        """
        Get an ROI by ID.
        
        Args:
            roi_id: ID of ROI to find
            
        Returns:
            ROI instance or None if not found
        """
        for roi in self.rois:
            if roi.roi_id == roi_id:
                return roi
        return None
    
    def get_rois_by_channel(self, channel: str) -> List[ROI]:
        """
        Get all ROIs for a specific channel.
        
        Args:
            channel: Channel identifier
            
        Returns:
            List of ROIs for the channel
        """
        return [roi for roi in self.rois if roi.channel == channel]
    
    def get_rois_by_group(self, group: str) -> List[ROI]:
        """
        Get all ROIs for a specific group.
        
        Args:
            group: Group identifier
            
        Returns:
            List of ROIs for the group
        """
        return [roi for roi in self.rois if roi.group == group]
    
    def crop_to_roi(self, roi: ROI) -> Optional[np.ndarray]:
        """
        Crop image data to ROI bounding box.
        
        Args:
            roi: ROI to crop to
            
        Returns:
            Cropped image data or None if no data
        """
        if self.data is None or roi.bounding_box is None:
            return None
        
        x, y, w, h = roi.bounding_box
        
        # Ensure coordinates are within image bounds
        x = max(0, min(x, self.width - 1))
        y = max(0, min(y, self.height - 1))
        w = min(w, self.width - x)
        h = min(h, self.height - y)
        
        if len(self.data.shape) == 2:
            return self.data[y:y+h, x:x+w]
        elif len(self.data.shape) == 3:
            return self.data[y:y+h, x:x+w, :]
        
        return None
    
    def apply_preprocessing_step(self, step_name: str) -> None:
        """
        Mark a preprocessing step as applied.
        
        Args:
            step_name: Name of the preprocessing step
        """
        if step_name not in self.preprocessing_steps:
            self.preprocessing_steps.append(step_name)
        
        if not self.is_preprocessed:
            self.is_preprocessed = True
    
    def is_step_applied(self, step_name: str) -> bool:
        """
        Check if a preprocessing step has been applied.
        
        Args:
            step_name: Name of the step to check
            
        Returns:
            True if step has been applied
        """
        return step_name in self.preprocessing_steps
    
    def get_pixel_intensity_at(self, x: int, y: int, channel: Optional[int] = None) -> Any:
        """
        Get pixel intensity at specific coordinates.
        
        Args:
            x: X coordinate
            y: Y coordinate
            channel: Channel index (optional)
            
        Returns:
            Pixel intensity value
        """
        if self.data is None:
            return None
        
        if x < 0 or x >= self.width or y < 0 or y >= self.height:
            return None
        
        if len(self.data.shape) == 2:
            return self.data[y, x]
        elif len(self.data.shape) == 3:
            if channel is None:
                return self.data[y, x, :]
            else:
                return self.data[y, x, channel]
        
        return None
    
    def get_statistics(self) -> dict:
        """
        Get basic statistics about the image.
        
        Returns:
            Dictionary with image statistics
        """
        stats = {
            'width': self.width,
            'height': self.height,
            'channels': self.channels,
            'bit_depth': self.bit_depth,
            'num_rois': len(self.rois),
            'is_preprocessed': self.is_preprocessed,
            'preprocessing_steps': len(self.preprocessing_steps)
        }
        
        if self.data is not None:
            stats.update({
                'min_intensity': float(np.min(self.data)),
                'max_intensity': float(np.max(self.data)),
                'mean_intensity': float(np.mean(self.data)),
                'std_intensity': float(np.std(self.data))
            })
        
        return stats
