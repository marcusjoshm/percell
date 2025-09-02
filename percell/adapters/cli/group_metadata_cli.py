#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
CLI Adapter for Group Metadata Service

This module provides a command-line interface for the GroupMetadataService,
allowing users to include cell group metadata in analysis results.
"""

import argparse
import sys
from pathlib import Path
from percell.main.composition_root import get_composition_root


def _create_parser() -> argparse.ArgumentParser:
    """
    Create and configure the argument parser for the group metadata CLI.
    
    Returns:
        Configured argument parser
    """
    parser = argparse.ArgumentParser(
        description='Include cell group metadata in analysis results'
    )
    
    parser.add_argument(
        '--grouped-cells-dir',
        required=True,
        help='Directory containing grouped cell metadata'
    )
    
    parser.add_argument(
        '--analysis-dir',
        required=True,
        help='Directory containing analysis results'
    )
    
    parser.add_argument(
        '--output-dir',
        help='Directory to save updated analysis results'
    )
    
    parser.add_argument(
        '--output-file',
        help='Specific output file name'
    )
    
    parser.add_argument(
        '--overwrite',
        action='store_true',
        help='Overwrite existing output files'
    )
    
    parser.add_argument(
        '--replace',
        action='store_true',
        help='Replace existing group columns'
    )
    
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Print verbose diagnostic information'
    )
    
    parser.add_argument(
        '--channels',
        nargs='+',
        help='Channels to process'
    )
    
    parser.add_argument(
        '--validate',
        action='store_true',
        help='Validate inputs and exit'
    )
    
    return parser


def _validate_arguments(args: argparse.Namespace) -> bool:
    """
    Validate the provided command line arguments.
    
    Args:
        args: Parsed command line arguments
        
    Returns:
        True if arguments are valid, False otherwise
    """
    # Check if grouped cells directory exists
    if not Path(args.grouped_cells_dir).exists():
        print(f"Error: Grouped cells directory does not exist: {args.grouped_cells_dir}")
        return False
    
    # Check if grouped cells directory is actually a directory
    if not Path(args.grouped_cells_dir).is_dir():
        print(f"Error: Grouped cells path is not a directory: {args.grouped_cells_dir}")
        return False
    
    # Check if analysis directory exists
    if not Path(args.analysis_dir).exists():
        print(f"Error: Analysis directory does not exist: {args.analysis_dir}")
        return False
    
    # Check if analysis directory is actually a directory
    if not Path(args.analysis_dir).is_dir():
        print(f"Error: Analysis path is not a directory: {args.analysis_dir}")
        return False
    
    # Check if output directory can be created (if specified)
    if args.output_dir:
        try:
            output_path = Path(args.output_dir)
            if not output_path.exists():
                output_path.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            print(f"Error: Cannot create output directory: {e}")
            return False
    
    return True


def _validate_inputs(grouped_cells_dir: str, analysis_dir: str) -> None:
    """
    Validate inputs for group metadata processing.
    
    Args:
        grouped_cells_dir: Directory containing grouped cell metadata
        analysis_dir: Directory containing analysis results
    """
    try:
        composition_root = get_composition_root()
        service = composition_root.get_service('group_metadata_service')
        
        # Check if metadata files exist
        metadata_files = service.find_group_metadata_files(grouped_cells_dir)
        if not metadata_files:
            print(f"❌ No group metadata files found in {grouped_cells_dir}")
            sys.exit(1)
        
        print(f"✅ Found {len(metadata_files)} group metadata files")
        
        # Check if analysis file can be found
        analysis_file = service.find_analysis_file(analysis_dir)
        if not analysis_file:
            print(f"❌ No analysis file found in {analysis_dir}")
            sys.exit(1)
        
        print(f"✅ Found analysis file: {analysis_file}")
        print("✅ Inputs validated successfully")
        
    except Exception as e:
        print(f"Error validating inputs: {e}")
        sys.exit(1)


def _run_group_metadata_processing(args: argparse.Namespace) -> None:
    """
    Run the group metadata processing.
    
    Args:
        args: Parsed command line arguments
    """
    try:
        composition_root = get_composition_root()
        service = composition_root.get_service('group_metadata_service')
        
        # Run the processing
        result = service.process_group_metadata(
            grouped_cells_dir=args.grouped_cells_dir,
            analysis_dir=args.analysis_dir,
            output_dir=args.output_dir,
            output_file=args.output_file,
            overwrite=args.overwrite,
            replace=args.replace,
            channels=args.channels
        )
        
        if result['success']:
            print("✅ Group metadata processing completed successfully")
            print(f"   {result['message']}")
            print(f"   Total records: {result['total_records']}")
            print(f"   Matched records: {result['matched_records']}")
            sys.exit(0)
        else:
            print(f"❌ Group metadata processing failed")
            print(f"   Error: {result['error']}")
            sys.exit(1)
            
    except Exception as e:
        print(f"Error running group metadata processing: {e}")
        sys.exit(1)


def main() -> None:
    """
    Main entry point for the group metadata CLI.
    """
    parser = _create_parser()
    args = parser.parse_args()
    
    # Handle special operations first
    if args.validate:
        _validate_inputs(args.grouped_cells_dir, args.analysis_dir)
        return
    
    # Validate arguments
    if not _validate_arguments(args):
        sys.exit(1)
    
    # Run the main processing
    _run_group_metadata_processing(args)


if __name__ == "__main__":
    main()
