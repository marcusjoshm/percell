#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Cell Tracking Script for Single-Cell Analysis Workflow

This script matches ROIs between two time points by finding the optimal assignment
that minimizes the total distance between cell centroids. It reorders the ROIs in the 
second time point to match the order of ROIs in the first time point, which allows for
tracking the same cells across multiple time points.

The script can be run in two modes:
1. Individual file mode: Match ROIs between two specific files
2. Batch mode: Process all matching ROI files in a directory
"""

import os
import sys
import argparse
import logging
from pathlib import Path

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s', stream=sys.stdout)
logger = logging.getLogger("ROITracker")

def load_roi_dict(*args, **kwargs):
    raise NotImplementedError("Use RoiTrackingService via DI container.")

def load_roi_bytes(*args, **kwargs):
    raise NotImplementedError("Use RoiTrackingService via DI container.")

def polygon_centroid(*args, **kwargs):
    raise NotImplementedError("Use RoiTrackingService via DI container.")

def get_roi_center(*args, **kwargs):
    raise NotImplementedError("Use RoiTrackingService via DI container.")

def match_rois(*args, **kwargs):
    raise NotImplementedError("Use RoiTrackingService via DI container.")

def save_zip_from_bytes(*args, **kwargs):
    raise NotImplementedError("Use RoiTrackingService via DI container.")

def process_roi_pair(zip_file1, zip_file2):
    from percell.infrastructure.dependencies.container import Container as DIContainer, AppConfig as DIAppConfig
    from percell.domain.value_objects.file_path import FilePath as VOFilePath
    di = DIContainer(DIAppConfig())
    service = di.roi_tracking_service()
    return service.process_roi_pair(VOFilePath.from_string(str(zip_file1)), VOFilePath.from_string(str(zip_file2)))

def find_roi_files_recursive(directory, t0: str, t1: str):
    from percell.infrastructure.dependencies.container import Container as DIContainer, AppConfig as DIAppConfig
    from percell.domain.value_objects.file_path import FilePath as VOFilePath
    di = DIContainer(DIAppConfig())
    service = di.roi_tracking_service()
    pairs = service.find_roi_files_recursive(VOFilePath.from_string(str(directory)), t0, t1)
    return [(str(p0), str(p1)) for (p0, p1) in pairs]

def batch_process_directory(directory, t0: str, t1: str, recursive=True):
    from percell.infrastructure.dependencies.container import Container as DIContainer, AppConfig as DIAppConfig
    from percell.domain.value_objects.file_path import FilePath as VOFilePath
    di = DIContainer(DIAppConfig())
    service = di.roi_tracking_service()
    return service.batch_process_directory(VOFilePath.from_string(str(directory)), t0, t1, recursive=recursive)

def main():
    """Main entry point for the script."""
    parser = argparse.ArgumentParser(description='Match and reorder ImageJ ROI files for cell tracking')
    
    parser.add_argument('--file1', type=str, help='First ROI zip file (reference)')
    parser.add_argument('--file2', type=str, help='Second ROI zip file (to be reordered)')
    parser.add_argument('--input', '-i', help='Input directory to search for ROI pairs')
    parser.add_argument('--recursive', '-r', action='store_true', help='Search directory recursively')
    parser.add_argument('--timepoints', nargs='+', help='List of exactly two timepoints to process (e.g., t00 t03)')
    parser.add_argument('--verbose', '-v', action='store_true', help='Enable verbose debug logging')
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
        logger.setLevel(logging.DEBUG)
        logger.info("Verbose logging enabled.")
    
    # Mode 1: Process specific pair
    if args.file1 and args.file2:
        if not args.timepoints or len(args.timepoints) != 2:
            logger.warning("Processing specific files, --timepoints argument ignored/not needed.")
        success = process_roi_pair(args.file1, args.file2)
        if not success:
            sys.exit(1)
    # Mode 2: Batch process directory
    elif args.input:
        if not args.recursive:
            logger.error("Batch processing currently requires the --recursive flag.")
            sys.exit(1)
        
        # Validate timepoints argument for batch mode
        if not args.timepoints:
            logger.error("Error: --timepoints argument is required for batch processing mode.")
            sys.exit(1)
        elif len(args.timepoints) == 1:
            logger.warning(f"ROI tracking requires two timepoints. Only one selected: {args.timepoints[0]}. Skipping tracking.")
            sys.exit(0) # Exit successfully, just skip the step
        elif len(args.timepoints) != 2:
            logger.error(f"ROI tracking requires exactly two timepoints. Received {len(args.timepoints)}: {args.timepoints}. Skipping tracking.")
            sys.exit(1) # Exit with error
        else:
            # Proceed with the two selected timepoints
            t0, t1 = args.timepoints[0], args.timepoints[1]
            logger.info(f"Starting batch processing for timepoints: {t0} -> {t1}")
            batch_process_directory(args.input, t0, t1, recursive=True)
    else:
        parser.print_help()
        logger.error("Please specify either --file1/--file2 or --input directory.")
        sys.exit(1)

if __name__ == "__main__":
    main()