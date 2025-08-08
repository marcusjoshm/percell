#!/usr/bin/env python3
"""
Test script for the centralized path configuration system.
"""

import sys
from pathlib import Path

# Add the percell package to the path
sys.path.insert(0, str(Path(__file__).parent.parent))

from percell.core.paths import get_path_config, get_path, get_path_str, path_exists, list_all_paths

def test_path_system():
    """Test the centralized path system."""
    print("Testing centralized path configuration system...")
    print("=" * 60)
    
    # Get the path configuration
    config = get_path_config()
    print(f"Package root: {config.get_package_root()}")
    print()
    
    # Test some key paths
    key_paths = [
        "setup_output_structure_script",
        "prepare_input_structure_script", 
        "launch_segmentation_tools_script",
        "bin_images_module",
        "config_default",
        "create_cell_masks_macro"
    ]
    
    print("Testing key paths:")
    for path_name in key_paths:
        try:
            path = get_path(path_name)
            exists = path_exists(path_name)
            print(f"  {path_name}: {path} {'✓' if exists else '✗'}")
        except Exception as e:
            print(f"  {path_name}: ERROR - {e}")
    
    print()
    print("All available paths:")
    all_paths = list_all_paths()
    for name, path_str in all_paths.items():
        print(f"  {name}: {path_str}")
    
    print()
    print("Path system test completed!")

if __name__ == "__main__":
    test_path_system()
