#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
CLI Adapter for Interactive Thresholding Service

This module provides a command-line interface for the InteractiveThresholdingService,
allowing users to threshold grouped cell images using ImageJ with interactive ROI selection.
"""

import argparse
import sys
from pathlib import Path
from percell.main.composition_root import get_composition_root


def _create_parser() -> argparse.ArgumentParser:
    """
    Create and configure the argument parser for the interactive thresholding CLI.
    
    Returns:
        Configured argument parser
    """
    parser = argparse.ArgumentParser(
        description='Interactive thresholding of grouped cell images using ImageJ with Otsu thresholding'
    )
    
    parser.add_argument(
        '--input-dir', '-i',
        required=True,
        help='Directory containing grouped cell images'
    )
    
    parser.add_argument(
        '--output-dir', '-o',
        required=True,
        help='Directory to save thresholded mask images'
    )
    
    parser.add_argument(
        '--imagej',
        required=True,
        help='Path to ImageJ executable'
    )
    
    parser.add_argument(
        '--macro',
        default='percell/macros/threshold_grouped_cells.ijm',
        help='Path to the dedicated ImageJ macro file (default: percell/macros/threshold_grouped_cells.ijm)'
    )
    
    parser.add_argument(
        '--auto-close',
        action='store_true',
        help='Close ImageJ when the macro completes'
    )
    
    parser.add_argument(
        '--channels',
        nargs='+',
        help='Channels to process (e.g., ch00 ch02)'
    )
    
    parser.add_argument(
        '--list-channels',
        action='store_true',
        help='List available channels in the input directory and exit'
    )
    
    parser.add_argument(
        '--validate',
        action='store_true',
        help='Validate input directory structure and exit'
    )
    
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Enable verbose output'
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
    # Check if input directory exists
    if not Path(args.input_dir).exists():
        print(f"Error: Input directory does not exist: {args.input_dir}")
        return False
    
    # Check if input directory is actually a directory
    if not Path(args.input_dir).is_dir():
        print(f"Error: Input path is not a directory: {args.input_dir}")
        return False
    
    # Check if ImageJ executable exists
    if not Path(args.imagej).exists():
        print(f"Error: ImageJ executable does not exist: {args.imagej}")
        return False
    
    # Check if macro file exists
    if not Path(args.macro).exists():
        print(f"Error: Macro file does not exist: {args.macro}")
        return False
    
    return True


def _list_available_channels(input_dir: str) -> None:
    """
    List available channels in the input directory.
    
    Args:
        input_dir: Directory to scan for channels
    """
    try:
        composition_root = get_composition_root()
        service = composition_root.get_service('interactive_thresholding_service')
        
        channels = service.get_available_channels(input_dir)
        
        if channels:
            print(f"Available channels in {input_dir}:")
            for channel in channels:
                print(f"  - {channel}")
        else:
            print(f"No channels found in {input_dir}")
            
    except Exception as e:
        print(f"Error listing channels: {e}")
        sys.exit(1)


def _validate_input_structure(input_dir: str) -> None:
    """
    Validate the input directory structure.
    
    Args:
        input_dir: Directory to validate
    """
    try:
        composition_root = get_composition_root()
        service = composition_root.get_service('interactive_thresholding_service')
        
        result = service.validate_input_structure(input_dir)
        
        if result['valid']:
            print(f"✅ Input directory structure is valid")
            print(f"   {result['message']}")
            if 'condition_dirs' in result:
                print(f"   Condition directories: {', '.join(result['condition_dirs'])}")
        else:
            print(f"❌ Input directory structure is invalid")
            print(f"   Error: {result['error']}")
            sys.exit(1)
            
    except Exception as e:
        print(f"Error validating input structure: {e}")
        sys.exit(1)


def _run_interactive_thresholding(args: argparse.Namespace) -> None:
    """
    Run the interactive thresholding process.
    
    Args:
        args: Parsed command line arguments
    """
    try:
        composition_root = get_composition_root()
        service = composition_root.get_service('interactive_thresholding_service')
        
        # Parse channels argument
        channels = None
        if args.channels:
            # Handle both space-separated and single string formats
            if len(args.channels) == 1 and ' ' in args.channels[0]:
                channels = args.channels[0].split()
            else:
                channels = args.channels
        
        # Run the thresholding process
        result = service.process_grouped_cells(
            input_dir=args.input_dir,
            output_dir=args.output_dir,
            imagej_path=args.imagej,
            macro_file=args.macro,
            auto_close=args.auto_close,
            channels=channels
        )
        
        if result['success']:
            print("✅ Interactive thresholding completed successfully")
            if result.get('needs_more_bins'):
                print("📊 User requested more bins for better cell grouping")
                print("   The workflow should restart the cell grouping step with more bins")
                sys.exit(5)  # Special exit code for more bins request
            else:
                print("🎯 Thresholding process completed without additional bin requests")
                sys.exit(0)
        else:
            print(f"❌ Interactive thresholding failed")
            if 'error' in result:
                print(f"   Error: {result['error']}")
            sys.exit(1)
            
    except Exception as e:
        print(f"Error running interactive thresholding: {e}")
        sys.exit(1)


def main() -> None:
    """
    Main entry point for the interactive thresholding CLI.
    """
    parser = _create_parser()
    args = parser.parse_args()
    
    # Handle special operations first
    if args.list_channels:
        _list_available_channels(args.input_dir)
        return
    
    if args.validate:
        _validate_input_structure(args.input_dir)
        return
    
    # Validate arguments
    if not _validate_arguments(args):
        sys.exit(1)
    
    # Run the main thresholding process
    _run_interactive_thresholding(args)


if __name__ == "__main__":
    main()
