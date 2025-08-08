"""
Centralized path configuration for the Microscopy Single-Cell Analysis Pipeline

This module provides a centralized way to manage all file paths used throughout
the application. This makes it easier to maintain and update paths when the
project structure changes.
"""

import os
import sys
from pathlib import Path
from typing import Dict, Any, Optional


class PathConfig:
    """
    Centralized path configuration for the percell package.
    
    This class manages all file paths used throughout the application,
    making it easy to update paths when the project structure changes.
    """
    
    def __init__(self):
        """Initialize the path configuration."""
        self._package_root = self._find_package_root()
        self._paths = self._initialize_paths()
    
    def _find_package_root(self) -> Path:
        """
        Find the root directory of the percell package.
        
        Returns:
            Path to the package root directory
        """
        # Try to find the package root by looking for the percell directory
        # that contains the bash, config, macros, etc. subdirectories
        
        # First, try to get it from the current module's location
        current_file = Path(__file__)
        package_root = current_file.parent.parent  # Go up from core/paths.py to percell/
        
        # Verify this is the correct package root by checking for expected subdirectories
        expected_dirs = ['bash', 'config', 'macros', 'core', 'modules']
        if all((package_root / dir_name).exists() for dir_name in expected_dirs):
            return package_root
        
        # If that doesn't work, try to find it in the Python path
        for path in sys.path:
            potential_root = Path(path) / 'percell'
            if potential_root.exists() and all((potential_root / dir_name).exists() for dir_name in expected_dirs):
                return potential_root
        
        # If still not found, try to find it relative to the current working directory
        cwd = Path.cwd()
        potential_root = cwd / 'percell'
        if potential_root.exists() and all((potential_root / dir_name).exists() for dir_name in expected_dirs):
            return potential_root
        
        # Last resort: try to find it in the parent directories of current working directory
        current = cwd
        for _ in range(10):  # Limit depth to avoid infinite loops
            potential_root = current / 'percell'
            if potential_root.exists() and all((potential_root / dir_name).exists() for dir_name in expected_dirs):
                return potential_root
            current = current.parent
            if current == current.parent:  # Reached root
                break
        
        # If all else fails, return a default path and let the caller handle the error
        return Path(__file__).parent.parent
    
    def _initialize_paths(self) -> Dict[str, Path]:
        """
        Initialize all the paths used in the application.
        
        Returns:
            Dictionary mapping path names to their absolute paths
        """
        paths = {
            # Package structure
            'package_root': self._package_root,
            'core': self._package_root / 'core',
            'modules': self._package_root / 'modules',
            'main': self._package_root / 'main',
            
            # Configuration files
            'config_dir': self._package_root / 'config',
            'config_template': self._package_root / 'config' / 'config.template.json',
            'config_default': self._package_root / 'config' / 'config.json',
            
            # Bash scripts
            'bash_dir': self._package_root / 'bash',
            'setup_output_structure_script': self._package_root / 'bash' / 'setup_output_structure.sh',
            'prepare_input_structure_script': self._package_root / 'bash' / 'prepare_input_structure.sh',
            'launch_segmentation_tools_script': self._package_root / 'bash' / 'launch_segmentation_tools.sh',
            
            # Python modules
            'bin_images_module': self._package_root / 'modules' / 'bin_images.py',
            'analyze_cell_masks_module': self._package_root / 'modules' / 'analyze_cell_masks.py',
            'combine_masks_module': self._package_root / 'modules' / 'combine_masks.py',
            'create_cell_masks_module': self._package_root / 'modules' / 'create_cell_masks.py',
            'directory_setup_module': self._package_root / 'modules' / 'directory_setup.py',
            'duplicate_rois_for_channels_module': self._package_root / 'modules' / 'duplicate_rois_for_channels.py',
            'extract_cells_module': self._package_root / 'modules' / 'extract_cells.py',
            'group_cells_module': self._package_root / 'modules' / 'group_cells.py',
            'include_group_metadata_module': self._package_root / 'modules' / 'include_group_metadata.py',
            'measure_roi_area_module': self._package_root / 'modules' / 'measure_roi_area.py',
            'otsu_threshold_grouped_cells_module': self._package_root / 'modules' / 'otsu_threshold_grouped_cells.py',
            'resize_rois_module': self._package_root / 'modules' / 'resize_rois.py',
            'set_directories_module': self._package_root / 'modules' / 'set_directories.py',
            'stage_classes_module': self._package_root / 'modules' / 'stage_classes.py',
            'stage_registry_module': self._package_root / 'modules' / 'stage_registry.py',
            'track_rois_module': self._package_root / 'modules' / 'track_rois.py',
            
            # ImageJ macros
            'macros_dir': self._package_root / 'macros',
            'analyze_cell_masks_macro': self._package_root / 'macros' / 'analyze_cell_masks.ijm',
            'create_cell_masks_macro': self._package_root / 'macros' / 'create_cell_masks.ijm',
            'extract_cells_macro': self._package_root / 'macros' / 'extract_cells.ijm',
            'measure_roi_area_macro': self._package_root / 'macros' / 'measure_roi_area.ijm',
            'resize_rois_macro': self._package_root / 'macros' / 'resize_rois.ijm',
            'threshold_grouped_cells_macro': self._package_root / 'macros' / 'threshold_grouped_cells.ijm',
            
            # Art and documentation
            'art_dir': self._package_root / 'art',
            'percell_terminal_window_image': self._package_root / 'art' / 'percell_terminal_window.png',
            
            # Setup and requirements
            'setup_dir': self._package_root / 'setup',
            'requirements_file': self._package_root / 'setup' / 'requirements.txt',
            'requirements_cellpose_file': self._package_root / 'setup' / 'requirements_cellpose.txt',
            'install_script': self._package_root / 'setup' / 'install.py',
        }
        
        return paths
    
    def get_path(self, path_name: str) -> Path:
        """
        Get a specific path by name.
        
        Args:
            path_name: Name of the path to retrieve
            
        Returns:
            Path object for the requested path
            
        Raises:
            KeyError: If the path name doesn't exist
        """
        if path_name not in self._paths:
            raise KeyError(f"Path '{path_name}' not found. Available paths: {list(self._paths.keys())}")
        
        return self._paths[path_name]
    
    def get_path_str(self, path_name: str) -> str:
        """
        Get a specific path as a string.
        
        Args:
            path_name: Name of the path to retrieve
            
        Returns:
            String representation of the path
            
        Raises:
            KeyError: If the path name doesn't exist
        """
        return str(self.get_path(path_name))
    
    def exists(self, path_name: str) -> bool:
        """
        Check if a path exists.
        
        Args:
            path_name: Name of the path to check
            
        Returns:
            True if the path exists, False otherwise
        """
        try:
            return self.get_path(path_name).exists()
        except KeyError:
            return False
    
    def ensure_executable(self, path_name: str) -> None:
        """
        Ensure a file is executable.
        
        Args:
            path_name: Name of the path to make executable
            
        Raises:
            FileNotFoundError: If the file doesn't exist
            KeyError: If the path name doesn't exist
        """
        file_path = self.get_path(path_name)
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        # Make the file executable
        file_path.chmod(0o755)
    
    def list_paths(self) -> Dict[str, str]:
        """
        Get a dictionary of all available paths.
        
        Returns:
            Dictionary mapping path names to their string representations
        """
        return {name: str(path) for name, path in self._paths.items()}
    
    def get_package_root(self) -> Path:
        """
        Get the package root directory.
        
        Returns:
            Path to the package root
        """
        return self._package_root


