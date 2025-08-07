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
import glob
import argparse
import numpy as np
import zipfile
from scipy.optimize import linear_sum_assignment
from read_roi import read_roi_zip
import logging
from pathlib import Path
import re

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s', stream=sys.stdout)
logger = logging.getLogger("ROITracker")

def load_roi_dict(zip_file_path):
    """
    Load ROI dictionaries from an ImageJ ROI .zip file using read_roi_zip.
    Returns a dictionary mapping ROI file names (without extension) to ROI dictionaries.
    
    Args:
        zip_file_path (str): Path to the ROI zip file
        
    Returns:
        dict: Dictionary mapping ROI names to ROI dictionaries
    """
    try:
        return read_roi_zip(zip_file_path)
    except Exception as e:
        logger.error(f"Error loading ROI file {zip_file_path}: {e}")
        return None

def load_roi_bytes(zip_file_path):
    """
    Load raw ROI file bytes from an ImageJ ROI .zip file.
    Returns a dictionary mapping ROI file names (without extension) to raw bytes.
    
    Args:
        zip_file_path (str): Path to the ROI zip file
        
    Returns:
        dict: Dictionary mapping ROI names to raw bytes
    """
    roi_bytes = {}
    try:
        with zipfile.ZipFile(zip_file_path, 'r') as z:
            for name in z.namelist():
                # Remove '.roi' extension (case-insensitive) if present
                key = name
                if name.lower().endswith('.roi'):
                    key = name[:-4]
                roi_bytes[key] = z.read(name)
        return roi_bytes
    except Exception as e:
        logger.error(f"Error loading ROI bytes from {zip_file_path}: {e}")
        return None

def polygon_centroid(x, y):
    """
    Compute the centroid of a polygon given vertex coordinate lists x and y.
    Uses the shoelace formula; if the computed area is nearly zero, falls back to arithmetic mean.
    Assumes the polygon is closed (first vertex == last vertex).
    
    Args:
        x (list): List of x-coordinates
        y (list): List of y-coordinates
        
    Returns:
        tuple: (x, y) coordinates of the centroid
    """
    A = 0.0
    Cx = 0.0
    Cy = 0.0
    n = len(x) - 1  # because the polygon is closed
    for i in range(n):
        cross = x[i] * y[i+1] - x[i+1] * y[i]
        A += cross
        Cx += (x[i] + x[i+1]) * cross
        Cy += (y[i] + y[i+1]) * cross
    A *= 0.5
    if abs(A) < 1e-8:
        return (sum(x[:-1]) / n, sum(y[:-1]) / n)
    Cx /= (6 * A)
    Cy /= (6 * A)
    return (Cx, Cy)

def get_roi_center(roi):
    """
    Compute the centroid of an ROI dictionary.
    
    If the ROI contains 'x' and 'y' keys (lists of vertex coordinates), compute the centroid using the shoelace formula.
    Otherwise, fall back to rectangular ROI parameters if available.
    
    Args:
        roi (dict): ROI dictionary from read_roi_zip
        
    Returns:
        tuple: (x, y) coordinates of the ROI center
        
    Raises:
        ValueError: If the ROI dictionary does not have expected keys
    """
    if 'x' in roi and 'y' in roi:
        x = list(roi['x'])
        y = list(roi['y'])
        # Ensure the polygon is closed
        if x[0] != x[-1] or y[0] != y[-1]:
            x.append(x[0])
            y.append(y[0])
        return polygon_centroid(x, y)
    elif all(k in roi for k in ['left', 'top', 'width', 'height']):
        return (roi['left'] + roi['width'] / 2, roi['top'] + roi['height'] / 2)
    elif all(k in roi for k in ['left', 'top', 'right', 'bottom']):
        w = roi['right'] - roi['left']
        h = roi['bottom'] - roi['top']
        return (roi['left'] + w / 2, roi['top'] + h / 2)
    else:
        raise ValueError("ROI dictionary does not have expected keys.")

