#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
CLI Adapter for Duplicate ROIs Service

This module provides a command-line interface for the DuplicateROIsService,
allowing users to duplicate ROI files for analysis channels.
"""

import argparse
import sys
from pathlib import Path
from percell.main.composition_root import get_composition_root


def _create_parser() -> argparse.ArgumentParser:
    """
    Create and configure the argument parser for the duplicate ROIs CLI.
    
    Returns:
        Configured argument parser
    """
    parser = argparse.ArgumentParser(
        description='Duplicate ROI files for each analysis channel'
    )
    
    parser.add_argument(
        '--roi-dir',
        required=True,
        help='Directory containing ROI files'
    )
    
    parser.add_argument(
        '--conditions',
        nargs='+',
        help='Conditions to include'
    )
    
    parser.add_argument(
        '--regions',
        nargs='+',
        help='Regions to include'
    )
    
    parser.add_argument(
        '--timepoints',
        nargs='+',
        help='Timepoints to include'
    )
    
    parser.add_argument(
        '--segmentation-channel',
        required=True,
        help='Segmentation channel used for ROI generation'
    )
    
    parser.add_argument(
        '--channels',
        nargs='+',
        required=True,
        help='Analysis channels to duplicate to'
    )
    
    parser.add_argument(
        '--list-conditions',
        action='store_true',
        help='List available conditions in ROI directory and exit'
    )
    
    parser.add_argument(
        '--list-regions',
        action='store_true',
        help='List available regions in ROI directory and exit'
    )
    
    parser.add_argument(
        '--list-timepoints',
        action='store_true',
        help='List available timepoints in ROI directory and exit'
    )
    
    parser.add_argument(
        '--validate',
        action='store_true',
        help='Validate inputs and exit'
    )
    
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Enable verbose logging'
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
    # Check if ROI directory exists
    if not Path(args.roi_dir).exists():
        print(f"Error: ROI directory does not exist: {args.roi_dir}")
        return False
    
    # Check if ROI directory is actually a directory
    if not Path(args.roi_dir).is_dir():
        print(f"Error: ROI path is not a directory: {args.roi_dir}")
        return False
    
    # Check if channels are provided
    if not args.channels:
        print("Error: No channels specified")
        return False
    
    # Check if segmentation channel is provided
    if not args.segmentation_channel:
        print("Error: Segmentation channel is required")
        return False
    
    return True


def _list_available_conditions(roi_dir: str) -> None:
    """
    List available conditions in the ROI directory.
    
    Args:
        roi_dir: Directory to scan for conditions
    """
    try:
        composition_root = get_composition_root()
        service = composition_root.get_service('duplicate_rois_service')
        
        conditions = service.get_available_conditions(roi_dir)
        
        if conditions:
            print(f"Available conditions in {roi_dir}:")
            for condition in conditions:
                print(f"  - {condition}")
        else:
            print(f"No conditions found in {roi_dir}")
            
    except Exception as e:
        print(f"Error listing conditions: {e}")
        sys.exit(1)


def _list_available_regions(roi_dir: str) -> None:
    """
    List available regions in the ROI directory.
    
    Args:
        roi_dir: Directory to scan for regions
    """
    try:
        composition_root = get_composition_root()
        service = composition_root.get_service('duplicate_rois_service')
        
        regions = service.get_available_regions(roi_dir)
        
        if regions:
            print(f"Available regions in {roi_dir}:")
            for region in regions:
                print(f"  - {region}")
        else:
            print(f"No regions found in {roi_dir}")
            
    except Exception as e:
        print(f"Error listing regions: {e}")
        sys.exit(1)


def _list_available_timepoints(roi_dir: str) -> None:
    """
    List available timepoints in the ROI directory.
    
    Args:
        roi_dir: Directory to scan for timepoints
    """
    try:
        composition_root = get_composition_root()
        service = composition_root.get_service('duplicate_rois_service')
        
        timepoints = service.get_available_timepoints(roi_dir)
        
        if timepoints:
            print(f"Available timepoints in {roi_dir}:")
            for timepoint in timepoints:
                print(f"  - {timepoint}")
        else:
            print(f"No timepoints found in {roi_dir}")
            
    except Exception as e:
        print(f"Error listing timepoints: {e}")
        sys.exit(1)


def _validate_inputs(roi_dir: str, channels: list, segmentation_channel: str) -> None:
    """
    Validate inputs for ROI duplication.
    
    Args:
        roi_dir: Directory containing ROI files
        channels: List of channel names to duplicate ROIs for
        segmentation_channel: Segmentation channel used for ROI generation
    """
    try:
        composition_root = get_composition_root()
        service = composition_root.get_service('duplicate_rois_service')
        
        result = service.validate_inputs(roi_dir, channels, segmentation_channel)
        
        if result['valid']:
            print(f"✅ {result['message']}")
        else:
            print(f"❌ {result['error']}")
            sys.exit(1)
            
    except Exception as e:
        print(f"Error validating inputs: {e}")
        sys.exit(1)


def _run_roi_duplication(args: argparse.Namespace) -> None:
    """
    Run the ROI duplication process.
    
    Args:
        args: Parsed command line arguments
    """
    try:
        composition_root = get_composition_root()
        service = composition_root.get_service('duplicate_rois_service')
        
        # Parse optional arguments
        conditions = args.conditions or []
        regions = args.regions or []
        timepoints = args.timepoints or []
        
        # Run the duplication process
        result = service.duplicate_rois_for_channels(
            roi_dir=args.roi_dir,
            conditions=conditions,
            regions=regions,
            timepoints=timepoints,
            segmentation_channel=args.segmentation_channel,
            channels=args.channels,
            verbose=args.verbose
        )
        
        if result['success']:
            print("✅ ROI duplication completed successfully")
            print(f"   Total files processed: {result['total_files_processed']}")
            print(f"   Successful copies: {result['successful_copies']}")
            print(f"   Channels processed: {', '.join(result['channels_processed'])}")
            
            if result.get('errors'):
                print(f"   Errors encountered: {len(result['errors'])}")
                if args.verbose:
                    for error in result['errors']:
                        print(f"     - {error}")
            
            print(f"   {result['message']}")
            sys.exit(0)
        else:
            print(f"❌ ROI duplication failed")
            print(f"   Error: {result['error']}")
            sys.exit(1)
            
    except Exception as e:
        print(f"Error running ROI duplication: {e}")
        sys.exit(1)


def main() -> None:
    """
    Main entry point for the duplicate ROIs CLI.
    """
    parser = _create_parser()
    args = parser.parse_args()
    
    # Handle special operations first
    if args.list_conditions:
        _list_available_conditions(args.roi_dir)
        return
    
    if args.list_regions:
        _list_available_regions(args.roi_dir)
        return
    
    if args.list_timepoints:
        _list_available_timepoints(args.roi_dir)
        return
    
    if args.validate:
        _validate_inputs(args.roi_dir, args.channels, args.segmentation_channel)
        return
    
    # Validate arguments
    if not _validate_arguments(args):
        sys.exit(1)
    
    # Run the main duplication process
    _run_roi_duplication(args)


if __name__ == "__main__":
    main()
