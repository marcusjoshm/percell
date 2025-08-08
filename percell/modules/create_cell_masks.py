#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Create Cell Masks Script for Single Cell Analysis Workflow

This script generates an ImageJ macro to create individual cell masks by applying ROIs
to the combined mask images. It processes ROIs from the ROIs directory and combined
masks from the combined_masks directory, saving individual cell masks to the masks directory.

This version uses a dedicated macro file with parameter passing instead of 
creating permanent macro files with hardcoded paths.
"""

import os
import sys
import argparse
import subprocess
import logging
import re
from pathlib import Path
import time
import glob
import numpy as np
import cv2
import tempfile
import shutil

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("CellMaskCreator")

def find_matching_mask_for_roi(roi_file, mask_dir):
    """
    Find the corresponding mask file for a ROI file.
    
    Args:
        roi_file (Path): Path to the ROI file
        mask_dir (Path): Directory containing mask files
    
    Returns:
        Path: Path to the matching mask file, or None if not found
    """
    # Extract metadata from ROI filename
    roi_path = Path(roi_file)
    roi_filename = roi_path.name
    
    # Get the condition from the parent directory
    condition = roi_path.parent.name
    condition_mask_dir = Path(mask_dir) / condition
    
    if not condition_mask_dir.exists():
        logger.warning(f"Condition directory not found in mask dir: {condition_mask_dir}")
        return None
    
    # Parse ROI filename to extract components
    # Example: ROIs_A549 Control_Merged_Processed001_ch00_t00_rois.zip
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
    
    # The region is the remaining part of the name
    region = cleaned_name
    if channel:
        region = region.replace(f"_{channel}", "")
    if timepoint:
        region = region.replace(f"_{timepoint}", "")
    
    # Clean up any trailing underscores
    region = region.rstrip("_")
    
    logger.info(f"Extracted components - Region: {region}, Channel: {channel}, Timepoint: {timepoint}")
    
    # Look for channel-specific mask files in the condition directory
    # Pattern: MASK_{region}_{channel}_{timepoint}.tif
    mask_pattern = f"MASK_{region}_{channel}_{timepoint}.tif"
    logger.info(f"Looking for mask file matching pattern: {mask_pattern}")
    
    mask_files = list(condition_mask_dir.glob(mask_pattern))
    if mask_files:
        logger.info(f"Found matching mask file: {mask_files[0]}")
        return mask_files[0]
    
    # Try with .tiff extension
    mask_pattern = f"MASK_{region}_{channel}_{timepoint}.tiff"
    mask_files = list(condition_mask_dir.glob(mask_pattern))
    if mask_files:
        logger.info(f"Found matching mask file: {mask_files[0]}")
        return mask_files[0]
    
    # Try more flexible search for this channel
    mask_files = list(condition_mask_dir.glob(f"MASK_{region}_{channel}_*.tif"))
    if mask_files:
        logger.info(f"Found matching mask file: {mask_files[0]}")
        return mask_files[0]
    
    # Try even more flexible search for this specific channel
    mask_files = list(condition_mask_dir.glob(f"MASK_*{channel}*.tif"))
    if mask_files:
        logger.info(f"Found potential mask file: {mask_files[0]}")
        return mask_files[0]
    
    logger.warning(f"No matching mask file found for ROI: {roi_file}")
    return None

def create_output_dir_for_roi(roi_file, output_base_dir):
    """
    Create an appropriate output directory structure for cell masks.
    
    Args:
        roi_file (Path): Path to the ROI file
        output_base_dir (Path): Base directory for outputs
        
    Returns:
        Path: Path to the output directory for cell masks
    """
    # Extract metadata from ROI filename
    roi_path = Path(roi_file)
    roi_filename = roi_path.name
    
    # Get the condition from the parent directory
    condition = roi_path.parent.name
    
    # Parse ROI filename to extract components
    # Example: ROIs_A549 Control_Merged_Processed001_ch00_t00_rois.zip
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
    
    # The region is the remaining part of the name
    region = cleaned_name
    if channel:
        region = region.replace(f"_{channel}", "")
    if timepoint:
        region = region.replace(f"_{timepoint}", "")
    
    # Clean up any trailing underscores
    region = region.rstrip("_")
    
    # Create the output directory structure with channel-specific organization
    # Format: output_base_dir/condition/region_channel_timepoint
    output_dir = Path(output_base_dir) / condition / f"{region}_{channel}_{timepoint}"
    os.makedirs(output_dir, exist_ok=True)
    
    logger.info(f"Created output directory: {output_dir}")
    return output_dir

def create_macro_with_parameters(macro_template_file, roi_file, mask_file, output_dir, auto_close=False):
    """
    Create a temporary macro file with parameters embedded from the dedicated macro template.
    
    Args:
        macro_template_file (str): Path to the dedicated macro template file
        roi_file (str): Path to the ROI file
        mask_file (str): Path to the mask file
        output_dir (str): Output directory for individual cell masks
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
        mask_file_path = str(mask_file).replace('\\', '/')
        output_dir_path = str(output_dir).replace('\\', '/')
        
        # Add parameter definitions at the beginning
        parameter_definitions = f"""
// Parameters embedded from Python script
roi_file = "{roi_file_path}";
mask_file = "{mask_file_path}";
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
            if '#@ String mask_file' not in content:
                logger.warning(f"Macro file may not be compatible - missing mask_file parameter")
            if '#@ String output_dir' not in content:
                logger.warning(f"Macro file may not be compatible - missing output_dir parameter")
        
        logger.info(f"Macro file validated: {macro_file}")
        return True
        
    except Exception as e:
        logger.error(f"Cannot read macro file {macro_file}: {e}")
        return False

def create_mask_macro(roi_dir, mask_dir, output_dir, imagej_path, auto_close=True):
    """
    Create ImageJ macro for creating cell masks.
    
    Args:
        roi_dir (str): Directory containing ROI files
        mask_dir (str): Directory containing combined masks
        output_dir (str): Directory to save cell masks
        imagej_path (str): Path to ImageJ executable
        auto_close (bool): Whether to close ImageJ after execution
        
    Returns:
        str: Path to the created macro file
    """
    # Create temporary directory for macro
    temp_dir = Path("macros")
    temp_dir.mkdir(exist_ok=True)
    
    # Create macro file
    macro_path = temp_dir / "temp_create_masks.ijm"
    
    # Convert paths to absolute paths
    roi_dir = str(Path(roi_dir).absolute())
    mask_dir = str(Path(mask_dir).absolute())
    output_dir = str(Path(output_dir).absolute())
    
    # Create macro content
    macro_content = f"""
    // Create cell masks macro
    roi_dir = "{roi_dir}";
    mask_dir = "{mask_dir}";
    output_dir = "{output_dir}";
    
    // Create output directory if it doesn't exist
    File.makeDirectory(output_dir);
    
    // Get list of all ROI files
    roi_list = getFileList(roi_dir);
    
    // Process each ROI file
    for (i = 0; i < roi_list.length; i++) {{
        if (endsWith(roi_list[i], ".zip")) {{
            // Open the ROI file
            open(roi_dir + File.separator + roi_list[i]);
            
            // Get the ROI name without extension
            roi_name = File.nameWithoutExtension;
            
            // Find matching mask file
            mask_name = roi_name.replace("_rois", "_combined_mask");
            mask_path = mask_dir + File.separator + mask_name + ".tif";
            
            if (File.exists(mask_path)) {{
                // Open the mask
                open(mask_path);
                
                // Apply ROIs to create individual cell masks
                roiManager("Show All");
                roiManager("Measure");
                
                // Save each ROI as a separate mask
                for (j = 0; j < roiManager("count"); j++) {{
                    roiManager("Select", j);
                    roiManager("Measure");
                    saveAs("Tiff", output_dir + File.separator + roi_name + "_cell" + (j+1) + "_mask.tif");
                }}
                
                // Close the mask
                close();
            }}
            
            // Close the ROI file
            close();
        }}
    }}
    
    // Exit ImageJ if auto_close is enabled
    if ({str(auto_close).lower()}) {{
        exit();
    }}
    """
    
    # Write macro to file
    with open(macro_path, 'w') as f:
        f.write(macro_content)
    
    return str(macro_path)

def main():
    """Main function to create individual cell masks."""
    parser = argparse.ArgumentParser(description='Create individual cell masks from ROIs and combined masks with dedicated macro')
    
    parser.add_argument('--roi-dir', required=True,
                        help='Directory containing ROI files')
    parser.add_argument('--mask-dir', required=True,
                        help='Directory containing combined mask images')
    parser.add_argument('--output-dir', required=True,
                        help='Output directory for individual cell masks')
    parser.add_argument('--imagej', required=True,
                        help='Path to ImageJ executable')
    parser.add_argument('--macro', default='percell/macros/create_cell_masks.ijm',
                       help='Path to the dedicated ImageJ macro file (default: percell/macros/create_cell_masks.ijm)')
    parser.add_argument('--auto-close', action='store_true',
                        help='Close ImageJ when the macro completes')
    parser.add_argument('--verbose', '-v', action='store_true',
                        help='Enable more verbose logging')
    parser.add_argument('--channels', nargs='+', help='Channels to process (e.g., ch00 ch02)')
    
    args = parser.parse_args()
    
    # Set logging level
    if args.verbose:
        logger.setLevel(logging.DEBUG)
    
    # Check macro file
    if not check_macro_file(args.macro):
        logger.error("Macro file validation failed")
        return 1
    
    # Parse channels argument
    channels = None
    if args.channels:
        # Handle both space-separated and single string formats
        if len(args.channels) == 1 and ' ' in args.channels[0]:
            channels = args.channels[0].split()
        else:
            channels = args.channels
        logger.info(f"Processing channels: {channels}")
    else:
        logger.info("No channels specified, processing all channels")
    
    # Find all ROI files in the ROI directory
    roi_dir = Path(args.roi_dir)
    mask_dir = Path(args.mask_dir)
    output_dir = Path(args.output_dir)
    
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # Find all ROI files in all subdirectories of the ROI directory
    roi_files = []
    for condition_dir in roi_dir.glob("*"):
        if condition_dir.is_dir() and not condition_dir.name.startswith('.'):
            roi_files.extend(list(condition_dir.glob("*.zip")))
    
    if not roi_files:
        logger.error(f"No ROI files found in {roi_dir}")
        return 1
    
    logger.info(f"Found {len(roi_files)} total ROI files")
    
    # Filter ROI files by specified channels if provided
    if channels:
        filtered_roi_files = []
        for roi_file in roi_files:
            # Extract channel from ROI filename
            roi_filename = roi_file.name
            channel_match = re.search(r'_(ch\d+)_', roi_filename)
            if channel_match:
                roi_channel = channel_match.group(1)
                if roi_channel in channels:
                    filtered_roi_files.append(roi_file)
                    logger.debug(f"Including ROI file {roi_file} (channel: {roi_channel})")
                else:
                    logger.debug(f"Skipping ROI file {roi_file} (channel: {roi_channel} not in {channels})")
            else:
                logger.warning(f"Could not extract channel from ROI filename: {roi_filename}")
        
        roi_files = filtered_roi_files
        logger.info(f"After channel filtering, processing {len(roi_files)} ROI files for channels: {channels}")
    
    if not roi_files:
        logger.error(f"No ROI files found matching specified channels: {channels}")
        return 1
    
    # Process each ROI file
    successful_masks = 0
    total_masks = 0
    
    for roi_file in roi_files:
        logger.info(f"Processing ROI file: {roi_file}")
        
        # Find the corresponding mask file
        mask_file = find_matching_mask_for_roi(roi_file, mask_dir)
        
        if mask_file:
            # Create output directory for this ROI
            mask_output_dir = create_output_dir_for_roi(roi_file, output_dir)
            
            # Create temporary macro with embedded parameters
            logger.info("Creating macro with embedded parameters...")
            temp_macro_file = create_macro_with_parameters(
                args.macro,
                roi_file,
                mask_file,
                mask_output_dir,
                args.auto_close
            )
            
            if not temp_macro_file:
                logger.error("Failed to create macro with parameters")
                continue
            
            try:
                # Run the ImageJ macro
                logger.info("Starting cell mask creation process...")
                success = run_imagej_macro(args.imagej, temp_macro_file, args.auto_close)
                
                if success:
                    # Check if masks were actually created
                    mask_files = list(mask_output_dir.glob("MASK_CELL*.tif"))
                    if not mask_files:
                        mask_files = list(mask_output_dir.glob("MASK_CELL*.tiff"))
                    
                    if mask_files:
                        logger.info(f"Successfully created {len(mask_files)} cell masks in {mask_output_dir}")
                        successful_masks += 1
                        total_masks += len(mask_files)
                    else:
                        logger.warning(f"No cell mask files were created in {mask_output_dir}")
                        # Wait a bit longer and check again (for network drives)
                        time.sleep(5)
                        mask_files = list(mask_output_dir.glob("MASK_CELL*.tif"))
                        if not mask_files:
                            mask_files = list(mask_output_dir.glob("MASK_CELL*.tiff"))
                        
                        if mask_files:
                            logger.info(f"On second check, found {len(mask_files)} cell masks in {mask_output_dir}")
                            successful_masks += 1
                            total_masks += len(mask_files)
                else:
                    logger.error("Cell mask creation failed")
            
            finally:
                # Clean up temporary macro file
                try:
                    os.unlink(temp_macro_file)
                    logger.debug(f"Cleaned up temporary macro file: {temp_macro_file}")
                except Exception as e:
                    logger.warning(f"Could not clean up temporary macro file {temp_macro_file}: {e}")
        else:
            logger.error(f"Could not find matching mask file for ROI: {roi_file}")
    
    logger.info(f"Cell mask creation completed. Successfully processed {successful_masks} of {len(roi_files)} ROI files.")
    logger.info(f"Total cell masks created: {total_masks}")
    
    if successful_masks > 0:
        return 0
    else:
        return 1

if __name__ == "__main__":
    sys.exit(main())