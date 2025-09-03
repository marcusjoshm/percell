"""
Image processing port interface for Percell.

Defines the contract for image processing operations (ImageJ integration, etc.).
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Optional, Any, Tuple
import numpy as np

from percell.domain.entities.image import Image
from percell.domain.entities.roi import ROI
from percell.domain.value_objects.file_path import FilePath


class ImageProcessingPort(ABC):
    """
    Port interface for image processing operations.
    
    This interface defines how the domain layer interacts with image processing tools
    (ImageJ, custom algorithms) without depending on specific implementations.
    """
    
    @abstractmethod
    def execute_macro(self, macro_name: str, parameters: Dict[str, Any], 
                     input_files: Optional[List[FilePath]] = None) -> Dict[str, Any]:
        """
        Execute an image processing macro.
        
        Args:
            macro_name: Name of the macro to execute
            parameters: Macro parameters
            input_files: Optional input files for the macro
            
        Returns:
            Macro execution results
            
        Raises:
            ImageProcessingError: If macro execution fails
        """
        pass
    
    @abstractmethod
    def resize_rois(self, rois: List[ROI], scale_factor: float) -> List[ROI]:
        """
        Resize ROIs by a scale factor.
        
        Args:
            rois: ROIs to resize
            scale_factor: Scaling factor (1.0 = no change)
            
        Returns:
            Resized ROIs
        """
        pass
    
    @abstractmethod
    def threshold_image(self, image: Image, method: str = 'otsu',
                       parameters: Optional[Dict[str, Any]] = None) -> Image:
        """
        Apply thresholding to an image.
        
        Args:
            image: Input image
            method: Thresholding method ('otsu', 'manual', etc.)
            parameters: Method-specific parameters
            
        Returns:
            Thresholded image
            
        Raises:
            ImageProcessingError: If thresholding fails
        """
        pass
    
    @abstractmethod
    def interactive_threshold(self, image: Image, 
                            roi: Optional[ROI] = None) -> Tuple[Image, float]:
        """
        Apply interactive thresholding with user input.
        
        Args:
            image: Input image
            roi: Optional ROI to focus on
            
        Returns:
            Tuple of (thresholded image, threshold value)
            
        Raises:
            ImageProcessingError: If thresholding fails
        """
        pass
    
    @abstractmethod
    def measure_roi_intensity(self, image: Image, roi: ROI) -> Dict[str, float]:
        """
        Measure intensity statistics within an ROI.
        
        Args:
            image: Source image
            roi: ROI to measure
            
        Returns:
            Dictionary with intensity measurements
        """
        pass
    
    @abstractmethod
    def measure_roi_area(self, roi: ROI, pixel_size: Optional[float] = None) -> float:
        """
        Measure ROI area.
        
        Args:
            roi: ROI to measure
            pixel_size: Optional pixel size for calibrated measurements
            
        Returns:
            ROI area (in pixels or calibrated units)
        """
        pass
    
    @abstractmethod
    def extract_cell_region(self, image: Image, roi: ROI, 
                          padding: int = 0) -> Image:
        """
        Extract a cell region from an image.
        
        Args:
            image: Source image
            roi: ROI defining the cell region
            padding: Additional padding around the ROI
            
        Returns:
            Extracted cell image
        """
        pass
    
    @abstractmethod
    def apply_gaussian_blur(self, image: Image, sigma: float) -> Image:
        """
        Apply Gaussian blur to an image.
        
        Args:
            image: Input image
            sigma: Blur sigma value
            
        Returns:
            Blurred image
        """
        pass
    
    @abstractmethod
    def apply_median_filter(self, image: Image, kernel_size: int) -> Image:
        """
        Apply median filter to an image.
        
        Args:
            image: Input image
            kernel_size: Size of the median filter kernel
            
        Returns:
            Filtered image
        """
        pass
    
    @abstractmethod
    def enhance_contrast(self, image: Image, method: str = 'clahe',
                        parameters: Optional[Dict[str, Any]] = None) -> Image:
        """
        Enhance image contrast.
        
        Args:
            image: Input image
            method: Enhancement method ('clahe', 'histogram_eq', etc.)
            parameters: Method-specific parameters
            
        Returns:
            Contrast-enhanced image
        """
        pass
    
    @abstractmethod
    def normalize_image(self, image: Image, method: str = 'minmax') -> Image:
        """
        Normalize image intensities.
        
        Args:
            image: Input image
            method: Normalization method ('minmax', 'zscore', etc.)
            
        Returns:
            Normalized image
        """
        pass
    
    @abstractmethod
    def create_composite_image(self, images: List[Image], 
                             channels: List[str]) -> Image:
        """
        Create a composite image from multiple channels.
        
        Args:
            images: List of channel images
            channels: Channel identifiers
            
        Returns:
            Composite image
        """
        pass
    
    @abstractmethod
    def split_channels(self, image: Image) -> List[Image]:
        """
        Split a multi-channel image into separate channel images.
        
        Args:
            image: Multi-channel input image
            
        Returns:
            List of single-channel images
        """
        pass
    
    @abstractmethod
    def create_maximum_projection(self, images: List[Image]) -> Image:
        """
        Create maximum intensity projection from a stack of images.
        
        Args:
            images: List of images in the stack
            
        Returns:
            Maximum projection image
        """
        pass
    
    @abstractmethod
    def register_images(self, reference: Image, target: Image) -> Image:
        """
        Register (align) target image to reference image.
        
        Args:
            reference: Reference image
            target: Image to be aligned
            
        Returns:
            Registered target image
        """
        pass
    
    @abstractmethod
    def calculate_colocalization(self, image1: Image, image2: Image,
                               roi: Optional[ROI] = None) -> Dict[str, float]:
        """
        Calculate colocalization metrics between two images.
        
        Args:
            image1: First image
            image2: Second image
            roi: Optional ROI to restrict analysis
            
        Returns:
            Dictionary with colocalization metrics
        """
        pass
    
    @abstractmethod
    def create_binary_mask(self, rois: List[ROI], 
                          image_shape: Tuple[int, int]) -> np.ndarray:
        """
        Create binary mask from ROIs.
        
        Args:
            rois: ROIs to convert to mask
            image_shape: Shape of the output mask
            
        Returns:
            Binary mask array
        """
        pass
    
    @abstractmethod
    def apply_morphological_operations(self, image: Image, operation: str,
                                     kernel_size: int = 3) -> Image:
        """
        Apply morphological operations to an image.
        
        Args:
            image: Input binary/grayscale image
            operation: Operation type ('opening', 'closing', 'erosion', 'dilation')
            kernel_size: Size of the morphological kernel
            
        Returns:
            Processed image
        """
        pass
    
    @abstractmethod
    def detect_edges(self, image: Image, method: str = 'canny',
                    parameters: Optional[Dict[str, Any]] = None) -> Image:
        """
        Detect edges in an image.
        
        Args:
            image: Input image
            method: Edge detection method ('canny', 'sobel', etc.)
            parameters: Method-specific parameters
            
        Returns:
            Edge-detected image
        """
        pass
    
    @abstractmethod
    def get_available_macros(self) -> List[str]:
        """
        Get list of available macros.
        
        Returns:
            List of macro names
        """
        pass
    
    @abstractmethod
    def validate_macro_parameters(self, macro_name: str, 
                                parameters: Dict[str, Any]) -> bool:
        """
        Validate parameters for a macro.
        
        Args:
            macro_name: Name of the macro
            parameters: Parameters to validate
            
        Returns:
            True if parameters are valid
        """
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """
        Check if image processing service is available.
        
        Returns:
            True if service is available
        """
        pass
    
    @abstractmethod
    def get_version(self) -> str:
        """
        Get version of the image processing tool.
        
        Returns:
            Version string
        """
        pass
    
    @abstractmethod
    def cleanup_resources(self) -> None:
        """Clean up any resources used by the image processing service."""
        pass


class ImageProcessingError(Exception):
    """Exception raised by image processing operations."""
    pass
