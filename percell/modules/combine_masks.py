#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Combine Masks Script

This script combines binary masks (with values 0 or 255) into a single mask image.
It processes masks with the naming pattern *_bin_*.tif from the grouped_masks
directory and saves the combined masks to the combined_masks directory.
"""

import os
import sys
import argparse
import logging
import numpy as np
from pathlib import Path
from percell.adapters.local_filesystem_adapter import LocalFileSystemAdapter
from percell.adapters.pil_image_processing_adapter import PILImageProcessingAdapter
import cv2
try:
    # Import tifffile for preserving metadata when writing TIFF files
    import tifffile
    HAVE_TIFFFILE = True
except ImportError:
    HAVE_TIFFFILE = False

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("MaskCombiner")

def get_mask_prefix(filename):
    """
    Extract the mask prefix from a filename.
    
    Args:
        filename (str): The mask filename (e.g., any region name format with _bin_ pattern)
        
    Returns:
        str: The mask prefix (everything before _bin_)
    """
    # Split by "_bin_" which appears in all mask files
    parts = filename.split("_bin_")
    if len(parts) < 2:
        return None
    
    # Return the part before "_bin_", which will preserve any region naming convention
    return parts[0]

def find_mask_groups(mask_dir):
    """
    Find all mask groups in the given directory.
    
    Args:
        mask_dir (Path): Directory containing mask files
        
    Returns:
        dict: Dictionary of mask groups, where key is the group prefix and value is a list of mask file paths
    """
    mask_groups = {}
    
    # Look for mask files with the pattern *_bin_*.tif
    mask_files = list(mask_dir.glob("*_bin_*.tif"))
    
    if not mask_files:
        logger.warning(f"No mask files matching *_bin_*.tif found in {mask_dir}")
        return mask_groups
    
    # Group mask files based on their prefix
    for mask_file in mask_files:
        mask_name = mask_file.name
        prefix = get_mask_prefix(mask_name)
        
        if prefix is None:
            logger.warning(f"Could not extract prefix from {mask_name}. Skipping.")
            continue
            
        # Add mask file to its group
        if prefix not in mask_groups:
            mask_groups[prefix] = []
        mask_groups[prefix].append(mask_file)
    
    return mask_groups

def read_image_with_metadata(image_path):
    """
    Read an image file with its metadata if available.
    
    Args:
        image_path (str): Path to the image file
        
    Returns:
        tuple: The loaded image and metadata if available, or (image, None) if not
    """
    metadata = None
    
    # Try tifffile first if available (best for metadata preservation)
    if HAVE_TIFFFILE:
        try:
            with tifffile.TiffFile(image_path) as tif:
                img = tif.asarray()
                # Try to extract resolution information
                if hasattr(tif, 'pages') and len(tif.pages) > 0:
                    page = tif.pages[0]
                    if hasattr(page, 'tags'):
                        # Extract resolution information if available
                        metadata = {}
                        if 'XResolution' in page.tags:
                            metadata['XResolution'] = page.tags['XResolution'].value
                        if 'YResolution' in page.tags:
                            metadata['YResolution'] = page.tags['YResolution'].value
                        if 'ResolutionUnit' in page.tags:
                            metadata['ResolutionUnit'] = page.tags['ResolutionUnit'].value
                        # Also check for ImageJ metadata
                        if hasattr(page, 'imagej_tags') and page.imagej_tags:
                            metadata.update(page.imagej_tags)
                
                return img, metadata
        except Exception as e:
            logger.warning(f"tifffile failed to read {image_path}: {e}")
    
    # Fallback to OpenCV
    try:
        img = cv2.imread(str(image_path), cv2.IMREAD_UNCHANGED)
        if img is not None:
            return img, None
        else:
            logger.warning(f"OpenCV failed to read {image_path}")
            return None, None
    except Exception as e:
        logger.warning(f"OpenCV error reading {image_path}: {e}")
        return None, None

def combine_masks(mask_dir, output_dir, channels=None):
    """
    Combine masks for each group in the mask directory.
    
    Args:
        mask_dir (Path): Directory containing mask files
        output_dir (Path): Directory to save combined masks
        channels (list): List of channels to process
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Extract condition, region and timepoint from the mask directory path
        # Example path: /path/to/grouped_masks/Dish_1_Washout_+_DMSO/R_1_t00
        mask_dir = Path(mask_dir)
        condition = mask_dir.parent.name  # e.g., Dish_1_Washout_+_DMSO
        region_timepoint = mask_dir.name  # e.g., R_1_t00
        
        # Ensure the output directory exists
        output_condition_dir = output_dir / condition
        LocalFileSystemAdapter().ensure_dir(output_condition_dir)
        
        # Find all mask groups
        mask_groups = find_mask_groups(mask_dir)
        logger.info(f"Found {len(mask_groups)} mask groups in {mask_dir}")
        
        if not mask_groups:
            logger.warning(f"No mask groups found in {mask_dir}")
            return True  # Not an error, just no masks to process
        
        # Process each mask group
        for prefix, mask_files in mask_groups.items():
            logger.info(f"Combining {len(mask_files)} masks for group {prefix}")
            
            if not mask_files:
                logger.warning(f"No mask files found for group {prefix}")
                continue
            
            # Initialize reference metadata from the first mask
            reference_metadata = None
            
            # Initialize combined mask with zeros
            first_mask, first_metadata = read_image_with_metadata(str(mask_files[0]))
            if first_mask is None:
                logger.error(f"Unable to read {mask_files[0]}. Skipping group {prefix}.")
                continue
            
            # Store metadata from the first mask if available
            if first_metadata is not None:
                reference_metadata = first_metadata
                logger.info(f"Found metadata in first mask: {reference_metadata}")
                
            # Initialize combined mask
            combined_mask = np.zeros_like(first_mask, dtype=np.uint8)
            
            # Combine all masks
            for mask_file in mask_files:
                # Read image with metadata
                mask, metadata = read_image_with_metadata(str(mask_file))
                if mask is None:
                    logger.warning(f"Unable to read {mask_file}. Skipping.")
                    continue
                
                # If we don't have metadata yet, use this one if available
                if reference_metadata is None and metadata is not None:
                    reference_metadata = metadata
                    logger.info(f"Using metadata from {mask_file}")
                
                # Binary masks have values 0 or 255, so when we add them together,
                # all pixels that were 255 in any mask will be at least 255 in the sum
                combined_mask = np.maximum(combined_mask, mask)
            
            # Create output filename
            output_filename = f"{prefix}.tif"
            output_path = output_condition_dir / output_filename
            
            # Save the combined mask with metadata if available
            if HAVE_TIFFFILE and reference_metadata is not None:
                try:
                    # Try to save with tifffile to preserve metadata
                    # Prepare metadata dictionary
                    metadata_dict = {}
                    
                    # Try to use the original resolution metadata
                    if reference_metadata:
                        # Check for ImageJ tags
                        if 'unit' in reference_metadata and 'resolution' in reference_metadata:
                            # These are common ImageJ metadata for units and scale
                            resolution = reference_metadata.get('resolution', 1.0)
                            unit = reference_metadata.get('unit', 'um')
                            metadata_dict['resolution'] = resolution
                            metadata_dict['unit'] = unit
                            logger.info(f"Using ImageJ scale information: {resolution} pixels/{unit}")
                        
                        # Standard TIFF resolution tags
                        if 'XResolution' in reference_metadata and 'YResolution' in reference_metadata:
                            metadata_dict['XResolution'] = reference_metadata['XResolution']
                            metadata_dict['YResolution'] = reference_metadata['YResolution']
                            if 'ResolutionUnit' in reference_metadata:
                                metadata_dict['ResolutionUnit'] = reference_metadata['ResolutionUnit']
                    
                    # Save with metadata
                    tifffile.imwrite(
                        str(output_path), 
                        combined_mask, 
                        imagej=True,  # Use ImageJ format
                        resolution=(metadata_dict.get('XResolution'), metadata_dict.get('YResolution')),
                        metadata={'unit': 'um'}  # Using 'um' instead of 'µm' to avoid encoding issues
                    )
                    logger.info(f"Saved combined mask with metadata to {output_path}")
                except Exception as e:
                    logger.warning(f"Failed to save with tifffile, falling back to image adapter: {e}")
                    PILImageProcessingAdapter().write_image(output_path, combined_mask)
                    logger.info(f"Saved combined mask to {output_path} (without metadata)")
            else:
                # Use image adapter as fallback
                PILImageProcessingAdapter().write_image(output_path, combined_mask)
                if not HAVE_TIFFFILE:
                    logger.warning("tifffile library not available - scale information not preserved. Install with: pip install tifffile")
                logger.info(f"Saved combined mask to {output_path}")
            
        return True
    
    except Exception as e:
        logger.error(f"Error combining masks: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False

def process_all_masks(input_dir, output_dir):
    """
    Process all mask directories in the input directory.
    
    Args:
        input_dir (Path): Root directory containing all mask directories
        output_dir (Path): Root directory to save combined masks
        
    Returns:
        bool: True if all mask directories were processed successfully, False otherwise
    """
    # Ensure the output directory exists
    LocalFileSystemAdapter().ensure_dir(output_dir)
    
    # Find all mask directories
    # The expected structure is: input_dir/condition/region_timepoint
    mask_dirs = []
    for condition_dir in input_dir.glob("*"):
        if condition_dir.is_dir():
            for region_dir in condition_dir.glob("*"):
                if region_dir.is_dir():
                    mask_dirs.append(region_dir)
    
    logger.info(f"Found {len(mask_dirs)} mask directories to process")
    
    # Process each mask directory
    all_successful = True
    for mask_dir in mask_dirs:
        # Get relative path components
        condition = mask_dir.parent.name
        region_timepoint = mask_dir.name
        
        logger.info(f"Processing {condition} - {region_timepoint}")
        
        # Process masks in this directory
        if not combine_masks(mask_dir, output_dir):
            logger.error(f"Failed to process masks in {mask_dir}")
            all_successful = False
    
    return all_successful

def main():
    """Main entry point for the script."""
    parser = argparse.ArgumentParser(description='Combine binary masks into a single mask')
    
    parser.add_argument('--input-dir', required=True,
                        help='Input directory containing mask files (grouped_masks directory)')
    parser.add_argument('--output-dir', required=True,
                        help='Output directory for combined masks (combined_masks directory)')
    parser.add_argument('--channels', nargs='+', help='Channels to process')
    
    args = parser.parse_args()
    
    # Convert paths to Path objects
    input_dir = Path(args.input_dir)
    output_dir = Path(args.output_dir)
    
    # Process all mask directories
    if process_all_masks(input_dir, output_dir):
        logger.info("Successfully combined all masks")
        return 0
    else:
        logger.error("Failed to combine some masks")
        return 1

if __name__ == "__main__":
    sys.exit(main())