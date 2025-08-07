#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Extract Individual Cells Script for Single Cell Analysis Workflow

This script uses ROIs to extract individual cells from the original images
and saves them as separate files in the cells directory.

This version uses a dedicated macro file with parameter passing instead of 
creating permanent temporary macro files.
"""

import os
import sys
import argparse
import subprocess
import logging
import tempfile
import time
import re
from pathlib import Path

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stdout  # Ensure logging goes to stdout for visibility
)
logger = logging.getLogger("CellExtractor")

def create_macro_with_parameters(macro_template_file, roi_file, image_file, output_dir, auto_close=False):
    """
    Create a temporary macro file with parameters embedded from the dedicated macro template.
    
    Args:
        macro_template_file (str): Path to the dedicated macro template file
        roi_file (str): Path to the ROI file
        image_file (str): Path to the raw image file
        output_dir (str): Directory to save extracted cell images
        auto_close (bool): Whether to add auto-close functionality
        
    Returns:
        str: Path to the created temporary macro file
    """
    try:
        # Read the dedicated macro template
        with open(macro_template_file, 'r') as f:
            template_content = f.read()
        
        # Remove the #@ parameter declarations since we're embedding the values
        lines = template_content.split('\n')
        filtered_lines = []
        for line in lines:
            if not line.strip().startswith('#@'):
                filtered_lines.append(line)
        
        # Ensure paths use forward slashes for ImageJ
        roi_file_path = str(roi_file).replace('\\', '/')
        image_file_path = str(image_file).replace('\\', '/')
        output_dir_path = str(output_dir).replace('\\', '/')
        
        # Add parameter definitions at the beginning
        parameter_definitions = f"""
// Parameters embedded from Python script
roi_file = "{roi_file_path}";
image_file = "{image_file_path}";
output_dir = "{output_dir_path}";
auto_close = {str(auto_close).lower()};
"""
        
        # Combine parameters with the filtered template content
        macro_content = parameter_definitions + '\n'.join(filtered_lines)
        
        # Create temporary macro file
        temp_macro = tempfile.NamedTemporaryFile(mode='w', suffix='.ijm', delete=False)
        temp_macro.write(macro_content)
        temp_macro.close()
        
        logger.info(f"Created temporary macro file: {temp_macro.name}")
        return temp_macro.name
        
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
        # Use -macro instead of --headless --run to avoid ROI Manager headless issues
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
    Check if the dedicated macro file exists and is readable.
    
    Args:
        macro_file (str): Path to the macro file
        
    Returns:
        bool: True if macro file is accessible, False otherwise
    """
    macro_path = Path(macro_file)
    
    if not macro_path.exists():
        logger.error(f"Macro file does not exist: {macro_file}")
        return False
    
    if not macro_path.is_file():
        logger.error(f"Macro path is not a file: {macro_file}")
        return False
    
    try:
        with open(macro_path, 'r') as f:
            content = f.read()
            # Check if it contains the expected parameter declarations
            if '#@ String roi_file' not in content:
                logger.warning(f"Macro file may not be compatible - missing roi_file parameter")
            if '#@ String image_file' not in content:
                logger.warning(f"Macro file may not be compatible - missing image_file parameter")
            if '#@ String output_dir' not in content:
                logger.warning(f"Macro file may not be compatible - missing output_dir parameter")
        
        logger.info(f"Macro file validated: {macro_file}")
        return True
        
    except Exception as e:
        logger.error(f"Cannot read macro file {macro_file}: {e}")
        return False

