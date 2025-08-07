#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Include Group Metadata in Analysis Results

This script takes the cell group metadata created during cell clustering
and incorporates it into the final analysis table, allowing for correlation
between expression level groups and cell phenotypes.
"""

import os
import sys
import argparse
import logging
import glob
import pandas as pd
import re
from pathlib import Path

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("GroupMetadataAnalysis")

def read_csv_robust(file_path):
    """
    Read CSV file with robust encoding handling.
    
    Args:
        file_path (Path or str): Path to the CSV file
        
    Returns:
        pandas.DataFrame: Loaded dataframe, or None if failed
    """
    encodings = ['utf-8', 'utf-8-sig', 'latin-1', 'cp1252', 'iso-8859-1']
    
    for encoding in encodings:
        try:
            df = pd.read_csv(file_path, encoding=encoding)
            logger.debug(f"Successfully read {file_path} with {encoding} encoding")
            return df
        except UnicodeDecodeError:
            logger.debug(f"Failed to read {file_path} with {encoding} encoding")
            continue
        except Exception as e:
            logger.error(f"Error reading {file_path} with {encoding} encoding: {e}")
            continue
    
    logger.error(f"Failed to read {file_path} with any supported encoding")
    return None

def find_group_metadata_files(grouped_cells_dir):
    """
    Find all cell group metadata CSV files.
    
    Args:
        grouped_cells_dir (str): Directory containing grouped cell metadata files
        
    Returns:
        list: List of paths to cell group metadata files
    """
    metadata_files = []
    
    # Convert to Path object if not already
    grouped_cells_dir = Path(grouped_cells_dir)
    
    # Find all *_cell_groups.csv files recursively
    for csv_file in grouped_cells_dir.glob("**/*_cell_groups.csv"):
        # Filter out macOS metadata files
        if not csv_file.name.startswith('._'):
            metadata_files.append(csv_file)
    
    logger.info(f"Found {len(metadata_files)} group metadata files")
    return metadata_files

def find_analysis_file(analysis_dir, output_dir=None):
    """
    Find the combined analysis CSV file.
    
    Args:
        analysis_dir (str): Directory containing analysis results
        output_dir (str): Base output directory for the entire workflow
        
    Returns:
        Path: Path to the combined analysis file, or None if not found
    """
    analysis_dir = Path(analysis_dir)
    
    # If output_dir is specified, try to find dish-specific combined analysis file
    if output_dir:
        # Get dish name from output directory
        output_path = Path(output_dir)
        dish_name = output_path.name.replace('_analysis_', '').replace('/', '_')
        
        # Look for dish-specific combined files
        dish_combined = analysis_dir / f"{dish_name}_combined_analysis.csv"
        if dish_combined.exists() and not dish_combined.name.startswith('._'):
            logger.info(f"Found dish-specific combined analysis file: {dish_combined}")
            return dish_combined
    
    # Look for combined_results.csv or similar
    for pattern in ["*combined*.csv", "*combined_analysis.csv", "combined_results.csv"]:
        combined_files = list(analysis_dir.glob(pattern))
        # Filter out macOS metadata files
        combined_files = [f for f in combined_files if not f.name.startswith('._')]
        if combined_files:
            combined_files.sort(key=lambda f: f.stat().st_size, reverse=True)
            logger.info(f"Found combined analysis file: {combined_files[0]}")
            return combined_files[0]
    
    # If not found, look for any CSV file that might be the combined results
    csv_files = list(analysis_dir.glob("*.csv"))
    # Filter out macOS metadata files
    csv_files = [f for f in csv_files if not f.name.startswith('._')]
    if csv_files:
        # Use the largest CSV file as it's likely the combined results
        csv_files.sort(key=lambda f: f.stat().st_size, reverse=True)
        logger.info(f"Using largest CSV file as combined analysis: {csv_files[0]}")
        return csv_files[0]
    
    logger.error(f"No CSV files found in {analysis_dir}")
    return None

def load_group_metadata(metadata_files):
    """
    Load and combine all group metadata files.
    
    Args:
        metadata_files (list): List of paths to metadata files
        
    Returns:
        pandas.DataFrame: Combined metadata dataframe
    """
    all_metadata = []
    
    for file_path in metadata_files:
        try:
            df = read_csv_robust(file_path)
            
            if df is None:
                logger.error(f"Failed to read {file_path}")
                continue
            
            # Display sample data for debugging
            logger.info(f"Sample data from {file_path}:\n{df.head(2)}")
            
            # Add source directory information to help with matching
            parent_dir = file_path.parent
            region_name = parent_dir.name
            condition_name = parent_dir.parent.name if parent_dir.parent.name != "grouped_cells" else ""
            
            df['region'] = region_name
            if condition_name:
                df['condition'] = condition_name
                
            all_metadata.append(df)
            logger.info(f"Loaded {len(df)} records from {file_path}")
            
        except Exception as e:
            logger.error(f"Error loading {file_path}: {e}")
    
    if not all_metadata:
        logger.error("No metadata files could be loaded")
        return None
    
    # Combine all metadata
    combined_df = pd.concat(all_metadata, ignore_index=True)
    logger.info(f"Combined metadata contains {len(combined_df)} records")
    
    return combined_df

def merge_metadata_with_analysis(group_metadata_df, analysis_file_path, output_path, overwrite=True, replace=True):
    """
    Merge group metadata with analysis results.
    
    Args:
        group_metadata_df (pandas.DataFrame): Group metadata dataframe
        analysis_file_path (Path): Path to analysis results file
        output_path (Path): Path to save the merged results
        overwrite (bool): Whether to overwrite the original file
        replace (bool): Whether to replace existing group data or keep it
        
    Returns:
        bool: True if successful, False otherwise
    """
    """
    Merge group metadata with analysis results.
    
    Args:
        group_metadata_df (pandas.DataFrame): Group metadata dataframe
        analysis_file_path (Path): Path to analysis results file
        output_path (Path): Path to save the merged results
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Load analysis results
        analysis_df = read_csv_robust(analysis_file_path)
        if analysis_df is None:
            logger.error(f"Failed to read analysis file: {analysis_file_path}")
            return False
        logger.info(f"Loaded analysis file with {len(analysis_df)} records")
        
        # Print column names for debugging
        logger.info(f"Analysis file columns: {analysis_df.columns.tolist()}")
        logger.info(f"Group metadata columns: {group_metadata_df.columns.tolist()}")
        
        # Check for duplicate cell entries in the analysis file
        if 'Slice' in analysis_df.columns:
            dup_count = analysis_df['Slice'].duplicated().sum()
            if dup_count > 0:
                logger.warning(f"Found {dup_count} duplicate cell entries in analysis file.")
                # This doesn't automatically fix it, but it alerts the user to the problem
        
        # If we have a 'cell_id' column in group_metadata_df, use it for matching
        if 'cell_id' in group_metadata_df.columns:
            # Clean up the cell_id values to improve matching
            group_metadata_df['cell_id_clean'] = group_metadata_df['cell_id'].apply(
                lambda x: str(x).replace('CELL', '').replace('.tif', '').strip() if isinstance(x, str) else str(x)
            )
        
        # Check if we can extract cell ID from Label, Slice, or other columns
        id_columns = ['Label', 'Slice', 'ROI']
        id_column = next((col for col in id_columns if col in analysis_df.columns), None)
        
        if id_column:
            logger.info(f"Using {id_column} column for cell identification")
            
            # Print sample values to understand format
            logger.info(f"Sample {id_column} values: {analysis_df[id_column].head(5).tolist()}")
            
            # Print more detailed examples to debug cell ID extraction
            for i in range(min(5, len(analysis_df))):
                if i < len(analysis_df):
                    logger.info(f"ID column example {i+1}: '{analysis_df[id_column].iloc[i]}'")
            
            # Extract cell ID from the identified column
            # Special case for formats like "R_1_t00_MASK_CELL1f" -> get just the number after "CELL"
            def extract_cell_id(x):
                if not isinstance(x, str):
                    return str(x)
                    
                # Special case for mask files with format R_1_t00_MASK_CELL1f
                cell_match = re.search(r'CELL(\d+)[a-zA-Z]*$', x)
                if cell_match:
                    return cell_match.group(1)  # Just the number part after CELL
                    
                # Try to get the last segment after underscore
                if '_' in x:
                    last_part = x.split('_')[-1]
                    # Remove non-digit characters if it contains digits
                    if any(c.isdigit() for c in last_part):
                        return ''.join(c for c in last_part if c.isdigit())
                    return last_part
                    
                # If nothing else works, just return any digits
                digits = ''.join(c for c in x if c.isdigit())
                if digits:
                    return digits
                    
                return x
                
            analysis_df['cell_id_clean'] = analysis_df[id_column].apply(extract_cell_id)
            
            # Log some examples of the extraction
            logger.info("Cell ID extraction examples:")
            for i in range(min(5, len(analysis_df))):
                if i < len(analysis_df):
                    original = analysis_df[id_column].iloc[i]
                    extracted = analysis_df['cell_id_clean'].iloc[i]
                    logger.info(f"  '{original}' -> '{extracted}'")
        else:
            logger.error(f"Cannot identify cell ID column in analysis file")
            return False
        
        # Print sample values after extraction for debugging
        logger.info(f"Sample extracted cell IDs: {analysis_df['cell_id_clean'].head(5).tolist()}")
        if 'cell_id_clean' in group_metadata_df.columns:
            logger.info(f"Sample metadata cell IDs: {group_metadata_df['cell_id_clean'].head(5).tolist()}")
        
        # Check which group columns we want in the final output
        group_cols_to_include = ['group_id', 'group_name', 'group_mean_auc']
        available_group_cols = [col for col in group_cols_to_include if col in group_metadata_df.columns]
        
        # First, ensure the metadata dataframe has no duplicate cell IDs
        if 'cell_id_clean' in group_metadata_df.columns and len(group_metadata_df) > 0:
            # Count duplicates
            dup_count = group_metadata_df['cell_id_clean'].duplicated().sum()
            if dup_count > 0:
                logger.warning(f"Found {dup_count} duplicate cell IDs in metadata. Taking the first occurrence.")
                # Keep only the first occurrence of each cell ID
                group_metadata_df = group_metadata_df.drop_duplicates(subset=['cell_id_clean'], keep='first')
        
        # Check if group columns already exist in the analysis_df
        existing_group_cols = [col for col in group_cols_to_include if col in analysis_df.columns]
        
        logger.info(f"Available group columns in metadata: {available_group_cols}")
        
        # Handle existing columns
        if existing_group_cols and replace:
            # Remove existing group columns if we're replacing them
            logger.info(f"Removing existing group columns: {existing_group_cols}")
            analysis_df = analysis_df.drop(columns=existing_group_cols)
            existing_group_cols = []
        
        # If group columns already exist and we're not replacing them, keep them
        if existing_group_cols and not replace:
            logger.info(f"Analysis file already has group columns: {existing_group_cols}")
            logger.info("Keeping existing group data")
            # Only add columns that don't exist yet
            new_cols = [col for col in available_group_cols if col not in existing_group_cols]
            
            if new_cols:
                logger.info(f"Adding new columns: {new_cols}")
                temp_group_df = pd.merge(
                    analysis_df[['cell_id_clean']],
                    group_metadata_df[['cell_id_clean'] + new_cols],
                    on='cell_id_clean',
                    how='left'
                )
                
                # Add the new columns
                for col in new_cols:
                    analysis_df[col] = temp_group_df[col]
            
            # Use the updated analysis dataframe as our result
            merged_df = analysis_df.copy()
        else:
            # Standard clean merge when no columns exist or we're replacing them
            logger.info("Performing clean merge with metadata")
            merged_df = pd.merge(
                analysis_df,
                group_metadata_df[['cell_id_clean'] + available_group_cols],
                on='cell_id_clean',
                how='left'
            )
        
        # Check how many rows have group data
        matched_count = merged_df['group_id'].notna().sum()
        logger.info(f"Matched {matched_count} of {len(merged_df)} records with group data")
        
        if matched_count == 0:
            logger.warning("No records were matched with group data. Check ID formats.")
            
            # As a last resort, try a more flexible matching approach
            logger.info("Attempting more flexible matching...")
            
            # Extract numeric parts from cell IDs for fuzzy matching
            analysis_df['numeric_id'] = analysis_df[id_column].apply(
                lambda x: ''.join(c for c in str(x) if c.isdigit())
            )
            
            # For metadata, the cell_id should already be numeric or nearly so
            group_metadata_df['numeric_id'] = group_metadata_df['cell_id'].apply(
                lambda x: ''.join(c for c in str(x) if c.isdigit())
            )
            
            # Log some examples for comparison
            logger.info("Numeric ID comparison examples:")
            for i in range(min(5, len(analysis_df))):
                if i < len(analysis_df):
                    original = analysis_df[id_column].iloc[i]
                    numeric = analysis_df['numeric_id'].iloc[i]
                    logger.info(f"  Analysis: '{original}' -> '{numeric}'")
                    
            for i in range(min(5, len(group_metadata_df))):
                if i < len(group_metadata_df):
                    original = group_metadata_df['cell_id'].iloc[i]
                    numeric = group_metadata_df['numeric_id'].iloc[i]
                    logger.info(f"  Metadata: '{original}' -> '{numeric}'")
            
            # Determine which group columns to include from metadata
            group_cols_to_include = ['group_id', 'group_name', 'group_mean_auc']
            available_group_cols = [col for col in group_cols_to_include if col in group_metadata_df.columns]
            
            # Check if group columns already exist
            existing_group_cols = [col for col in group_cols_to_include if col in analysis_df.columns]
            
            if existing_group_cols:
                # Update existing columns
                temp_group_df = pd.merge(
                    analysis_df[['numeric_id']],
                    group_metadata_df[['numeric_id'] + available_group_cols],
                    on='numeric_id',
                    how='left'
                )
                
                # Update the existing columns with new values and add any missing ones
                for col in available_group_cols:
                    if col in existing_group_cols:
                        analysis_df[col] = temp_group_df[col]
                    else:
                        analysis_df[col] = temp_group_df[col]
                    
                merged_df = analysis_df.copy()
            else:
                # Try matching on numeric IDs
                merged_df = pd.merge(
                    analysis_df,
                    group_metadata_df[['numeric_id'] + available_group_cols],
                    on='numeric_id',
                    how='left'
                )
            
            matched_count = merged_df['group_id'].notna().sum()
            logger.info(f"After flexible matching: {matched_count} of {len(merged_df)} records matched")
        
        # Remove temporary columns used for matching
        for col in ['cell_id_clean', 'numeric_id']:
            if col in merged_df.columns:
                merged_df = merged_df.drop(columns=[col])
        
        # Check for duplicate rows in the final dataframe
        dup_check_cols = ['Slice'] if 'Slice' in merged_df.columns else merged_df.columns.tolist()[:3]
        dup_rows = merged_df.duplicated(subset=dup_check_cols).sum()
        if dup_rows > 0:
            logger.warning(f"Found {dup_rows} duplicate rows in final merge result.")
            logger.info("Removing duplicate rows to ensure each cell appears only once.")
            merged_df = merged_df.drop_duplicates(subset=dup_check_cols)
        
        # Save merged results
        if overwrite:
            # Overwrite the original file
            merged_df.to_csv(analysis_file_path, index=False)
            logger.info(f"Updated original analysis file with group data: {analysis_file_path}")
        
        # Also save to specified output path if different
        if str(output_path) != str(analysis_file_path):
            merged_df.to_csv(output_path, index=False)
            logger.info(f"Saved merged results to {output_path}")
        
        return True
    
    except Exception as e:
        logger.error(f"Error merging data: {e}")
        return False

