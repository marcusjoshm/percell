#!/usr/bin/env python3
"""
Measure ROI Area Module for Microscopy Single-Cell Analysis Pipeline

This module opens ROI lists and corresponding raw data files, then measures ROI areas
using ImageJ. Results are saved as CSV files in the analysis folder.
"""

import os
import tempfile
import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# Setup module logger
import logging
logger = logging.getLogger(__name__)


def create_macro_with_parameters(macro_template_file, roi_file, image_file, csv_file, auto_close=False):
    """
    Create a dedicated ImageJ macro file with specific parameters.
    
    Args:
        macro_template_file (str): Path to the macro template file
        roi_file (str): Path to the ROI file (.zip or .roi)
        image_file (str): Path to the raw image file
        csv_file (str): Path to output CSV file
        auto_close (bool): Whether the macro should automatically close ImageJ
        
    Returns:
        str: Path to the created macro file, or None if error
    """
    try:
        # Validate inputs
        if not os.path.exists(macro_template_file):
            logger.error(f"Macro template file not found: {macro_template_file}")
            return None
            
        if not os.path.exists(roi_file):
            logger.error(f"ROI file not found: {roi_file}")
            return None
            
        if not os.path.exists(image_file):
            logger.error(f"Image file not found: {image_file}")
            return None
        
        # Ensure output directory exists
        os.makedirs(os.path.dirname(csv_file), exist_ok=True)
        
        # Read the macro template
        with open(macro_template_file, 'r') as f:
            macro_content = f.read()
        
        # Replace the macro content with actual parameter values
        # Convert paths to forward slashes for ImageJ compatibility
        roi_file_clean = roi_file.replace(os.sep, '/')
        image_file_clean = image_file.replace(os.sep, '/')
        csv_file_clean = csv_file.replace(os.sep, '/')
        auto_close_str = str(auto_close).lower()
        
        # Replace the parameter declarations with actual assignments
        final_macro = macro_content.replace(
            '#@ String roi_file', f'roi_file = "{roi_file_clean}";'
        ).replace(
            '#@ String image_file', f'image_file = "{image_file_clean}";'
        ).replace(
            '#@ String csv_file', f'csv_file = "{csv_file_clean}";'
        ).replace(
            '#@ Boolean auto_close', f'auto_close = {auto_close_str};'
        )
        
        # Create temporary macro file
        temp_dir = tempfile.gettempdir()
        temp_macro_file = os.path.join(temp_dir, f"measure_roi_area_{os.getpid()}.ijm")
        
        with open(temp_macro_file, 'w') as f:
            f.write(final_macro)
        
        logger.info(f"Created macro file: {temp_macro_file}")
        logger.info(f"  ROI file: {roi_file}")
        logger.info(f"  Image file: {image_file}")
        logger.info(f"  CSV file: {csv_file}")
        logger.info(f"  Auto close: {auto_close}")
        
        return temp_macro_file
        
    except Exception as e:
        logger.error(f"Error creating macro with parameters: {e}")
        return None


