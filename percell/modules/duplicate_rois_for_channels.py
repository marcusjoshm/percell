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

def find_segmentation_roi_files(roi_dir: Path, conditions: list, regions: list, timepoints: list, segmentation_channel: str) -> list:
    """
    Locate ROI zip files corresponding to the segmentation channel, filtered by
    selected conditions/regions/timepoints. Avoids inferring channels from names
    beyond checking for the explicit segmentation_channel token.
    """
    matched: list[Path] = []
    for condition_dir in roi_dir.glob("*"):
        if not condition_dir.is_dir() or condition_dir.name.startswith('.'):
            continue
        if conditions and condition_dir.name not in conditions:
            continue
        # ROI zips are saved directly under condition directory by the resize macro
        for roi_zip in condition_dir.glob("*.zip"):
            name = roi_zip.name
            if not name.endswith("_rois.zip"):
                continue
            if segmentation_channel and segmentation_channel not in name:
                continue
            if regions and not any(r in name for r in regions):
                continue
            if timepoints and not any(t in name for t in timepoints):
                continue
            matched.append(roi_zip)
    return matched

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

def duplicate_rois_for_channels(roi_dir, conditions, regions, timepoints, segmentation_channel, channels, verbose=False):
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
    
    # Find ROI files for the segmentation channel using the provided selections
    roi_files = find_segmentation_roi_files(roi_dir, conditions, regions, timepoints, segmentation_channel)
    if not roi_files:
        logger.error(f"No ROI files found in {roi_dir}")
        return 1
    
    logger.info(f"Found {len(roi_files)} ROI files to process")
    successful_copies = 0
    channels_processed = set()
    
    for roi_file in roi_files:
        if verbose:
            logger.debug(f"Processing ROI file: {roi_file}")

        # Create a copy for each analysis channel different from segmentation channel
        for target_channel in channels:
            if target_channel == segmentation_channel:
                continue

            base_name = roi_file.name
            if segmentation_channel and segmentation_channel in base_name:
                new_name = base_name.replace(segmentation_channel, target_channel)
            else:
                # Insert the target channel before the suffix if no token present
                new_name = re.sub(r'(\.zip)$', f'_{target_channel}\\1', base_name)

            new_path = roi_file.parent / new_name

            if verbose:
                logger.debug(f"Creating ROI file for {target_channel}: {new_name}")

            try:
                if not new_path.exists():
                    shutil.copy2(roi_file, new_path)
                successful_copies += 1
                channels_processed.add(target_channel)
            except Exception as e:
                logger.error(f"Failed to copy ROI file: {e}")
                continue
    
    logger.info(f"Successfully created or verified ROI files for channels: {sorted(list(channels_processed))}")
    
    return 0

def main():
    parser = argparse.ArgumentParser(description='Duplicate ROI files for each analysis channel')
    parser.add_argument('--roi-dir', required=True, help='Directory containing ROI files')
    parser.add_argument('--conditions', nargs='+', help='Conditions to include')
    parser.add_argument('--regions', nargs='+', help='Regions to include')
    parser.add_argument('--timepoints', nargs='+', help='Timepoints to include')
    parser.add_argument('--segmentation-channel', required=True, help='Segmentation channel used for ROI generation')
    parser.add_argument('--channels', nargs='+', required=True, help='Analysis channels to duplicate to')
    parser.add_argument('--verbose', action='store_true', help='Enable verbose logging')
    
    args = parser.parse_args()
    
    conditions = args.conditions or []
    regions = args.regions or []
    timepoints = args.timepoints or []
    channels = args.channels or []

    if args.verbose:
        logger.setLevel(logging.DEBUG)
        logger.debug("Verbose logging enabled")
        logger.debug(f"Selections -> conditions={conditions} regions={regions} timepoints={timepoints} seg_channel={args.segmentation_channel} channels={channels}")
    
    return duplicate_rois_for_channels(
        args.roi_dir,
        conditions,
        regions,
        timepoints,
        args.segmentation_channel,
        channels,
        args.verbose,
    )

if __name__ == "__main__":
    sys.exit(main()) 