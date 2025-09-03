"""
Metadata port interface for Percell.

Defines the contract for metadata extraction and management operations.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Optional, Any, Set
from pathlib import Path

from percell.domain.entities.metadata import Metadata
from percell.domain.entities.image import Image
from percell.domain.value_objects.file_path import FilePath


class MetadataPort(ABC):
    """
    Port interface for metadata operations.
    
    This interface defines how the domain layer interacts with metadata extraction
    and management systems without depending on specific implementations.
    """
    
    @abstractmethod
    def extract_metadata_from_filename(self, file_path: FilePath) -> Metadata:
        """
        Extract metadata from filename.
        
        Args:
            file_path: Path to the file
            
        Returns:
            Extracted metadata
            
        Raises:
            MetadataError: If metadata extraction fails
        """
        pass
    
    @abstractmethod
    def extract_metadata_from_image(self, image_path: FilePath) -> Metadata:
        """
        Extract metadata from image file headers.
        
        Args:
            image_path: Path to the image file
            
        Returns:
            Extracted metadata
            
        Raises:
            MetadataError: If metadata extraction fails
        """
        pass
    
    @abstractmethod
    def extract_metadata_from_directory(self, directory: FilePath) -> List[Metadata]:
        """
        Extract metadata from all files in a directory.
        
        Args:
            directory: Directory to scan
            
        Returns:
            List of metadata for all files
        """
        pass
    
    @abstractmethod
    def query_metadata(self, filters: Dict[str, Any]) -> List[Metadata]:
        """
        Query metadata with filters.
        
        Args:
            filters: Dictionary of filter criteria
            
        Returns:
            List of matching metadata
        """
        pass
    
    @abstractmethod
    def generate_naming_convention(self, metadata: Metadata, 
                                 template: Optional[str] = None) -> str:
        """
        Generate standardized filename from metadata.
        
        Args:
            metadata: Metadata to use for naming
            template: Optional naming template
            
        Returns:
            Generated filename
        """
        pass
    
    @abstractmethod
    def validate_naming_convention(self, filename: str) -> bool:
        """
        Validate if filename follows expected naming convention.
        
        Args:
            filename: Filename to validate
            
        Returns:
            True if filename is valid
        """
        pass
    
    @abstractmethod
    def get_unique_conditions(self, metadata_list: List[Metadata]) -> Set[str]:
        """
        Get unique conditions from metadata list.
        
        Args:
            metadata_list: List of metadata to analyze
            
        Returns:
            Set of unique conditions
        """
        pass
    
    @abstractmethod
    def get_unique_timepoints(self, metadata_list: List[Metadata]) -> Set[str]:
        """
        Get unique timepoints from metadata list.
        
        Args:
            metadata_list: List of metadata to analyze
            
        Returns:
            Set of unique timepoints
        """
        pass
    
    @abstractmethod
    def get_unique_regions(self, metadata_list: List[Metadata]) -> Set[str]:
        """
        Get unique regions from metadata list.
        
        Args:
            metadata_list: List of metadata to analyze
            
        Returns:
            Set of unique regions
        """
        pass
    
    @abstractmethod
    def get_unique_channels(self, metadata_list: List[Metadata]) -> Set[str]:
        """
        Get unique channels from metadata list.
        
        Args:
            metadata_list: List of metadata to analyze
            
        Returns:
            Set of unique channels
        """
        pass
    
    @abstractmethod
    def group_by_condition(self, metadata_list: List[Metadata]) -> Dict[str, List[Metadata]]:
        """
        Group metadata by condition.
        
        Args:
            metadata_list: List of metadata to group
            
        Returns:
            Dictionary mapping conditions to metadata lists
        """
        pass
    
    @abstractmethod
    def group_by_timepoint(self, metadata_list: List[Metadata]) -> Dict[str, List[Metadata]]:
        """
        Group metadata by timepoint.
        
        Args:
            metadata_list: List of metadata to group
            
        Returns:
            Dictionary mapping timepoints to metadata lists
        """
        pass
    
    @abstractmethod
    def group_by_region(self, metadata_list: List[Metadata]) -> Dict[str, List[Metadata]]:
        """
        Group metadata by region.
        
        Args:
            metadata_list: List of metadata to group
            
        Returns:
            Dictionary mapping regions to metadata lists
        """
        pass
    
    @abstractmethod
    def find_matching_files(self, reference_metadata: Metadata, 
                          search_directory: FilePath,
                          match_criteria: List[str]) -> List[FilePath]:
        """
        Find files matching reference metadata.
        
        Args:
            reference_metadata: Reference metadata to match against
            search_directory: Directory to search in
            match_criteria: List of metadata fields to match on
            
        Returns:
            List of matching file paths
        """
        pass
    
    @abstractmethod
    def create_metadata_index(self, directory: FilePath) -> Dict[str, Metadata]:
        """
        Create an index of all metadata in a directory.
        
        Args:
            directory: Directory to index
            
        Returns:
            Dictionary mapping file paths to metadata
        """
        pass
    
    @abstractmethod
    def update_metadata_index(self, index: Dict[str, Metadata], 
                            new_files: List[FilePath]) -> Dict[str, Metadata]:
        """
        Update existing metadata index with new files.
        
        Args:
            index: Existing metadata index
            new_files: New files to add to index
            
        Returns:
            Updated metadata index
        """
        pass
    
    @abstractmethod
    def validate_metadata_completeness(self, metadata: Metadata) -> Dict[str, bool]:
        """
        Validate completeness of metadata.
        
        Args:
            metadata: Metadata to validate
            
        Returns:
            Dictionary mapping field names to validation status
        """
        pass
    
    @abstractmethod
    def merge_metadata(self, metadata_list: List[Metadata]) -> Metadata:
        """
        Merge multiple metadata objects.
        
        Args:
            metadata_list: List of metadata to merge
            
        Returns:
            Merged metadata
        """
        pass
    
    @abstractmethod
    def export_metadata(self, metadata_list: List[Metadata], 
                       output_path: FilePath, format: str = 'json') -> None:
        """
        Export metadata to file.
        
        Args:
            metadata_list: Metadata to export
            output_path: Output file path
            format: Export format ('json', 'csv', 'excel')
            
        Raises:
            MetadataError: If export fails
        """
        pass
    
    @abstractmethod
    def import_metadata(self, input_path: FilePath) -> List[Metadata]:
        """
        Import metadata from file.
        
        Args:
            input_path: Input file path
            
        Returns:
            List of imported metadata
            
        Raises:
            MetadataError: If import fails
        """
        pass
    
    @abstractmethod
    def get_metadata_statistics(self, metadata_list: List[Metadata]) -> Dict[str, Any]:
        """
        Get statistics about metadata collection.
        
        Args:
            metadata_list: Metadata to analyze
            
        Returns:
            Dictionary with statistics
        """
        pass
    
    @abstractmethod
    def detect_naming_pattern(self, file_paths: List[FilePath]) -> Optional[str]:
        """
        Detect naming pattern from file paths.
        
        Args:
            file_paths: List of file paths to analyze
            
        Returns:
            Detected naming pattern or None if no pattern found
        """
        pass
    
    @abstractmethod
    def suggest_metadata_corrections(self, metadata: Metadata) -> List[str]:
        """
        Suggest corrections for metadata issues.
        
        Args:
            metadata: Metadata to analyze
            
        Returns:
            List of suggested corrections
        """
        pass


class MetadataError(Exception):
    """Exception raised by metadata operations."""
    pass