def run_imagej_macro(imagej_path, macro_file, auto_close=False):
    """
    Run ImageJ with the dedicated macro using -macro mode.
    
    Args:
        imagej_path (str): Path to the ImageJ executable
        macro_file (str): Path to the dedicated ImageJ macro file
        auto_close (bool): Whether the macro will automatically close ImageJ
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Use -macro mode for user interaction
        cmd = [imagej_path, '-macro', str(macro_file)]
        
        logger.info(f"Running ImageJ command: {' '.join(cmd)}")
        logger.info(f"ImageJ will {'auto-close' if auto_close else 'remain open'} after execution")
        
        result = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=False  # Don't raise an exception on non-zero return code
        )
        
        # Log the output
        if result.stdout:
            logger.info("ImageJ output:")
            for line in result.stdout.splitlines():
                logger.info(f"  {line}")
        
        if result.stderr:
            logger.warning("ImageJ errors:")
            for line in result.stderr.splitlines():
                logger.warning(f"  {line}")
        
        # Check if the command executed successfully
        if result.returncode != 0:
            logger.error(f"ImageJ returned non-zero exit code: {result.returncode}")
            return False
        
        return True
        
    except Exception as e:
        logger.error(f"Error running ImageJ: {e}")
        return False


def check_macro_file(macro_file):
    """
    Check if the macro file exists and is readable.
    
    Args:
        macro_file (str): Path to the macro file
        
    Returns:
        bool: True if file is valid, False otherwise
    """
    if not os.path.exists(macro_file):
        logger.error(f"Macro file does not exist: {macro_file}")
        return False
    
    try:
        with open(macro_file, 'r') as f:
            content = f.read()
        if len(content.strip()) == 0:
            logger.error(f"Macro file is empty: {macro_file}")
            return False
        logger.info(f"Macro file validated: {macro_file}")
        return True
    except Exception as e:
        logger.error(f"Error reading macro file {macro_file}: {e}")
        return False


def validate_inputs(roi_file, image_file, output_dir):
    """
    Validate input files and directories.
    
    Args:
        roi_file (str): Path to ROI file
        image_file (str): Path to image file
        output_dir (str): Path to output directory
        
    Returns:
        bool: True if all inputs are valid, False otherwise
    """
    # Check ROI file
    if not os.path.exists(roi_file):
        logger.error(f"ROI file does not exist: {roi_file}")
        return False
    
    # Check image file
    if not os.path.exists(image_file):
        logger.error(f"Image file does not exist: {image_file}")
        return False
    
    # Check/create output directory
    try:
        os.makedirs(output_dir, exist_ok=True)
        logger.info(f"Output directory validated/created: {output_dir}")
        return True
    except Exception as e:
        logger.error(f"Cannot create output directory {output_dir}: {e}")
        return False


def find_roi_image_pairs(input_dir, output_dir):
    """
    Find matching ROI and image file pairs for measurement.
    
    Args:
        input_dir (str): Input directory containing data
        output_dir (str): Output directory with processed data
        
    Returns:
        List[Tuple[str, str, str]]: List of (roi_file, image_file, csv_file) tuples
    """
    pairs = []
    
    try:
        input_path = Path(input_dir)
        output_path = Path(output_dir)
        
        # Look for ROI files in the output structure
        roi_pattern = "**/*.zip"  # ROI Manager saves as .zip files
        roi_files = list(output_path.glob(roi_pattern))
        
        logger.info(f"Found {len(roi_files)} ROI files in output directory")
        
        for roi_file in roi_files:
            logger.info(f"Processing ROI file: {roi_file}")
            
            # Extract the base filename from ROI file
            roi_name = roi_file.name
            
            # Handle different ROI naming patterns
            if roi_name.startswith("ROIs_") and roi_name.endswith("_rois.zip"):
                # Remove "ROIs_" prefix and "_rois.zip" suffix
                base_name = roi_name[5:-9]  # Remove "ROIs_" and "_rois.zip"
            elif roi_name.endswith("_rois.zip"):
                # Remove "_rois.zip" suffix
                base_name = roi_name[:-9]
            elif roi_name.endswith(".zip"):
                # Remove ".zip" suffix
                base_name = roi_name[:-4]
            else:
                logger.warning(f"Unrecognized ROI file pattern: {roi_name}")
                continue
            
            logger.info(f"Extracted base name: {base_name}")
            
            # Search for corresponding image files in input directory
            found_match = False
            
            # Search recursively in input directory for matching image files
            for img_ext in ['.tif', '.tiff', '.png', '.jpg']:
                # Try different matching patterns
                search_patterns = [
                    f"**/{base_name}{img_ext}",  # Exact match
                    f"**/*{base_name}*{img_ext}",  # Contains base name
                ]
                
                for pattern in search_patterns:
                    matching_images = list(input_path.glob(pattern))
                    
                    for potential_image in matching_images:
                        # Create output CSV file path with condition and "cell_area" in the filename
                        # Extract condition from ROI file path, same as analyze_cell_masks.py
                        # ROI path structure: output_dir/ROIs/condition/ROI_file.zip
                        roi_path = Path(roi_file)
                        condition_name = roi_path.parent.name  # Get the condition directory name (parent of ROI file)
                        
                        # Extract the ROI directory name from the ROI filename (like mask directory name)
                        roi_name = roi_file.stem  # Get filename without extension
                        # Remove "ROIs_" prefix and "_rois" suffix to get the directory name
                        if roi_name.startswith("ROIs_"):
                            roi_dir_name = roi_name[5:]  # Remove "ROIs_" prefix
                        else:
                            roi_dir_name = roi_name
                        
                        if roi_dir_name.endswith("_rois"):
                            roi_dir_name = roi_dir_name[:-5]  # Remove "_rois" suffix
                        
                        # Create filename with condition and ROI directory name
                        csv_filename = f"{condition_name}_{roi_dir_name}_cell_area.csv"
                        csv_file = output_path / "analysis" / csv_filename
                        csv_file.parent.mkdir(parents=True, exist_ok=True)
                        
                        pairs.append((str(roi_file), str(potential_image), str(csv_file)))
                        logger.info(f"Found pair: ROI={roi_file.name}, Image={potential_image.name}")
                        found_match = True
                        break
                    
                    if found_match:
                        break
                
                if found_match:
                    break
            
            if not found_match:
                logger.warning(f"No matching image found for ROI file: {roi_name}")
        
        logger.info(f"Found {len(pairs)} ROI-image pairs for measurement")
        return pairs
        
    except Exception as e:
        logger.error(f"Error finding ROI-image pairs: {e}")
        return []


def measure_roi_areas(input_dir, output_dir, imagej_path, auto_close=True):
    """
    Main function to measure ROI areas for all found pairs.
    
    Args:
        input_dir (str): Input directory containing raw data
        output_dir (str): Output directory containing processed data
        imagej_path (str): Path to ImageJ executable
        auto_close (bool): Whether to auto-close ImageJ after each measurement
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        logger.info("Starting ROI area measurement...")
        
        # Find ROI-image pairs
        pairs = find_roi_image_pairs(input_dir, output_dir)
        
        if not pairs:
            logger.warning("No ROI-image pairs found for measurement")
            return True  # Not an error, just nothing to do
        
        # Get macro template path
        macro_template = Path(__file__).parent.parent.parent / "macros" / "measure_roi_area.ijm"
        
        if not macro_template.exists():
            logger.error(f"Macro template not found: {macro_template}")
            return False
        
        success_count = 0
        total_count = len(pairs)
        
        for roi_file, image_file, csv_file in pairs:
            logger.info(f"Processing pair {success_count + 1}/{total_count}")
            logger.info(f"  ROI: {roi_file}")
            logger.info(f"  Image: {image_file}")
            logger.info(f"  Output: {csv_file}")
            
            # Create macro with parameters
            macro_file = create_macro_with_parameters(
                str(macro_template), roi_file, image_file, csv_file, auto_close
            )
            
            if not macro_file:
                logger.error(f"Failed to create macro for {roi_file}")
                continue
            
            try:
                # Run ImageJ macro
                if run_imagej_macro(imagej_path, macro_file, auto_close):
                    if os.path.exists(csv_file):
                        logger.info(f"Successfully measured ROIs: {csv_file}")
                        success_count += 1
                    else:
                        logger.warning(f"Macro completed but CSV file not found: {csv_file}")
                else:
                    logger.error(f"Failed to run ImageJ macro for {roi_file}")
                
            finally:
                # Clean up temporary macro file
                try:
                    os.remove(macro_file)
                except Exception as e:
                    logger.warning(f"Could not remove temporary macro file: {e}")
        
        logger.info(f"ROI area measurement completed: {success_count}/{total_count} successful")
        return success_count > 0
        
    except Exception as e:
        logger.error(f"Error in measure_roi_areas: {e}")
        return False


if __name__ == "__main__":
    # For testing purposes
    import sys
    
    if len(sys.argv) != 4:
        print("Usage: python measure_roi_area.py <input_dir> <output_dir> <imagej_path>")
        sys.exit(1)
    
    input_dir = sys.argv[1]
    output_dir = sys.argv[2]
    imagej_path = sys.argv[3]
    
    # Setup basic logging
    logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
    
    success = measure_roi_areas(input_dir, output_dir, imagej_path)
    sys.exit(0 if success else 1)