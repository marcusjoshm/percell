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
from pathlib import Path
import logging
import sys

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s', stream=sys.stdout)
logger = logging.getLogger(__name__)

def bin_image(*args, **kwargs):
    # Deprecated in module script; logic moved to domain service.
    raise NotImplementedError("Use ImageBinningService via DI container.")


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
    
    from percell.infrastructure.dependencies.container import Container as DIContainer, AppConfig as DIAppConfig
    from percell.domain.value_objects.file_path import FilePath as VOFilePath

    di = DIContainer(DIAppConfig())
    service = di.image_binning_service()
    count = service.process_images(
        input_dir=VOFilePath.from_string(str(input_path)),
        output_dir=VOFilePath.from_string(str(output_path)),
        bin_factor=bin_factor,
        target_conditions=target_conditions,
        target_regions=target_regions,
        target_timepoints=target_timepoints,
        target_channels=target_channels,
    )
    logger.info(f"Processed {count} files matching the criteria.")


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