# Global instance for easy access
_path_config = None


def get_path_config() -> PathConfig:
    """
    Get the global path configuration instance.
    
    Returns:
        PathConfig instance
    """
    global _path_config
    if _path_config is None:
        _path_config = PathConfig()
    return _path_config


def get_path(path_name: str) -> Path:
    """
    Get a specific path by name.
    
    Args:
        path_name: Name of the path to retrieve
        
    Returns:
        Path object for the requested path
    """
    return get_path_config().get_path(path_name)


def get_path_str(path_name: str) -> str:
    """
    Get a specific path as a string.
    
    Args:
        path_name: Name of the path to retrieve
        
    Returns:
        String representation of the path
    """
    return get_path_config().get_path_str(path_name)


def path_exists(path_name: str) -> bool:
    """
    Check if a path exists.
    
    Args:
        path_name: Name of the path to check
        
    Returns:
        True if the path exists, False otherwise
    """
    return get_path_config().exists(path_name)


def ensure_executable(path_name: str) -> None:
    """
    Ensure a file is executable.
    
    Args:
        path_name: Name of the path to make executable
    """
    get_path_config().ensure_executable(path_name)


def list_all_paths() -> Dict[str, str]:
    """
    Get a dictionary of all available paths.
    
    Returns:
        Dictionary mapping path names to their string representations
    """
    return get_path_config().list_paths()