def match_rois(roi_list1, roi_list2):
    """
    Given two lists of ROI dictionaries, compute the optimal matching indices (for roi_list2)
    that minimizes the total Euclidean distance between centroids.
    
    Args:
        roi_list1 (list): List of ROI dictionaries for first time point
        roi_list2 (list): List of ROI dictionaries for second time point
        
    Returns:
        list: List of indices that map ROIs in roi_list2 to match roi_list1
    """
    n1 = len(roi_list1)
    n2 = len(roi_list2)
    
    # If the lists have different lengths, use the smaller one as the size
    # and only match that many ROIs
    n = min(n1, n2)
    
    # Use a subset of ROIs if necessary
    roi_subset1 = roi_list1[:n]
    roi_subset2 = roi_list2[:n]
    
    cost_matrix = np.zeros((n, n))
    centers1 = [get_roi_center(roi) for roi in roi_subset1]
    centers2 = [get_roi_center(roi) for roi in roi_subset2]
    
    for i in range(n):
        for j in range(n):
            cost_matrix[i, j] = np.linalg.norm(np.array(centers1[i]) - np.array(centers2[j]))
    
    row_ind, col_ind = linear_sum_assignment(cost_matrix)
    
    # If the second list is longer, pad the matching with additional indices
    if n2 > n1:
        extra_indices = list(range(n, n2))
        return list(col_ind) + extra_indices
    
    return col_ind

def save_zip_from_bytes(roi_bytes_list, output_zip_path):
    """
    Save a list of raw ROI bytes to a zip file.
    Each ROI file is written with a sequential name (e.g. ROI_001.roi).
    
    Args:
        roi_bytes_list (list): List of raw ROI byte data
        output_zip_path (str): Path to save the zip file
    """
    try:
        with zipfile.ZipFile(output_zip_path, 'w') as z:
            for i, data in enumerate(roi_bytes_list):
                name = f"ROI_{i+1:03d}.roi"
                z.writestr(name, data)
        logger.info(f"Saved reordered ROIs to {output_zip_path}")
    except Exception as e:
        logger.error(f"Error saving zip file {output_zip_path}: {e}")
        return False
    return True

def process_roi_pair(zip_file1, zip_file2):
    """
    Process a pair of ROI zip files, reordering the second to match the first.
    
    Args:
        zip_file1 (str): Path to the first ROI zip file (reference)
        zip_file2 (str): Path to the second ROI zip file (to be reordered)
        
    Returns:
        bool: True if successful, False otherwise
    """
    logger.info(f"Processing ROI pair: {os.path.basename(zip_file1)} -> {os.path.basename(zip_file2)}")
    
    # Load ROI dictionaries from each zip file
    roi_dict1 = load_roi_dict(zip_file1)
    roi_dict2 = load_roi_dict(zip_file2)
    
    if roi_dict1 is None or roi_dict2 is None:
        logger.error("Failed to load ROI dictionaries.")
        return False
    
    # Load raw ROI file bytes from the second zip file
    roi_bytes2 = load_roi_bytes(zip_file2)
    
    if roi_bytes2 is None:
        logger.error("Failed to load ROI bytes.")
        return False
    
    # Convert dictionaries to lists while preserving the ROI file names
    roi_items1 = list(roi_dict1.items())  # list of (filename, roi_dict)
    roi_items2 = list(roi_dict2.items())
    
    # Extract ROI dictionaries and file names
    rois1 = [item[1] for item in roi_items1]
    rois2 = [item[1] for item in roi_items2]
    names2 = [item[0] for item in roi_items2]
    
    logger.info(f"Found {len(rois1)} ROIs in first file and {len(rois2)} ROIs in second file")
    
    if len(rois1) == 0 or len(rois2) == 0:
        logger.error("One or both ROI files contain no ROIs")
        return False
    
    # Compute matching: get indices for rois2 that best match rois1
    matching_indices = match_rois(rois1, rois2)
    
    # Reorder the raw bytes from the second zip using the matching
    reordered_bytes = []
    for idx in matching_indices:
        if idx < len(names2):  # Ensure index is valid
            key = names2[idx]
            reordered_bytes.append(roi_bytes2[key])
    
    # Make a backup of the original file
    backup_file = zip_file2 + ".bak"
    try:
        if not os.path.exists(backup_file):
            os.replace(zip_file2, backup_file)
            logger.info(f"Created backup: {backup_file}")
    except Exception as e:
        logger.error(f"Failed to create backup file: {e}")
        return False
    
    # Save over the second zip file
    return save_zip_from_bytes(reordered_bytes, zip_file2)

