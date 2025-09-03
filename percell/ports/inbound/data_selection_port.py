"""
Data selection port interface for Percell.

Defines the contract for data selection and validation operations.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Optional, Any, Set
from percell.domain.entities.metadata import Metadata
from percell.domain.value_objects.file_path import FilePath


class DataSelectionPort(ABC):
    """
    Port interface for data selection operations.
    
    This interface defines how external systems can select and validate
    input data for processing.
    """
    
    @abstractmethod
    def select_input_directory(self, default_path: Optional[FilePath] = None) -> FilePath:
        """
        Select input directory for processing.
        
        Args:
            default_path: Optional default directory path
            
        Returns:
            Selected directory path
            
        Raises:
            DataSelectionError: If selection fails or is cancelled
        """
        pass
    
    @abstractmethod
    def select_output_directory(self, default_path: Optional[FilePath] = None) -> FilePath:
        """
        Select output directory for results.
        
        Args:
            default_path: Optional default directory path
            
        Returns:
            Selected directory path
            
        Raises:
            DataSelectionError: If selection fails or is cancelled
        """
        pass
    
    @abstractmethod
    def discover_images(self, directory: FilePath, 
                       patterns: Optional[List[str]] = None) -> List[FilePath]:
        """
        Discover image files in a directory.
        
        Args:
            directory: Directory to search
            patterns: Optional file patterns to match
            
        Returns:
            List of discovered image file paths
        """
        pass
    
    @abstractmethod
    def validate_input_data(self, file_paths: List[FilePath]) -> Dict[str, Any]:
        """
        Validate input data files.
        
        Args:
            file_paths: List of file paths to validate
            
        Returns:
            Validation results with status and issues
        """
        pass
    
    @abstractmethod
    def extract_data_structure(self, directory: FilePath) -> Dict[str, Any]:
        """
        Extract and analyze data structure from directory.
        
        Args:
            directory: Directory to analyze
            
        Returns:
            Data structure information
        """
        pass
    
    @abstractmethod
    def select_conditions(self, available_conditions: Set[str], 
                         default_selection: Optional[Set[str]] = None) -> Set[str]:
        """
        Select experimental conditions to process.
        
        Args:
            available_conditions: Set of available conditions
            default_selection: Optional default selection
            
        Returns:
            Selected conditions
        """
        pass
    
    @abstractmethod
    def select_timepoints(self, available_timepoints: Set[str], 
                         default_selection: Optional[Set[str]] = None) -> Set[str]:
        """
        Select timepoints to process.
        
        Args:
            available_timepoints: Set of available timepoints
            default_selection: Optional default selection
            
        Returns:
            Selected timepoints
        """
        pass
    
    @abstractmethod
    def select_regions(self, available_regions: Set[str], 
                      default_selection: Optional[Set[str]] = None) -> Set[str]:
        """
        Select regions to process.
        
        Args:
            available_regions: Set of available regions
            default_selection: Optional default selection
            
        Returns:
            Selected regions
        """
        pass
    
    @abstractmethod
    def select_channels(self, available_channels: Set[str], 
                       default_selection: Optional[Set[str]] = None) -> Dict[str, str]:
        """
        Select and assign channel roles.
        
        Args:
            available_channels: Set of available channels
            default_selection: Optional default selection
            
        Returns:
            Dictionary mapping channel roles to channel IDs
        """
        pass
    
    @abstractmethod
    def preview_selection(self, selection_criteria: Dict[str, Any]) -> Dict[str, Any]:
        """
        Preview what files will be processed based on selection criteria.
        
        Args:
            selection_criteria: Selection criteria to preview
            
        Returns:
            Preview information including file counts and examples
        """
        pass
    
    @abstractmethod
    def confirm_selection(self, preview_info: Dict[str, Any]) -> bool:
        """
        Confirm the data selection.
        
        Args:
            preview_info: Preview information to confirm
            
        Returns:
            True if selection is confirmed
        """
        pass
    
    @abstractmethod
    def save_selection_criteria(self, criteria: Dict[str, Any], 
                              save_path: FilePath) -> None:
        """
        Save selection criteria to file.
        
        Args:
            criteria: Selection criteria to save
            save_path: Path to save criteria
            
        Raises:
            DataSelectionError: If save fails
        """
        pass
    
    @abstractmethod
    def load_selection_criteria(self, load_path: FilePath) -> Dict[str, Any]:
        """
        Load selection criteria from file.
        
        Args:
            load_path: Path to load criteria from
            
        Returns:
            Loaded selection criteria
            
        Raises:
            DataSelectionError: If load fails
        """
        pass


class DataSelectionError(Exception):
    """Exception raised by data selection operations."""
    pass