def find_image_for_roi(roi_file, raw_data_dir):
    """
    Find the corresponding image file for a ROI file.
    
    Args:
        roi_file: Path to the ROI file
        raw_data_dir: Directory containing raw data
        
    Returns:
        Path to the corresponding image file, or None if not found
    """
    # Extract metadata from ROI filename
    roi_path = Path(roi_file)
    roi_filename = roi_path.name
    
    # Get the condition from the parent directory
    condition = roi_path.parent.name
    condition_dir = Path(raw_data_dir) / condition
    
    logger.info(f"Looking for image file for ROI: {roi_filename}")
    logger.info(f"Condition: {condition}")
    
    # Parse ROI filename to extract components
    # Example: ROIs_R_1_Merged_ch01_t00_rois.zip
    
    # Remove the ROIs_ prefix and _rois.zip suffix
    cleaned_name = roi_filename
    if cleaned_name.startswith("ROIs_"):
        cleaned_name = cleaned_name[5:]  # Remove "ROIs_"
    
    if cleaned_name.endswith("_rois.zip"):
        cleaned_name = cleaned_name[:-9]  # Remove "_rois.zip"
    elif cleaned_name.endswith(".zip"):
        cleaned_name = cleaned_name[:-4]  # Remove ".zip"
    
    logger.info(f"Cleaned ROI name: {cleaned_name}")
    
    # Extract components using regex
    channel_match = re.search(r'_(ch\d+)_', cleaned_name)
    timepoint_match = re.search(r'_(t\d+)(?:_|$)', cleaned_name)
    
    # Default to empty strings if not found
    channel = channel_match.group(1) if channel_match else ""
    timepoint = timepoint_match.group(1) if timepoint_match else ""
    
    # The region is the remaining part of the name
    # For example, if cleaned_name is "R_1_Merged_ch01_t00", 
    # and we remove "_ch01_t00", we get "R_1_Merged"
    region = cleaned_name
    if channel:
        region = region.replace(f"_{channel}", "")
    if timepoint:
        region = region.replace(f"_{timepoint}", "")
    
    # Clean up any trailing underscores
    region = region.rstrip("_")
    
    logger.info(f"Extracted components - Region: {region}, Channel: {channel}, Timepoint: {timepoint}")
    
    # Use the extracted components to find the image file
    # Look in all subdirectories of the condition directory
    image_pattern = f"{region}_{channel}_{timepoint}.tif"
    logger.info(f"Looking for image file matching pattern: {image_pattern}")
    
    # Use recursive glob to find the file
    possible_files = list(condition_dir.glob(f"**/{image_pattern}"))
    
    if possible_files:
        logger.info(f"Found matching image file: {possible_files[0]}")
        return possible_files[0]
    
    # If not found with the pattern, search more broadly
    logger.warning(f"No exact match found, trying more flexible search")
    
    # Try partial matches based on region, channel, and timepoint
    for subdir in condition_dir.glob("**"):
        if subdir.is_dir():
            logger.debug(f"Searching in subdirectory: {subdir}")
            
            # Look for files matching parts of the pattern
            for file in subdir.glob("*.tif"):
                filename = file.name
                
                # Check if the filename contains all the extracted components
                matches_region = region in filename
                matches_channel = channel in filename if channel else True
                matches_timepoint = timepoint in filename if timepoint else True
                
                if matches_region and matches_channel and matches_timepoint:
                    logger.info(f"Found partial match: {file}")
                    return file
    
    logger.error(f"No matching image file found for ROI: {roi_filename}")
    return None

def create_output_dir_for_roi(roi_file, output_base_dir):
    """
    Create an appropriate output directory structure for extracted cells.
    
    Args:
        roi_file: Path to the ROI file
        output_base_dir: Base directory for outputs
        
    Returns:
        Path to the output directory for cells
    """
    # Extract metadata from ROI filename
    roi_path = Path(roi_file)
    roi_filename = roi_path.name
    
    # Get the condition from the parent directory
    condition = roi_path.parent.name
    
    # Extract components from the ROI filename
    # Example: ROIs_R_1_Merged_ch01_t00_rois.zip
    
    # Remove the ROIs_ prefix and _rois.zip suffix
    cleaned_name = roi_filename
    if cleaned_name.startswith("ROIs_"):
        cleaned_name = cleaned_name[5:]  # Remove "ROIs_"
    
    if cleaned_name.endswith("_rois.zip"):
        cleaned_name = cleaned_name[:-9]  # Remove "_rois.zip"
    elif cleaned_name.endswith(".zip"):
        cleaned_name = cleaned_name[:-4]  # Remove ".zip"
    
    # Extract components using regex
    channel_match = re.search(r'_(ch\d+)_', cleaned_name)
    timepoint_match = re.search(r'_(t\d+)(?:_|$)', cleaned_name)
    
    # Default to empty strings if not found
    channel = channel_match.group(1) if channel_match else ""
    timepoint = timepoint_match.group(1) if timepoint_match else ""
    
    # Remove channel and timepoint parts to get the region
    region = cleaned_name
    if channel:
        region = region.replace(f"_{channel}", "")
    if timepoint:
        region = region.replace(f"_{timepoint}", "")
    
    # Clean up any trailing underscores
    region = region.rstrip("_")
    
    # Create the output directory structure
    # Format: output_base_dir/condition/region_channel_timepoint
    output_dir = Path(output_base_dir) / condition / f"{region}_{channel}_{timepoint}"
    os.makedirs(output_dir, exist_ok=True)
    
    logger.info(f"Created output directory: {output_dir}")
    return output_dir