def find_roi_files_recursive(directory, t0: str, t1: str):
    """
    Recursively find pairs of ROI zip files matching t0 and t1 timepoints based on common filename prefixes.
    
    Args:
        directory (str): Root directory to search
        t0 (str): The identifier for the first timepoint (e.g., 't00')
        t1 (str): The identifier for the second timepoint (e.g., 't03')
        
    Returns:
        list: A list of tuples, where each tuple contains (path_to_t0_file, path_to_t1_file)
    """
    t0_pattern = f"**/*{t0}*_rois.zip"
    t1_pattern = f"**/*{t1}*_rois.zip"
    logger.info(f"Searching for ROI pairs recursively in '{directory}' using timepoints '{t0}' and '{t1}'")
    logger.info(f"Pattern T0: {t0_pattern}")
    logger.info(f"Pattern T1: {t1_pattern}")
    
    # Use Pathlib for robust recursive globbing
    path_dir = Path(directory)
    t0_files = list(path_dir.glob(t0_pattern))
    t1_files = list(path_dir.glob(t1_pattern))
    
    logger.info(f"Found {len(t0_files)} files matching {t0}")
    logger.info(f"Found {len(t1_files)} files matching {t1}")
    
    pairs = []
    t1_map = {str(f): f for f in t1_files} # Map full path string to Path object for faster lookup
    
    for f0_path in t0_files:
        # Derive expected t1 path by replacing t0 with t1 in the t0 path string
        # This assumes the only difference in the path affecting the match is t0 vs t1
        f0_str = str(f0_path)
        # Need a robust way to replace only the specific timepoint identifier
        # Regex might be safer if names are complex, but simple replace might work for R_X_tXX_...
        if t0 not in f0_str:
            logger.warning(f"Timepoint '{t0}' not found in path '{f0_str}'. Cannot determine matching {t1} file. Skipping.")
            continue

        expected_t1_str = f0_str.replace(t0, t1)
        
        if expected_t1_str in t1_map:
            pairs.append((str(f0_path), expected_t1_str))
        else:
            logger.warning(f"Could not find matching {t1} file for {f0_path} (expected path: {expected_t1_str})")
            
    logger.info(f"Found {len(pairs)} matching ROI pairs.")
    return pairs

def batch_process_directory(directory, t0: str, t1: str, recursive=True):
    """
    Find and process all matching ROI pairs in a directory.
    
    Args:
        directory (str): Directory to search
        t0 (str): Identifier for the first timepoint.
        t1 (str): Identifier for the second timepoint.
        recursive (bool): Whether to search recursively
    """
    if recursive:
        pairs = find_roi_files_recursive(directory, t0, t1)
    else:
        logger.error("Non-recursive search is not currently supported. Please use --recursive.")
        return
    
    if not pairs:
        logger.warning(f"No matching ROI pairs found in {directory}")
        return
    
    successful = 0
    for t0_file, t1_file in pairs:
        if process_roi_pair(t0_file, t1_file):
            successful += 1
    
    logger.info(f"Successfully processed {successful} out of {len(pairs)} ROI file pairs")
    return successful

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