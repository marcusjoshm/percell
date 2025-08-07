#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Cell Mask Analysis Script

This script uses ImageJ to analyze mask files, running the Analyze Particles
function and capturing the results directly from stdout to create CSV files.

This version uses a dedicated macro file with parameter passing instead of 
creating permanent macro files with hardcoded paths.
"""

import os
import sys
import argparse
import logging
import subprocess
from pathlib import Path
import tempfile
import glob
import time
import re
import csv
import pandas as pd
import numpy as np
import cv2
import shutil

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("CellAnalysis")

# Map timepoint (t00, t03, etc.) to timepoint label (t00, t03, etc.)
TIME_MAPPING = {
    't00': 't00',  # t00
    't03': 't03',  # t03
    't06': 't06'   # t06
}

# Time translation for imaging log file
TIMEPOINT_TO_MINUTES = {
    't00': '45',  # t00
    't03': '60',  # t03
    't06': '75'   # t06
}

def create_macro_with_parameters(macro_template_file, mask_paths, csv_file, auto_close=False):
    """
    Create a temporary macro file with parameters embedded from the dedicated macro template.
    
    Args:
        macro_template_file (str): Path to the dedicated macro template file
        mask_paths (list): List of paths to mask files to analyze
        csv_file (str): Path to the CSV file to save results
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
        normalized_mask_paths = []
        for mask_path in mask_paths:
            normalized_path = str(mask_path).replace('\\', '/')
            normalized_mask_paths.append(normalized_path)
        
        csv_file_path = str(csv_file).replace('\\', '/')
        
        # Create semicolon-separated list of mask files
        mask_files_list = ";".join(normalized_mask_paths)
        
        # Add parameter definitions at the beginning
        parameter_definitions = f"""
// Parameters embedded from Python script
mask_files_list = "{mask_files_list}";
csv_file = "{csv_file_path}";
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
    Run ImageJ with the dedicated macro using -batch mode.
    
    Args:
        imagej_path (str): Path to the ImageJ executable
        macro_file (str): Path to the dedicated ImageJ macro file
        auto_close (bool): Whether the macro will automatically close ImageJ
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Use -batch mode for headless execution
        cmd = [imagej_path, "-batch", str(macro_file)]
        
        logger.info(f"Running ImageJ command: {' '.join(cmd)}")
        logger.info(f"ImageJ will {'auto-close' if auto_close else 'remain open'} after execution")
        
        # Run ImageJ in headless mode with the macro
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # Variables for processing output
        results_count = 0
        
        # Monitor and log the output in real-time
        while True:
            output = process.stdout.readline()
            if output == '' and process.poll() is not None:
                break
            if output:
                line = output.strip()
                logger.info(f"ImageJ: {line}")
                
                # Count how many files were analyzed
                if line.startswith("ANALYSIS_END:"):
                    results_count += 1
        
        # Get any remaining output
        stdout, stderr = process.communicate()
        if stdout:
            logger.info(f"ImageJ additional output: {stdout.strip()}")
        if stderr:
            logger.warning(f"ImageJ errors: {stderr.strip()}")
        
        # Check if the command executed successfully
        if process.returncode != 0:
            logger.error(f"ImageJ returned non-zero exit code: {process.returncode}")
            if results_count == 0:
                return False
        
        logger.info(f"Successfully processed {results_count} mask files")
        return results_count > 0
        
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
            if '#@ String mask_files_list' not in content:
                logger.warning(f"Macro file may not be compatible - missing mask_files_list parameter")
            if '#@ String csv_file' not in content:
                logger.warning(f"Macro file may not be compatible - missing csv_file parameter")
            if '#@ Boolean auto_close' not in content:
                logger.warning(f"Macro file may not be compatible - missing auto_close parameter")
        
        logger.info(f"Macro file validated: {macro_file}")
        return True
        
    except Exception as e:
        logger.error(f"Cannot read macro file {macro_file}: {e}")
        return False

def find_mask_files(input_dir, max_files=50, regions=None, timepoints=None):
    """
    Find mask files in the input directory and group them by parent directories.
    
    Args:
        input_dir (str): Input directory to search
        max_files (int): Maximum number of files to find
        regions (list): List of regions to include (e.g., R_1, R_2, or custom regions like '50min_Washout_LSG1-Halo')
                       When specified, directories will match if they contain any part of these regions or vice versa
        timepoints (list): List of timepoints to include (e.g., t00, t03)
        
    Returns:
        dict: Dictionary mapping directory paths to lists of mask file paths
    """
    # Group mask files by their parent directory
    mask_files_by_dir = {}
    
    # Convert input timepoints to list if needed
    target_timepoints = []
    if timepoints:
        # Handle both string and list inputs
        if isinstance(timepoints, str):
            # Split by whitespace and strip each item
            target_timepoints = [tp.strip() for tp in timepoints.split()]
        elif isinstance(timepoints, list):
            # If it's a list with space-separated items, split each item
            temp_timepoints = []
            for tp in timepoints:
                if isinstance(tp, str) and ' ' in tp:
                    temp_timepoints.extend([t.strip() for t in tp.split()])
                else:
                    temp_timepoints.append(tp)
            target_timepoints = temp_timepoints
    
    # Handle regions input
    target_regions = []
    if regions:
        # Similar handling for regions
        if isinstance(regions, str):
            target_regions = [r.strip() for r in regions.split()]
        elif isinstance(regions, list):
            temp_regions = []
            for r in regions:
                if isinstance(r, str) and ' ' in r:
                    temp_regions.extend([reg.strip() for reg in r.split()])
                else:
                    temp_regions.append(r)
            target_regions = temp_regions
    
    logger.info(f"Looking for mask files in: {input_dir}")
    logger.info(f"Filtering by regions: {target_regions}")
    logger.info(f"Filtering by timepoints: {target_timepoints}")
    
    # Search for .tif and .tiff files
    for extension in ["tif", "tiff"]:
        pattern = os.path.join(input_dir, "**", f"MASK_CELL*.{extension}")
        logger.info(f"Searching with pattern: {pattern}")
        
        for mask_path in glob.glob(pattern, recursive=True):
            # Get the parent directory (usually contains the condition/region info)
            parent_dir = os.path.dirname(mask_path)
            
            # Extract region and timepoint from the directory name
            dir_name = os.path.basename(parent_dir)
            logger.info(f"Processing directory: {dir_name}")
            
            # Try several patterns to match directories
            region = None
            timepoint = None
            
            # First try the standard R_X_tXX pattern
            standard_match = re.match(r"(R_\d+)_(t\d+)", dir_name)
            if standard_match:
                region = standard_match.group(1)
                timepoint = standard_match.group(2)
                logger.info(f"  Matched standard pattern - region: {region}, timepoint: {timepoint}")
            
            # If that doesn't match, try the custom pattern with region_timepoint
            elif '_' in dir_name:
                # Try to match a pattern like "50min_Washout_t00" or "region_t00"
                custom_match = re.match(r"(.+?)_(t\d+)$", dir_name)
                if custom_match:
                    region = custom_match.group(1)
                    timepoint = custom_match.group(2)
                    logger.info(f"  Matched custom pattern - region: {region}, timepoint: {timepoint}")
            
            # If we still don't have a match, try to extract as much info as possible
            if region is None or timepoint is None:
                # Look for any timepoint pattern
                tp_match = re.search(r"(t\d+)", dir_name)
                if tp_match:
                    timepoint = tp_match.group(1)
                    # Use the rest as the region
                    parts = dir_name.split(timepoint)
                    potential_region = parts[0].strip('_')
                    if potential_region:
                        region = potential_region
                    logger.info(f"  Extracted from parts - region: {region}, timepoint: {timepoint}")
            
            # Skip if we couldn't extract both region and timepoint
            if region is None or timepoint is None:
                logger.info(f"  Could not extract region/timepoint from directory: {dir_name}")
                continue
            
            # Filter by regions if specified - with more flexible matching
            if target_regions:
                region_match = False
                for target_region in target_regions:
                    # Check if the directory region is a subset of a target region
                    if region in target_region or target_region in region:
                        region_match = True
                        logger.info(f"  Region {region} matched with target region {target_region}")
                        break
                
                if not region_match:
                    logger.info(f"  Skipping {dir_name} due to region filter (no match found between {region} and {target_regions})")
                    continue
                
            # Filter by timepoints if specified
            if target_timepoints and timepoint not in target_timepoints:
                logger.info(f"  Skipping {dir_name} due to timepoint filter ({timepoint} not in {target_timepoints})")
                continue
            
            # Add the file to the appropriate directory group
            if parent_dir not in mask_files_by_dir:
                mask_files_by_dir[parent_dir] = []
            mask_files_by_dir[parent_dir].append(mask_path)
            logger.info(f"  Added mask file: {os.path.basename(mask_path)}")
    
    # Log the results
    total_files = sum(len(files) for files in mask_files_by_dir.values())
    logger.info(f"Found {total_files} mask files in {len(mask_files_by_dir)} directories matching filters")
    
    # Log the contents of each matched directory
    for dir_path, file_paths in mask_files_by_dir.items():
        logger.info(f"Directory {os.path.basename(dir_path)} has {len(file_paths)} mask files")
        for i, file_path in enumerate(file_paths[:3]):
            logger.info(f"  Sample file {i+1}: {os.path.basename(file_path)}")
        if len(file_paths) > 3:
            logger.info(f"  ...and {len(file_paths) - 3} more files")
    
    if total_files == 0:
        logger.error(f"No mask files found in {input_dir} matching filters")
        return {}
    
    return mask_files_by_dir

def generate_csv_filename(directory_path, output_dir):
    """
    Generate a unique CSV filename based on the directory structure.
    
    Args:
        directory_path (str): Directory path containing the mask files
        output_dir (str): Base output directory
        
    Returns:
        str: Path to the CSV file
    """
    # Extract condition name from directory path, same as measure_roi_area.py
    dir_path = Path(directory_path)
    condition_name = dir_path.parent.name  # Get the condition directory name (parent of mask directory)
    
    # Get the mask directory name for additional identification
    mask_dir_name = dir_path.name
    
    # Create filename with condition prefix, similar to cell area files
    csv_name = f"{condition_name}_{mask_dir_name}_particle_analysis.csv"
    
    return os.path.join(output_dir, csv_name)

def process_mask_directory(dir_path, mask_paths, output_dir, imagej_path, macro_template_file, auto_close=False):
    """
    Process a directory of mask files.
    
    Args:
        dir_path (str): Path to the directory
        mask_paths (list): List of mask file paths to process
        output_dir (str): Output directory for results
        imagej_path (str): Path to the ImageJ executable
        macro_template_file (str): Path to the dedicated macro template file
        auto_close (bool): Whether to add auto-close functionality
        
    Returns:
        bool: True if successful, False otherwise
    """
    # Generate an output CSV filename for the directory
    csv_file = generate_csv_filename(dir_path, output_dir)
    
    # Create temporary macro with embedded parameters
    logger.info("Creating macro with embedded parameters...")
    temp_macro_file = create_macro_with_parameters(
        macro_template_file,
        mask_paths,
        csv_file,
        auto_close
    )
    
    if not temp_macro_file:
        logger.error("Failed to create macro with parameters")
        return False
    
    try:
        # Run the macro with ImageJ
        logger.info("Starting mask analysis process...")
        success = run_imagej_macro(imagej_path, temp_macro_file, auto_close)
        
        if success:
            logger.info(f"Successfully analyzed {len(mask_paths)} mask files in {dir_path}")
        else:
            logger.error(f"Failed to analyze mask files in {dir_path}")
        
        return success
    
    finally:
        # Clean up temporary macro file
        try:
            os.unlink(temp_macro_file)
            logger.debug(f"Cleaned up temporary macro file: {temp_macro_file}")
        except Exception as e:
            logger.warning(f"Could not clean up temporary macro file {temp_macro_file}: {e}")

def create_analysis_macro(input_dir, output_dir, imagej_path, auto_close=True):
    """
    Create ImageJ macro for analyzing cell masks.
    
    Args:
        input_dir (str): Directory containing cell masks
        output_dir (str): Directory to save analysis results
        imagej_path (str): Path to ImageJ executable
        auto_close (bool): Whether to close ImageJ after execution
        
    Returns:
        str: Path to the created macro file
    """
    # Create temporary directory for macro
    temp_dir = Path("macros")
    temp_dir.mkdir(exist_ok=True)
    
    # Create macro file
    macro_path = temp_dir / "temp_analyze_masks.ijm"
    
    # Convert paths to absolute paths
    input_dir = str(Path(input_dir).absolute())
    output_dir = str(Path(output_dir).absolute())
    
    # Create macro content
    macro_content = f"""
    // Analyze cell masks macro
    input_dir = "{input_dir}";
    output_dir = "{output_dir}";
    
    // Create output directory if it doesn't exist
    File.makeDirectory(output_dir);
    
    // Get list of all mask files
    file_list = getFileList(input_dir);
    
    // Process each file
    for (i = 0; i < file_list.length; i++) {{
        if (endsWith(file_list[i], "_mask.tif")) {{
            // Open the mask
            open(input_dir + File.separator + file_list[i]);
            
            // Get the mask name without extension
            mask_name = File.nameWithoutExtension;
            
            // Set measurements
            run("Set Measurements...", "area mean standard modal min centroid center perimeter bounding fit shape feret's integrated median skewness kurtosis area_fraction display redirect=None decimal=3");
            
            // Measure the mask
            run("Measure");
            
            // Save measurements
            saveAs("Results", output_dir + File.separator + mask_name + "_measurements.csv");
            
            // Close the mask
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
    """Main function to analyze cell masks."""
    parser = argparse.ArgumentParser(description='Analyze cell masks using ImageJ with dedicated macro')
    
    parser.add_argument('--input', '-i', required=True,
                        help='Directory containing mask files')
    parser.add_argument('--output', '-o', required=True,
                        help='Directory for output analysis files')
    parser.add_argument('--imagej', required=True,
                        help='Path to ImageJ executable')
    parser.add_argument('--macro', default='single_cell_analyzer/macros/analyze_cell_masks.ijm',
                       help='Path to the dedicated ImageJ macro file (default: single_cell_analyzer/macros/analyze_cell_masks.ijm)')
    parser.add_argument('--regions', nargs='+',
                        help='Specific regions to process (e.g., R_1 R_2)')
    parser.add_argument('--timepoints', '-t', nargs='+',
                        help='Specific timepoints to process (e.g., t00 t03)')
    parser.add_argument('--max-files', type=int, default=50,
                        help='Maximum number of files to process per directory')
    parser.add_argument('--channels', nargs='+', help='Channels to process')
    
    args = parser.parse_args()
    
    # Create output directory if it doesn't exist
    os.makedirs(args.output, exist_ok=True)
    
    # Check macro file
    if not check_macro_file(args.macro):
        logger.error("Macro file validation failed")
        return 1
    
    # Find mask files grouped by directory
    mask_files_by_dir = find_mask_files(
        args.input, 
        args.max_files,
        args.regions,
        args.timepoints
    )
    
    if not mask_files_by_dir:
        logger.error(f"No mask files found in {args.input} matching the specified filters.") # Adjusted message
        return 1
    
    # Process each directory
    success_count = 0
    total_dirs = len(mask_files_by_dir)
    
    for dir_path, mask_paths in mask_files_by_dir.items():
        success = process_mask_directory(
            dir_path, 
            mask_paths, 
            args.output, 
            args.imagej, 
            args.macro,
            auto_close=True  # Always auto-close for batch processing
        )
        if success:
            success_count += 1
    
    # Report overall results
    if success_count > 0:
        logger.info(f"Cell mask analysis completed successfully: {success_count}/{total_dirs} directories processed")
        
        # Combine all CSV files into a single summary
        if success_count > 1:
            combine_csv_files(args.output)
        
        return 0
    else:
        logger.error("Cell mask analysis failed - no successful directories processed")
        return 1

def combine_csv_files(output_dir):
    """
    Combine all CSV summary files in the output directory into a single consolidated file.
    
    Args:
        output_dir (str): Directory containing individual CSV summary files
    
    Returns:
        str: Path to the combined CSV file, or None if no files were found/combined
    """
    # Find all CSV files in the output directory
    csv_pattern = os.path.join(output_dir, '*_summary.csv')
    csv_files = glob.glob(csv_pattern)
    
    if not csv_files:
        logger.warning(f"No CSV summary files found in {output_dir} to combine")
        return None
    
    logger.info(f"Found {len(csv_files)} CSV summary files to combine")
    
    # Read all CSV files into pandas DataFrames
    all_dfs = []
    for csv_file in csv_files:
        try:
            # Extract condition/region information from filename
            filename = os.path.basename(csv_file)
            base_name = filename.replace('_summary.csv', '')
            
            # Read the CSV file
            df = pd.read_csv(csv_file)
            
            # Add columns to identify the source
            # Parse out experiment details from the filename
            if filename.startswith('masks_'):
                # Example: masks_Dish_9_FUS-P525L_VCPi_+_Washout_+_DMSO_R_1_t00_summary.csv
                parts = base_name.split('_')
                
                # Extract information - assuming a specific format
                # This may need to be adjusted based on actual filename patterns
                region_idx = -2 if parts[-2].startswith('R') else None
                time_idx = -1 if parts[-1].startswith('t') else None
                
                if region_idx:
                    df['Region'] = parts[region_idx]
                if time_idx:
                    df['Timepoint'] = parts[time_idx]
                
                # Extract condition by removing timepoint and region
                condition_parts = parts[1:-2] if region_idx and time_idx else parts[1:]
                df['Condition'] = '_'.join(condition_parts)
            else:
                # Generic handling if the filename doesn't match expected pattern
                df['Source'] = base_name
            
            all_dfs.append(df)
            logger.info(f"Processed {filename} with {len(df)} rows")
            
        except Exception as e:
            logger.warning(f"Error reading CSV file {csv_file}: {e}")
            continue
    
    if not all_dfs:
        logger.warning("No valid data found in CSV files")
        return None
    
    # Combine all DataFrames
    combined_df = pd.concat(all_dfs, ignore_index=True)
    
    # Generate output filename based on common elements
    # Extract what appears to be the experiment identifier (e.g., Dish_9)
    experiment_ids = set()
    for csv_file in csv_files:
        filename = os.path.basename(csv_file)
        if filename.startswith('masks_'):
            parts = filename.split('_')
            if len(parts) > 2:
                experiment_ids.add(f"{parts[1]}_{parts[2]}")
    
    # Create a combined filename
    if experiment_ids:
        combined_name = '_'.join(sorted(experiment_ids))
    else:
        # Fallback if we can't extract experiment IDs
        combined_name = "combined_analysis"
    
    combined_file = os.path.join(output_dir, f"{combined_name}_combined_analysis.csv")
    
    # Save the combined DataFrame
    combined_df.to_csv(combined_file, index=False)
    logger.info(f"Created combined analysis file: {combined_file} with {len(combined_df)} rows")
    
    return combined_file

if __name__ == "__main__":
    sys.exit(main())