def main():
    """Main function to extract individual cells."""
    parser = argparse.ArgumentParser(description='Extract individual cells using ROIs with dedicated macro')
    
    parser.add_argument('--roi-dir', '-i', required=True,
                        help='Directory containing ROI files')
    parser.add_argument('--raw-data-dir', '-d', required=True,
                        help='Directory containing original images')
    parser.add_argument('--output-dir', '-o', required=True,
                        help='Directory where individual cells will be saved')
    parser.add_argument('--imagej', required=True,
                        help='Path to ImageJ executable')
    parser.add_argument('--macro', default='src/macros/extract_cells.ijm',
                       help='Path to the dedicated ImageJ macro file (default: src/macros/extract_cells.ijm)')
    parser.add_argument('--regions', '-r', nargs='+',
                        help='List of regions to process')
    parser.add_argument('--timepoints', '-t', nargs='+',
                        help='List of timepoints to process')
    parser.add_argument('--conditions', '-c', nargs='+',
                        help='List of conditions to process')
    parser.add_argument('--auto-close', action='store_true',
                        help='Close ImageJ when the macro completes')
    parser.add_argument('--verbose', '-v', action='store_true',
                        help='Enable more verbose logging')
    parser.add_argument('--channels', nargs='+', help='Channels to process')
    
    args = parser.parse_args()
    
    # Set logging level based on verbose flag
    if args.verbose:
        logger.setLevel(logging.DEBUG)
        logger.debug("Verbose logging enabled")
    
    # Create output directory if it doesn't exist
    os.makedirs(args.output_dir, exist_ok=True)
    
    # Check macro file
    if not check_macro_file(args.macro):
        logger.error("Macro file validation failed")
        return 1
    
    # Find all ROI files in the ROI directory
    roi_dir = Path(args.roi_dir)
    if not roi_dir.exists():
        logger.error(f"ROI directory does not exist: {roi_dir}")
        return 1
    
    # Find all ROI files in all subdirectories of the ROI directory
    roi_files = []
    
    # Check what's in the ROI directory
    logger.info(f"ROI directory contents:")
    for condition_dir in roi_dir.glob("*"):
        if condition_dir.is_dir() and not condition_dir.name.startswith('.'):
            logger.info(f"  Directory: {condition_dir.name}")
            # Check for ROI files in this condition directory
            condition_roi_files = list(condition_dir.glob("*.zip"))
            logger.info(f"    Found {len(condition_roi_files)} ROI files in {condition_dir.name}")
            
            # Filter ROI files based on regions if specified
            if args.regions:
                filtered_roi_files = []
                for roi_file in condition_roi_files:
                    roi_name = roi_file.name
                    for region in args.regions:
                        if region in roi_name:
                            filtered_roi_files.append(roi_file)
                            break
                condition_roi_files = filtered_roi_files
                
            # Filter ROI files based on timepoints if specified
            if args.timepoints:
                filtered_roi_files = []
                for roi_file in condition_roi_files:
                    roi_name = roi_file.name
                    for timepoint in args.timepoints:
                        if timepoint in roi_name:
                            filtered_roi_files.append(roi_file)
                            break
                condition_roi_files = filtered_roi_files
            
            # Add the filtered ROI files to our list
            roi_files.extend(condition_roi_files)
    
    # Filter by conditions if specified
    if args.conditions:
        filtered_roi_files = []
        for roi_file in roi_files:
            condition = roi_file.parent.name
            if condition in args.conditions:
                filtered_roi_files.append(roi_file)
        roi_files = filtered_roi_files
    
    if not roi_files:
        logger.error(f"No ROI files found in {roi_dir}")
        return 1
    
    logger.info(f"Found {len(roi_files)} ROI files to process")
    
    # Process each ROI file
    successful_extractions = 0
    total_cells_extracted = 0
    
    for roi_file in roi_files:
        # Skip if channels are specified and this file doesn't match any of them
        if args.channels:
            file_channels = [ch for ch in args.channels if ch in str(roi_file)]
            if not file_channels:
                logger.info(f"Skipping {roi_file} - no matching channels")
                continue
            logger.info(f"Processing channels {file_channels} for {roi_file}")
        
        logger.info(f"Processing ROI file: {roi_file}")
        
        # Find the corresponding image file
        image_file = find_image_for_roi(roi_file, args.raw_data_dir)
        
        if image_file:
            # Create output directory for this ROI
            cell_output_dir = create_output_dir_for_roi(roi_file, args.output_dir)
            
            # Create temporary macro with embedded parameters
            logger.info("Creating macro with embedded parameters...")
            temp_macro_file = create_macro_with_parameters(
                args.macro,
                roi_file,
                image_file,
                cell_output_dir,
                args.auto_close
            )
            
            if not temp_macro_file:
                logger.error("Failed to create macro with parameters")
                continue
            
            try:
                # Run the ImageJ macro
                logger.info("Starting cell extraction process...")
                success = run_imagej_macro(args.imagej, temp_macro_file, args.auto_close)
                
                if success:
                    # Check if cells were actually extracted
                    cell_files = list(cell_output_dir.glob("CELL*.tif"))
                    if cell_files:
                        logger.info(f"Successfully extracted {len(cell_files)} cells to {cell_output_dir}")
                        successful_extractions += 1
                        total_cells_extracted += len(cell_files)
                    else:
                        logger.warning(f"No cell files were created in {cell_output_dir}")
                else:
                    logger.error("Cell extraction failed")
            
            finally:
                # Clean up temporary macro file
                try:
                    os.unlink(temp_macro_file)
                    logger.debug(f"Cleaned up temporary macro file: {temp_macro_file}")
                except Exception as e:
                    logger.warning(f"Could not clean up temporary macro file {temp_macro_file}: {e}")
        else:
            logger.error(f"Could not find matching image file for {roi_file}")
    
    logger.info(f"Cell extraction completed. Successfully processed {successful_extractions} of {len(roi_files)} ROI files.")
    logger.info(f"Total cells extracted: {total_cells_extracted}")
    
    return 0 if successful_extractions > 0 else 1

if __name__ == "__main__":
    sys.exit(main())