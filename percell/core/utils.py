"""
Utility functions for the Microscopy Single-Cell Analysis Pipeline

This module provides utility functions for common operations like
locating package resources, path handling, and other helper functions.
"""

import os
import sys
from pathlib import Path
from typing import Optional


def get_package_root() -> Path:
    """
    Get the root directory of the percell package.
    
    Returns:
        Path to the package root directory
    """
    # Try to find the package root by looking for the percell directory
    # that contains the bash, config, macros, etc. subdirectories
    
    # First, try to get it from the current module's location
    current_file = Path(__file__)
    package_root = current_file.parent.parent  # Go up from core/utils.py to percell/
    
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


def get_package_resource(relative_path: str) -> Path:
    """
    Get the absolute path to a package resource.
    
    Args:
        relative_path: Relative path from the package root (e.g., 'bash/setup_output_structure.sh')
        
    Returns:
        Absolute path to the resource
        
    Raises:
        FileNotFoundError: If the resource doesn't exist
    """
    package_root = get_package_root()
    resource_path = package_root / relative_path
    
    if not resource_path.exists():
        raise FileNotFoundError(f"Package resource not found: {relative_path} (searched in {package_root})")
    
    return resource_path


def get_bash_script(script_name: str) -> Path:
    """
    Get the absolute path to a bash script in the package.
    
    Args:
        script_name: Name of the bash script (e.g., 'setup_output_structure.sh')
        
    Returns:
        Absolute path to the bash script
        
    Raises:
        FileNotFoundError: If the script doesn't exist
    """
    return get_package_resource(f"bash/{script_name}")


def get_config_file(config_name: str) -> Path:
    """
    Get the absolute path to a config file in the package.
    
    Args:
        config_name: Name of the config file (e.g., 'config.json')
        
    Returns:
        Absolute path to the config file
        
    Raises:
        FileNotFoundError: If the config file doesn't exist
    """
    return get_package_resource(f"config/{config_name}")


def get_macro_file(macro_name: str) -> Path:
    """
    Get the absolute path to a macro file in the package.
    
    Args:
        macro_name: Name of the macro file (e.g., 'create_cell_masks.ijm')
        
    Returns:
        Absolute path to the macro file
        
    Raises:
        FileNotFoundError: If the macro file doesn't exist
    """
    return get_package_resource(f"macros/{macro_name}")


def ensure_executable(file_path: Path) -> None:
    """
    Ensure a file is executable.
    
    Args:
        file_path: Path to the file to make executable
    """
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    
    # Make the file executable
    file_path.chmod(0o755)


def find_package_root_from_script() -> Optional[Path]:
    """
    Find the package root when running from a script.
    This is useful for finding the package root when the command is run from anywhere.
    
    Returns:
        Path to the package root, or None if not found
    """
    # Get the path to the percell command that was executed
    if len(sys.argv) > 0:
        script_path = Path(sys.argv[0]).resolve()
        
        # If it's a symbolic link, follow it
        if script_path.is_symlink():
            script_path = script_path.readlink()
        
        # Look for the package root in the directory containing the script
        # The script should be in venv/bin/percell, so we need to go up to find the package
        current = script_path.parent  # bin/
        current = current.parent      # venv/
        current = current.parent      # percell project root
        
        # Check if this looks like the package root
        if current.exists() and (current / 'percell').exists():
            return current / 'percell'
    
    return None
