#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
CLI Adapter for Track ROIs Service

This module provides a command-line interface for the TrackROIsService,
allowing users to match and reorder ImageJ ROI files for cell tracking.
"""

import argparse
import sys
from pathlib import Path
from percell.main.composition_root import get_composition_root


def _create_parser() -> argparse.ArgumentParser:
    """
    Create and configure the argument parser for the track ROIs CLI.
    
    Returns:
        Configured argument parser
    """
    parser = argparse.ArgumentParser(
        description='Match and reorder ImageJ ROI files for cell tracking'
    )
    
    parser.add_argument(
        '--file1',
        type=str,
        help='First ROI zip file (reference)'
    )
    
    parser.add_argument(
        '--file2',
        type=str,
        help='Second ROI zip file (to be reordered)'
    )
    
    parser.add_argument(
        '--input', '-i',
        help='Input directory to search for ROI pairs'
    )
    
    parser.add_argument(
        '--recursive', '-r',
        action='store_true',
        help='Search directory recursively'
    )
    
    parser.add_argument(
        '--timepoints',
        nargs='+',
        help='List of exactly two timepoints to process (e.g., t00 t03)'
    )
    
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Enable verbose debug logging'
    )
    
    parser.add_argument(
        '--validate',
        action='store_true',
        help='Validate timepoints and exit'
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
    # Mode 1: Process specific pair
    if args.file1 and args.file2:
        # Check if both files exist
        if not Path(args.file1).exists():
            print(f"Error: First ROI file does not exist: {args.file1}")
            return False
        
        if not Path(args.file2).exists():
            print(f"Error: Second ROI file does not exist: {args.file2}")
            return False
        
        return True
    
    # Mode 2: Batch process directory
    elif args.input:
        if not Path(args.input).exists():
            print(f"Error: Input directory does not exist: {args.input}")
            return False
        
        if not Path(args.input).is_dir():
            print(f"Error: Input path is not a directory: {args.input}")
            return False
        
        if not args.recursive:
            print("Error: Batch processing currently requires the --recursive flag")
            return False
        
        # Validate timepoints argument for batch mode
        if not args.timepoints:
            print("Error: --timepoints argument is required for batch processing mode")
            return False
        
        return True
    
    else:
        print("Error: Please specify either --file1/--file2 or --input directory")
        return False


def _validate_timepoints(timepoints: list) -> None:
    """
    Validate timepoints for ROI tracking.
    
    Args:
        timepoints: List of timepoint identifiers
    """
    try:
        composition_root = get_composition_root()
        service = composition_root.get_service('track_rois_service')
        
        result = service.validate_timepoints(timepoints)
        
        if result['valid']:
            print(f"✅ {result['message']}")
        elif result.get('skip_tracking'):
            print(f"⚠️  {result['warning']}")
            print("   ROI tracking will be skipped")
            sys.exit(0)
        else:
            print(f"❌ {result['error']}")
            sys.exit(1)
            
    except Exception as e:
        print(f"Error validating timepoints: {e}")
        sys.exit(1)


def _process_roi_pair(file1: str, file2: str) -> None:
    """
    Process a specific pair of ROI files.
    
    Args:
        file1: Path to the first ROI zip file (reference)
        file2: Path to the second ROI zip file (to be reordered)
    """
    try:
        composition_root = get_composition_root()
        service = composition_root.get_service('track_rois_service')
        
        result = service.process_roi_pair(file1, file2)
        
        if result['success']:
            print("✅ ROI pair processing completed successfully")
            print(f"   {result['message']}")
            print(f"   ROIs processed: {result['rois_processed']}")
            if result.get('backup_created'):
                print(f"   Backup created: {result['backup_created']}")
            sys.exit(0)
        else:
            print(f"❌ ROI pair processing failed")
            print(f"   Error: {result['error']}")
            sys.exit(1)
            
    except Exception as e:
        print(f"Error processing ROI pair: {e}")
        sys.exit(1)


def _batch_process_directory(input_dir: str, timepoints: list, recursive: bool) -> None:
    """
    Batch process ROI files in a directory.
    
    Args:
        input_dir: Directory to search for ROI pairs
        timepoints: List of exactly two timepoints to process
        recursive: Whether to search recursively
    """
    try:
        composition_root = get_composition_root()
        service = composition_root.get_service('track_rois_service')
        
        # Validate timepoints first
        timepoint_result = service.validate_timepoints(timepoints)
        if not timepoint_result['valid']:
            if timepoint_result.get('skip_tracking'):
                print(f"⚠️  {timepoint_result['warning']}")
                print("   ROI tracking will be skipped")
                sys.exit(0)
            else:
                print(f"❌ {timepoint_result['error']}")
                sys.exit(1)
        
        t0, t1 = timepoint_result['t0'], timepoint_result['t1']
        print(f"Starting batch processing for timepoints: {t0} -> {t1}")
        
        result = service.batch_process_directory(input_dir, t0, t1, recursive=recursive)
        
        if result['success']:
            print("✅ Batch processing completed successfully")
            print(f"   {result['message']}")
            print(f"   Total pairs: {result['total_pairs']}")
            print(f"   Successful pairs: {result['successful_pairs']}")
            print(f"   Failed pairs: {result['failed_pairs']}")
            
            if result.get('errors'):
                print(f"   Errors encountered: {len(result['errors'])}")
                for error in result['errors']:
                    print(f"     - {error}")
            
            sys.exit(0)
        else:
            if result.get('warning'):
                print(f"⚠️  {result['warning']}")
                sys.exit(0)
            else:
                print(f"❌ Batch processing failed")
                print(f"   Error: {result['error']}")
                sys.exit(1)
            
    except Exception as e:
        print(f"Error in batch processing: {e}")
        sys.exit(1)


def main() -> None:
    """
    Main entry point for the track ROIs CLI.
    """
    parser = _create_parser()
    args = parser.parse_args()
    
    # Handle special operations first
    if args.validate and args.timepoints:
        _validate_timepoints(args.timepoints)
        return
    
    # Validate arguments
    if not _validate_arguments(args):
        sys.exit(1)
    
    # Run the appropriate processing mode
    if args.file1 and args.file2:
        # Mode 1: Process specific pair
        _process_roi_pair(args.file1, args.file2)
    elif args.input:
        # Mode 2: Batch process directory
        _batch_process_directory(args.input, args.timepoints, args.recursive)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
