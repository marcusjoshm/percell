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
    # Delegate to domain ROIProcessor
    from percell.infrastructure.dependencies.container import Container as DIContainer, AppConfig as DIAppConfig
    from percell.domain.value_objects.file_path import FilePath as VOFilePath
    di = DIContainer(DIAppConfig())
    processor = di.roi_processor()
    count = processor.duplicate_rois_for_channels(VOFilePath.from_string(str(roi_dir)), channels)
    # Maintain legacy return convention: 0 on success, 1 on failure
    if count <= 0:
        return 1
    logger.info(f"Successfully created {count} ROI copies for channels {channels}")
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