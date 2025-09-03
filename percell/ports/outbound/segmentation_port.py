"""
Segmentation port interface for Percell.

Defines the contract for cell segmentation operations.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Optional, Any, Tuple
import numpy as np

from percell.domain.entities.image import Image
from percell.domain.entities.roi import ROI
from percell.domain.value_objects.file_path import FilePath


class SegmentationPort(ABC):
    """
    Port interface for cell segmentation operations.
    
    This interface defines how the domain layer interacts with segmentation tools
    (Cellpose, other segmentation algorithms) without depending on specific implementations.
    """
    
    @abstractmethod
    def segment_cells(self, image: Image, parameters: Dict[str, Any]) -> List[ROI]:
        """
        Segment cells in an image.
        
        Args:
            image: Input image to segment
            parameters: Segmentation parameters
            
        Returns:
            List of detected cell ROIs
            
        Raises:
            SegmentationError: If segmentation fails
        """
        pass
    
    @abstractmethod
    def segment_batch(self, images: List[Image], 
                     parameters: Dict[str, Any]) -> Dict[str, List[ROI]]:
        """
        Segment cells in multiple images.
        
        Args:
            images: List of images to segment
            parameters: Segmentation parameters
            
        Returns:
            Dictionary mapping image IDs to ROI lists
            
        Raises:
            SegmentationError: If batch segmentation fails
        """
        pass
    
    @abstractmethod
    def validate_segmentation(self, rois: List[ROI], 
                            image: Optional[Image] = None) -> Dict[str, Any]:
        """
        Validate segmentation results.
        
        Args:
            rois: ROIs to validate
            image: Optional source image for validation
            
        Returns:
            Validation results with metrics and quality scores
        """
        pass
    
    @abstractmethod
    def get_supported_models(self) -> List[str]:
        """
        Get list of supported segmentation models.
        
        Returns:
            List of model names
        """
        pass
    
    @abstractmethod
    def get_default_parameters(self, model: Optional[str] = None) -> Dict[str, Any]:
        """
        Get default parameters for segmentation.
        
        Args:
            model: Optional model name
            
        Returns:
            Dictionary of default parameters
        """
        pass
    
    @abstractmethod
    def estimate_processing_time(self, image: Image, 
                               parameters: Dict[str, Any]) -> float:
        """
        Estimate processing time for segmentation.
        
        Args:
            image: Input image
            parameters: Segmentation parameters
            
        Returns:
            Estimated processing time in seconds
        """
        pass
    
    @abstractmethod
    def preprocess_image(self, image: Image, 
                        parameters: Dict[str, Any]) -> Image:
        """
        Preprocess image for segmentation.
        
        Args:
            image: Input image
            parameters: Preprocessing parameters
            
        Returns:
            Preprocessed image
        """
        pass
    
    @abstractmethod
    def postprocess_rois(self, rois: List[ROI], 
                        parameters: Dict[str, Any]) -> List[ROI]:
        """
        Postprocess segmentation results.
        
        Args:
            rois: Raw segmentation ROIs
            parameters: Postprocessing parameters
            
        Returns:
            Processed ROIs
        """
        pass
    
    @abstractmethod
    def filter_rois_by_size(self, rois: List[ROI], 
                          min_area: Optional[float] = None,
                          max_area: Optional[float] = None) -> List[ROI]:
        """
        Filter ROIs by size criteria.
        
        Args:
            rois: ROIs to filter
            min_area: Minimum area threshold
            max_area: Maximum area threshold
            
        Returns:
            Filtered ROIs
        """
        pass
    
    @abstractmethod
    def filter_rois_by_shape(self, rois: List[ROI], 
                           min_circularity: Optional[float] = None,
                           max_aspect_ratio: Optional[float] = None) -> List[ROI]:
        """
        Filter ROIs by shape criteria.
        
        Args:
            rois: ROIs to filter
            min_circularity: Minimum circularity threshold
            max_aspect_ratio: Maximum aspect ratio threshold
            
        Returns:
            Filtered ROIs
        """
        pass
    
    @abstractmethod
    def merge_overlapping_rois(self, rois: List[ROI], 
                             overlap_threshold: float = 0.5) -> List[ROI]:
        """
        Merge overlapping ROIs.
        
        Args:
            rois: ROIs to process
            overlap_threshold: Overlap threshold for merging
            
        Returns:
            ROIs with overlapping ones merged
        """
        pass
    
    @abstractmethod
    def split_touching_cells(self, rois: List[ROI], 
                           image: Optional[Image] = None) -> List[ROI]:
        """
        Split touching or clustered cells.
        
        Args:
            rois: ROIs that may contain multiple cells
            image: Optional source image for splitting guidance
            
        Returns:
            ROIs with split cells
        """
        pass
    
    @abstractmethod
    def calculate_roi_properties(self, roi: ROI, 
                               image: Optional[Image] = None) -> Dict[str, float]:
        """
        Calculate additional properties for an ROI.
        
        Args:
            roi: ROI to analyze
            image: Optional source image for intensity measurements
            
        Returns:
            Dictionary of calculated properties
        """
        pass
    
    @abstractmethod
    def export_masks(self, rois: List[ROI], image_shape: Tuple[int, int], 
                    output_path: FilePath) -> None:
        """
        Export ROIs as segmentation masks.
        
        Args:
            rois: ROIs to export
            image_shape: Shape of the original image (height, width)
            output_path: Path to save mask image
            
        Raises:
            SegmentationError: If export fails
        """
        pass
    
    @abstractmethod
    def import_masks(self, mask_path: FilePath) -> List[ROI]:
        """
        Import ROIs from segmentation masks.
        
        Args:
            mask_path: Path to mask image file
            
        Returns:
            List of ROIs extracted from masks
            
        Raises:
            SegmentationError: If import fails
        """
        pass
    
    @abstractmethod
    def get_segmentation_statistics(self, rois: List[ROI]) -> Dict[str, Any]:
        """
        Get statistics about segmentation results.
        
        Args:
            rois: Segmented ROIs
            
        Returns:
            Dictionary with segmentation statistics
        """
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """
        Check if segmentation service is available.
        
        Returns:
            True if service is available and ready
        """
        pass
    
    @abstractmethod
    def get_version(self) -> str:
        """
        Get version of the segmentation tool.
        
        Returns:
            Version string
        """
        pass
    
    @abstractmethod
    def cleanup_resources(self) -> None:
        """Clean up any resources used by the segmentation service."""
        pass


class SegmentationError(Exception):
    """Exception raised by segmentation operations."""
    pass
