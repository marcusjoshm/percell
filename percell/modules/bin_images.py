#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Bin microscopy images for cell segmentation.

This script recursively searches for .tif files in the specified
input directory, performs 4x4 binning, and saves the processed 
images to the output directory.
"""

import os
import argparse
import glob
from pathlib import Path
import re
import logging
import numpy as np
from skimage import io, exposure
from skimage.transform import downscale_local_mean
import tifffile
import sys

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s', stream=sys.stdout)
logger = logging.getLogger(__name__)

def bin_image(image, bin_factor=4):
    """
    Bin an image by the specified factor using local mean.
    
    Args:
        image (numpy.ndarray): Input image
        bin_factor (int): Binning factor
        
    Returns:
        numpy.ndarray: Binned image
    """
    return downscale_local_mean(image, (bin_factor, bin_factor))


def process_images(input_dir, output_dir, bin_factor=4,
                   target_conditions=None, target_regions=None,
                   target_timepoints=None, target_channels=None):
    """
    Process images in input directory and save to output directory, filtering by selections.
    
    Args:
        input_dir (str): Input directory path
        output_dir (str): Output directory path
        bin_factor (int): Binning factor
        target_conditions (list): List of conditions to process
        target_regions (list): List of regions to process
        target_timepoints (list): List of timepoints to process
        target_channels (list): List of channels to process
    """
    input_path = Path(input_dir)
    output_path = Path(output_dir)
    
    logger.info(f"Starting image binning process.")
    logger.info(f"Input directory: {input_path}")
    logger.info(f"Output directory: {output_path}")
    logger.info(f"Bin factor: {bin_factor}")
    logger.info(f"Target Conditions: {target_conditions}")
    logger.info(f"Target Regions: {target_regions}")
    logger.info(f"Target Timepoints: {target_timepoints}")
    logger.info(f"Target Channels: {target_channels}")
    
    # Create output directory if it doesn't exist
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Use MetadataService to enumerate files and metadata
    try:
        from percell.infrastructure.dependencies.container import Container as DIContainer, AppConfig as DIAppConfig
        from percell.domain.value_objects.file_path import FilePath as VOFilePath
        di = DIContainer(DIAppConfig())
        metadata_service = di.metadata_service()
        md_list = metadata_service.scan_directory_for_metadata(VOFilePath.from_string(str(input_path)), recursive=True)
        # Build list of actual file paths from metadata
        all_files = [Path(m.file_path) for m in md_list if getattr(m, 'file_path', None)]
    except Exception as e:
        logger.warning(f"MetadataService unavailable or failed ({e}); falling back to glob.")
        all_files = list(input_path.glob("**/*.tif"))
    logger.info(f"Found {len(all_files)} total .tif files in {input_path}.")

    # Convert selection lists to sets for efficient lookup, if they exist
    # Handle 'all' special value for selections
    all_selection = {'all'}
    
    if target_conditions and all_selection.issubset(set(target_conditions)):
        selected_conditions = None  # Process all conditions
    else:
        selected_conditions = set(target_conditions) if target_conditions else None
        
    if target_regions and all_selection.issubset(set(target_regions)):
        selected_regions = None  # Process all regions
    else:
        selected_regions = set(target_regions) if target_regions else None
        
    if target_timepoints and all_selection.issubset(set(target_timepoints)):
        selected_timepoints = None  # Process all timepoints
    else: 
        selected_timepoints = set(target_timepoints) if target_timepoints else None
        
    if target_channels and all_selection.issubset(set(target_channels)):
        selected_channels = None  # Process all channels
    else:
        selected_channels = set(target_channels) if target_channels else None
        
    logger.info(f"Filter sets created - Conditions: {selected_conditions}, Regions: {selected_regions}, Timepoints: {selected_timepoints}, Channels: {selected_channels}")

    processed_count = 0
    
    for file_path in all_files:
        # Convert to Path object for easier manipulation
        file_path = Path(file_path)
        
        # --- Filter based on selections ---
        try:
            # Extract condition from parent directory path
            # The condition is usually the first directory under the input directory
            current_condition = None
            relative_path = file_path.relative_to(input_path)
            if len(relative_path.parts) > 0:
                current_condition = relative_path.parts[0]
                
            if not current_condition:
                logger.warning(f"Could not determine condition directory for {file_path}. Skipping.")
                continue
                
            if selected_conditions and current_condition not in selected_conditions:
                continue
                
            # Prefer metadata from service if available
            current_region = None
            current_timepoint = None
            current_channel = None
            try:
                # Find corresponding metadata for this file
                md = next((m for m in md_list if getattr(m, 'file_path', None) and Path(m.file_path) == file_path), None)
                if md:
                    current_region = md.region
                    current_timepoint = md.timepoint
                    current_channel = md.channel
            except Exception:
                pass
            # Fallback to filename parsing if needed
            if not (current_region and current_timepoint and current_channel):
                filename = file_path.name
                region_pattern = r'(.+?)_(ch\d+)_(t\d+)'
                region_match = re.search(region_pattern, filename)
                if region_match:
                    current_region = current_region or region_match.group(1)
                else:
                    parts = filename.split('_')
                    ch_index = -1
                    for i, part in enumerate(parts):
                        if part.startswith('ch'):
                            ch_index = i
                    if ch_index > 0:
                        current_region = current_region or '_'.join(parts[:ch_index])
                timepoint_match = re.search(r'(t\d+)', filename)
                channel_match = re.search(r'(ch\d+)', filename)
                current_timepoint = current_timepoint or (timepoint_match.group(1) if timepoint_match else None)
                current_channel = current_channel or (channel_match.group(1) if channel_match else None)

            logger.debug(f"Parsed metadata - Condition: {current_condition}, Region: {current_region}, Timepoint: {current_timepoint}, Channel: {current_channel}")

            # Apply filters
            # Apply filters - only if we have them selected
            if selected_regions is not None:
                if not current_region or current_region not in selected_regions:
                    logger.debug(f"Skipping file due to region filter: {current_region} not in {selected_regions}")
                    continue
            
            if selected_timepoints is not None:
                if not current_timepoint or current_timepoint not in selected_timepoints:
                    logger.debug(f"Skipping file due to timepoint filter: {current_timepoint} not in {selected_timepoints}")
                    continue
                    
            if selected_channels is not None:
                if not current_channel or current_channel not in selected_channels:
                    logger.debug(f"Skipping file due to channel filter: {current_channel} not in {selected_channels}")
                    continue
                
        except Exception as e:
            logger.warning(f"Could not parse metadata or apply filters for {file_path}. Skipping. Error: {e}")
            continue
        # --- End Filter ---
        
        logger.info(f"Processing {file_path}...")
        
        # Determine output path maintaining directory structure
        try:
            # Maintain the same structure as input
            # For example: input/condition/timepoint_1/file.tif -> output/condition/timepoint_1/bin4x4_file.tif
            relative_path = file_path.relative_to(input_path)
            output_file = output_path / relative_path.parent / f"bin4x4_{file_path.name}"
            
            # Create output directory structure
            output_file.parent.mkdir(parents=True, exist_ok=True)

            # Read the image
            image = io.imread(file_path)
            
            # Bin the image
            binned_image = bin_image(image, bin_factor=bin_factor)
            
            # Save the processed image
            tifffile.imwrite(output_file, binned_image.astype(image.dtype))
            
            logger.info(f"Saved binned image to {output_file}")
            processed_count += 1

        except Exception as e:
            logger.error(f"Error processing or saving file {file_path}: {e}", exc_info=True)
    
    logger.info("Image binning completed.")
    logger.info(f"Processed {processed_count} files matching the criteria.")


def main():
    parser = argparse.ArgumentParser(description="Bin microscopy images for cell segmentation")
    parser.add_argument("--input", "-i", required=True, help="Input directory containing raw image data")
    parser.add_argument("--output", "-o", required=True, help="Output directory for binned images")
    parser.add_argument("--conditions", nargs='+', help="List of conditions to process")
    parser.add_argument("--regions", nargs='+', help="List of regions to process")
    parser.add_argument("--timepoints", nargs='+', help="List of timepoints to process (e.g., t00 t03)")
    parser.add_argument("--channels", nargs='+', help="List of channels to process (e.g., ch00 ch01)")
    parser.add_argument("--bin-factor", "-b", type=int, default=4, help="Binning factor (default: 4)")
    parser.add_argument("--verbose", "-v", action="store_true", help="Enable verbose debug logging")
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG) # Set root logger to DEBUG if verbose
        logger.setLevel(logging.DEBUG) # Also set specific logger
        logger.info("Verbose logging enabled.")

    process_images(args.input, args.output, args.bin_factor, 
                   args.conditions, args.regions, args.timepoints, args.channels)


if __name__ == "__main__":
    main()