#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Duplicate ROIs for Analysis Channels Script

This script takes ROI files created from the segmentation channel and creates
copies with naming conventions matching each analysis channel. This allows
downstream scripts to find the appropriate ROI files for each channel.
"""

import os
import sys
import argparse
import shutil
import logging
import re
from pathlib import Path

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("ROIDuplicator")

def extract_channel_from_filename(filename):
    """
    Extract channel name from ROI filename.
    
    Args:
        filename (str): ROI filename
    
    Returns:
        str: Channel name (e.g., 'ch00', 'ch01', etc.) or None if not found
    """
    # Look for channel pattern in filename
    match = re.search(r'_ch\d+_', filename)
    if match:
        return match.group(0).strip('_')
    return None

def create_roi_filename_for_channel(original_filename, original_channel, target_channel):
    """
    Create a new ROI filename by replacing the channel.
    
    Args:
        original_filename (str): Original ROI filename
        original_channel (str): Original channel (e.g., 'ch00')
        target_channel (str): Target channel (e.g., 'ch02')
        
    Returns:
        str: New filename with target channel
    """
    if original_channel in original_filename:
        return original_filename.replace(original_channel, target_channel)
    return original_filename

def duplicate_rois_for_channels(roi_dir, channels, verbose=False):
    """
    Duplicate ROI files for each analysis channel.
    
    Args:
        roi_dir (str): Directory containing ROI files
        channels (list): List of channel names to duplicate ROIs for
        verbose (bool): Enable verbose logging
    """
    roi_dir = Path(roi_dir)
    if not roi_dir.exists():
        logger.error(f"ROI directory not found: {roi_dir}")
        return 1
    
    logger.info(f"Duplicating ROI files for analysis channels: {channels}")
    
    # Find all ROI files
    roi_files = list(roi_dir.glob("**/*.zip"))
    if not roi_files:
        logger.error(f"No ROI files found in {roi_dir}")
        return 1
    
    logger.info(f"Found {len(roi_files)} ROI files to process")
    successful_copies = 0
    channels_already_exist = set()
    channels_processed = set()
    
    for roi_file in roi_files:
        if verbose:
            logger.debug(f"Processing ROI file: {roi_file}")
        
        # Extract channel from filename
        try:
            channel = extract_channel_from_filename(roi_file.name)
            if not channel:
                logger.warning(f"Could not extract channel from filename: {roi_file.name}")
                continue
        except Exception as e:
            logger.warning(f"Error extracting channel from filename: {e}")
            continue
        
        # Track which channels already have ROI files
        if channel in channels:
            channels_already_exist.add(channel)
        
        # Create a copy for each target channel
        for target_channel in channels:
            # Skip if it's the same channel
            if target_channel == channel:
                if verbose:
                    logger.debug(f"Skipping {target_channel} - already exists")
                continue
            
            # Create new filename with target channel
            # Replace the channel part while preserving the rest of the filename
            new_name = re.sub(r'_ch\d+_', f'_{target_channel}_', roi_file.name)
            new_path = roi_file.parent / new_name
            
            if verbose:
                logger.debug(f"Created ROI file for {target_channel}: {new_name}")
            
            try:
                from percell.adapters.local_filesystem_adapter import LocalFileSystemAdapter
                LocalFileSystemAdapter().copy(roi_file, new_path, overwrite=True)
                if verbose:
                    logger.debug(f"Copied {roi_file} -> {new_path}")
                successful_copies += 1
                channels_processed.add(target_channel)
            except Exception as e:
                logger.error(f"Failed to copy ROI file: {e}")
                continue
    
    # Check if all requested channels are now available (either existed or were created)
    all_channels_available = channels_already_exist.union(channels_processed)
    missing_channels = set(channels) - all_channels_available
    
    logger.info(f"Successfully copied {successful_copies} ROI files")
    logger.info(f"Channels that already existed: {sorted(list(channels_already_exist))}")
    logger.info(f"Channels created by copying: {sorted(list(channels_processed))}")
    
    if missing_channels:
        logger.error(f"Failed to provide ROI files for channels: {sorted(list(missing_channels))}")
        return 1
    elif successful_copies == 0 and len(channels_already_exist) > 0:
        logger.info("All requested channels already have ROI files - no copying needed")
    
    logger.info(f"All requested channels now have ROI files: {channels}")
    
    return 0

def main():
    parser = argparse.ArgumentParser(description='Duplicate ROI files for each analysis channel')
    parser.add_argument('--roi-dir', required=True, help='Directory containing ROI files')
    parser.add_argument('--channels', required=True, help='Channels to duplicate ROIs for (space-separated)')
    parser.add_argument('--verbose', action='store_true', help='Enable verbose logging')
    
    args = parser.parse_args()
    
    # Handle channels as either a single string or multiple arguments
    if isinstance(args.channels, list):
        channels = args.channels
    else:
        # Split the string on spaces to get individual channels
        channels = args.channels.split()
    
    if args.verbose:
        logger.setLevel(logging.DEBUG)
        logger.debug("Verbose logging enabled")
        logger.debug(f"Parsed channels: {channels}")
    
    return duplicate_rois_for_channels(args.roi_dir, channels, args.verbose)

if __name__ == "__main__":
    sys.exit(main()) 