def main():
    parser = argparse.ArgumentParser(description='Include cell group metadata in analysis results')
    parser.add_argument('--grouped-cells-dir', required=True, help='Directory containing grouped cell metadata')
    parser.add_argument('--analysis-dir', required=True, help='Directory containing analysis results')
    parser.add_argument('--output-dir', help='Directory to save updated analysis results')
    parser.add_argument('--output-file', help='Specific output file name')
    parser.add_argument('--overwrite', action='store_true', help='Overwrite existing output files')
    parser.add_argument('--replace', action='store_true', help='Replace existing group columns')
    parser.add_argument('--verbose', action='store_true', help='Print verbose diagnostic information')
    parser.add_argument('--channels', nargs='+', help='Channels to process')
    
    args = parser.parse_args()
    
    # Set up logging level
    if args.verbose:
        logger.setLevel(logging.DEBUG)
    
    # Find all group metadata files
    metadata_files = find_group_metadata_files(args.grouped_cells_dir)
    
    if not metadata_files:
        logger.error("No group metadata files found")
        return 1
    
    # Filter metadata files by channels if specified
    if args.channels:
        filtered_files = []
        for metadata_file in metadata_files:
            file_channels = [ch for ch in args.channels if ch in str(metadata_file)]
            if file_channels:
                logger.info(f"Including {metadata_file} for channels {file_channels}")
                filtered_files.append(metadata_file)
            else:
                logger.info(f"Skipping {metadata_file} - no matching channels")
        metadata_files = filtered_files
    
    if not metadata_files:
        logger.error("No metadata files match the specified channels")
        return 1
    
    # Load and combine all metadata
    group_metadata_df = load_group_metadata(metadata_files)
    if group_metadata_df is None:
        logger.error("Failed to load group metadata")
        return 1
    
    # Find the analysis file
    analysis_file = find_analysis_file(args.analysis_dir, args.output_dir)
    if not analysis_file:
        logger.error("No analysis file found")
        return 1
    
    # Determine output path
    if args.output_file:
        output_path = Path(args.output_file)
    elif args.output_dir:
        output_path = Path(args.output_dir) / analysis_file.name
    else:
        output_path = analysis_file
    
    # Merge metadata with analysis results
    success = merge_metadata_with_analysis(
        group_metadata_df,
        analysis_file,
        output_path,
        overwrite=args.overwrite,
        replace=args.replace
    )
    
    if success:
        logger.info("Successfully processed group metadata")
        return 0
    else:
        logger.error("Failed to process group metadata")
        return 1

if __name__ == "__main__":
    sys.exit(main())
