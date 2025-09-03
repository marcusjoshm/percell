"""
Storage port interface for Percell.

Defines the contract for storage operations (file system access).
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any, Iterator
import numpy as np
from pathlib import Path

from percell.domain.entities.image import Image
from percell.domain.entities.roi import ROI
from percell.domain.value_objects.file_path import FilePath


class StoragePort(ABC):
    """
    Port interface for storage operations.
    
    This interface defines how the domain layer interacts with storage systems
    (file systems, databases, etc.) without depending on specific implementations.
    """
    
    @abstractmethod
    def create_directory(self, path: FilePath) -> None:
        """
        Create a directory.
        
        Args:
            path: Directory path to create
            
        Raises:
            StorageError: If directory creation fails
        """
        pass
    
    @abstractmethod
    def directory_exists(self, path: FilePath) -> bool:
        """
        Check if directory exists.
        
        Args:
            path: Directory path to check
            
        Returns:
            True if directory exists
        """
        pass
    
    @abstractmethod
    def file_exists(self, path: FilePath) -> bool:
        """
        Check if file exists.
        
        Args:
            path: File path to check
            
        Returns:
            True if file exists
        """
        pass
    
    @abstractmethod
    def list_files(self, directory: FilePath, pattern: Optional[str] = None, 
                  recursive: bool = False) -> List[FilePath]:
        """
        List files in a directory.
        
        Args:
            directory: Directory to search
            pattern: Optional file pattern (glob style)
            recursive: Search subdirectories
            
        Returns:
            List of file paths
        """
        pass
    
    @abstractmethod
    def list_directories(self, directory: FilePath, recursive: bool = False) -> List[FilePath]:
        """
        List subdirectories in a directory.
        
        Args:
            directory: Directory to search
            recursive: Search subdirectories
            
        Returns:
            List of directory paths
        """
        pass
    
    @abstractmethod
    def read_image(self, path: FilePath) -> np.ndarray:
        """
        Read image data from file.
        
        Args:
            path: Image file path
            
        Returns:
            Image data as numpy array
            
        Raises:
            StorageError: If image cannot be read
        """
        pass
    
    @abstractmethod
    def write_image(self, data: np.ndarray, path: FilePath, 
                   metadata: Optional[Dict[str, Any]] = None) -> None:
        """
        Write image data to file.
        
        Args:
            data: Image data as numpy array
            path: Output file path
            metadata: Optional metadata to embed
            
        Raises:
            StorageError: If image cannot be written
        """
        pass
    
    @abstractmethod
    def read_roi_file(self, path: FilePath) -> List[ROI]:
        """
        Read ROI data from file.
        
        Args:
            path: ROI file path (typically .zip file)
            
        Returns:
            List of ROI objects
            
        Raises:
            StorageError: If ROI file cannot be read
        """
        pass
    
    @abstractmethod
    def write_roi_file(self, rois: List[ROI], path: FilePath) -> None:
        """
        Write ROI data to file.
        
        Args:
            rois: List of ROI objects
            path: Output file path
            
        Raises:
            StorageError: If ROI file cannot be written
        """
        pass
    
    @abstractmethod
    def copy_file(self, source: FilePath, destination: FilePath) -> None:
        """
        Copy a file.
        
        Args:
            source: Source file path
            destination: Destination file path
            
        Raises:
            StorageError: If file cannot be copied
        """
        pass
    
    @abstractmethod
    def move_file(self, source: FilePath, destination: FilePath) -> None:
        """
        Move a file.
        
        Args:
            source: Source file path
            destination: Destination file path
            
        Raises:
            StorageError: If file cannot be moved
        """
        pass
    
    @abstractmethod
    def delete_file(self, path: FilePath) -> None:
        """
        Delete a file.
        
        Args:
            path: File path to delete
            
        Raises:
            StorageError: If file cannot be deleted
        """
        pass
    
    @abstractmethod
    def delete_directory(self, path: FilePath, recursive: bool = False) -> None:
        """
        Delete a directory.
        
        Args:
            path: Directory path to delete
            recursive: Delete contents recursively
            
        Raises:
            StorageError: If directory cannot be deleted
        """
        pass
    
    @abstractmethod
    def get_file_size(self, path: FilePath) -> int:
        """
        Get file size in bytes.
        
        Args:
            path: File path
            
        Returns:
            File size in bytes
            
        Raises:
            StorageError: If file size cannot be determined
        """
        pass
    
    @abstractmethod
    def get_modification_time(self, path: FilePath) -> float:
        """
        Get file modification time.
        
        Args:
            path: File path
            
        Returns:
            Modification time as timestamp
            
        Raises:
            StorageError: If modification time cannot be determined
        """
        pass
    
    @abstractmethod
    def read_text_file(self, path: FilePath) -> str:
        """
        Read text file content.
        
        Args:
            path: Text file path
            
        Returns:
            File content as string
            
        Raises:
            StorageError: If file cannot be read
        """
        pass
    
    @abstractmethod
    def write_text_file(self, content: str, path: FilePath) -> None:
        """
        Write text content to file.
        
        Args:
            content: Text content
            path: Output file path
            
        Raises:
            StorageError: If file cannot be written
        """
        pass
    
    @abstractmethod
    def read_json_file(self, path: FilePath) -> Dict[str, Any]:
        """
        Read JSON file content.
        
        Args:
            path: JSON file path
            
        Returns:
            Parsed JSON data
            
        Raises:
            StorageError: If file cannot be read or parsed
        """
        pass
    
    @abstractmethod
    def write_json_file(self, data: Dict[str, Any], path: FilePath) -> None:
        """
        Write data to JSON file.
        
        Args:
            data: Data to write
            path: Output file path
            
        Raises:
            StorageError: If file cannot be written
        """
        pass
    
    @abstractmethod
    def cleanup_temp_files(self, directory: FilePath, 
                          older_than_hours: Optional[float] = None) -> int:
        """
        Clean up temporary files.
        
        Args:
            directory: Directory to clean
            older_than_hours: Only delete files older than this many hours
            
        Returns:
            Number of files deleted
        """
        pass
    
    @abstractmethod
    def get_disk_usage(self, path: FilePath) -> Dict[str, int]:
        """
        Get disk usage information.
        
        Args:
            path: Path to check
            
        Returns:
            Dictionary with 'total', 'used', 'free' in bytes
        """
        pass
    
    @abstractmethod
    def create_backup(self, source: FilePath, backup_dir: FilePath) -> FilePath:
        """
        Create a backup of a file or directory.
        
        Args:
            source: Source path to backup
            backup_dir: Directory to store backup
            
        Returns:
            Path to created backup
            
        Raises:
            StorageError: If backup cannot be created
        """
        pass
    
    @abstractmethod
    def watch_directory(self, directory: FilePath) -> Iterator[FilePath]:
        """
        Watch directory for changes.
        
        Args:
            directory: Directory to watch
            
        Yields:
            Paths of changed files
        """
        pass


class StorageError(Exception):
    """Exception raised by storage operations."""
    pass
