#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Bin Images CLI Adapter

This CLI adapter provides a command-line interface for the BinImagesService,
allowing users to bin microscopy images for cell segmentation.

Part of Microscopy Single-Cell Analysis Pipeline
"""

import argparse
import sys
from pathlib import Path
from typing import List

from percell.main.composition_root import get_composition_root


class BinImagesCLI:
    """
    CLI adapter for the BinImagesService.
    
    This adapter handles user interaction and delegates business logic
    to the BinImagesService through the composition root.
    """
    
    def __init__(self):
        """Initialize the CLI adapter."""
        self.composition_root = get_composition_root()
        self.service = self.composition_root.get_service('bin_images_service')
    
    def _create_parser(self) -> argparse.ArgumentParser:
        """Create the command line argument parser."""
        parser = argparse.ArgumentParser(
            description="Bin microscopy images for cell segmentation",
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog="""
Examples:
  # Bin all images with default 4x4 binning
  bin_images --input /path/to/raw/images --output /path/to/binned/images
  
  # Bin specific conditions only
  bin_images --input /path/to/raw/images --output /path/to/binned/images --conditions condition1 condition2
  
  # Bin with custom bin factor
  bin_images --input /path/to/raw/images --output /path/to/binned/images --bin-factor 8
  
  # Bin specific regions, timepoints, and channels
  bin_images --input /path/to/raw/images --output /path/to/binned/images --regions region1 region2 --timepoints t00 t03 --channels ch01 ch02
  
  # List available options without processing
  bin_images --input /path/to/raw/images --list-options
            """
        )
        
        # Required arguments
        parser.add_argument(
            '--input', '-i',
            type=str,
            required=True,
            help='Input directory containing raw image data'
        )
        parser.add_argument(
            '--output', '-o',
            type=str,
            required=True,
            help='Output directory for binned images'
        )
        
        # Optional arguments
        parser.add_argument(
            '--conditions',
            nargs='+',
            help='List of conditions to process (use "all" for all conditions)'
        )
        parser.add_argument(
            '--regions',
            nargs='+',
            help='List of regions to process (use "all" for all regions)'
        )
        parser.add_argument(
            '--timepoints',
            nargs='+',
            help='List of timepoints to process (e.g., t00 t03)'
        )
        parser.add_argument(
            '--channels',
            nargs='+',
            help='List of channels to process (e.g., ch00 ch01)'
        )
        parser.add_argument(
            '--bin-factor', '-b',
            type=int,
            default=4,
            help='Binning factor (default: 4)'
        )
        parser.add_argument(
            '--list-options',
            action='store_true',
            help='List available conditions, regions, timepoints, and channels without processing'
        )
        parser.add_argument(
            '--verbose', '-v',
            action='store_true',
            help='Enable verbose debug logging'
        )
        
        return parser
    
    def _validate_arguments(self, args: argparse.ArgumentParser) -> bool:
        """
        Validate command line arguments.
        
        Args:
            args: Parsed command line arguments
            
        Returns:
            bool: True if arguments are valid, False otherwise
        """
        # Check if input directory exists
        input_path = Path(args.input)
        if not input_path.exists():
            print(f"Error: Input directory does not exist: {args.input}")
            return False
        
        if not input_path.is_dir():
            print(f"Error: Input path is not a directory: {args.input}")
            return False
        
        # Check if output directory can be created
        output_path = Path(args.output)
        try:
            output_path.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            print(f"Error: Cannot create output directory {args.output}: {e}")
            return False
        
        # Validate bin factor
        if args.bin_factor <= 0:
            print(f"Error: Bin factor must be positive: {args.bin_factor}")
            return False
        
        return True
    
    def _list_available_options(self, input_dir: str):
        """
        List available conditions, regions, timepoints, and channels.
        
        Args:
            input_dir (str): Input directory path
        """
        print(f"Available options in: {input_dir}")
        print("-" * 60)
        
        try:
            # Get available conditions
            conditions = self.service.get_available_conditions(input_dir)
            print(f"Conditions ({len(conditions)}):")
            for condition in conditions:
                print(f"  - {condition}")
            print()
            
            # Get available regions
            regions = self.service.get_available_regions(input_dir)
            print(f"Regions ({len(regions)}):")
            for region in regions:
                print(f"  - {region}")
            print()
            
            # Get available timepoints
            timepoints = self.service.get_available_timepoints(input_dir)
            print(f"Timepoints ({len(timepoints)}):")
            for timepoint in timepoints:
                print(f"  - {timepoint}")
            print()
            
            # Get available channels
            channels = self.service.get_available_channels(input_dir)
            print(f"Channels ({len(channels)}):")
            for channel in channels:
                print(f"  - {channel}")
            print()
            
        except Exception as e:
            print(f"Error listing available options: {e}")
    
    def run(self, args: List[str] = None) -> int:
        """
        Run the bin images CLI.
        
        Args:
            args: Command line arguments (if None, uses sys.argv)
            
        Returns:
            int: Exit code (0 for success, non-zero for failure)
        """
        try:
            # Parse arguments
            parser = self._create_parser()
            parsed_args = parser.parse_args(args)
            
            # Validate arguments
            if not self._validate_arguments(parsed_args):
                return 1
            
            # Handle list options mode
            if parsed_args.list_options:
                self._list_available_options(parsed_args.input)
                return 0
            
            # Set log level based on verbosity
            if parsed_args.verbose:
                # This would need to be implemented in the logging port
                pass
            
            # Perform image binning
            return self._process_images(parsed_args)
            
        except KeyboardInterrupt:
            print("\nOperation cancelled by user")
            return 1
        except Exception as e:
            print(f"Error: {e}")
            if 'parsed_args' in locals() and parsed_args.verbose:
                import traceback
                traceback.print_exc()
            return 1
    
    def _process_images(self, args: argparse.ArgumentParser) -> int:
        """
        Process images using the bin images service.
        
        Args:
            args: Parsed command line arguments
            
        Returns:
            int: Exit code
        """
        print(f"Starting image binning process...")
        print(f"Input directory: {args.input}")
        print(f"Output directory: {args.output}")
        print(f"Bin factor: {args.bin_factor}")
        print(f"Conditions: {args.conditions or 'all'}")
        print(f"Regions: {args.regions or 'all'}")
        print(f"Timepoints: {args.timepoints or 'all'}")
        print(f"Channels: {args.channels or 'all'}")
        print("-" * 60)
        
        # Process images
        results = self.service.process_images(
            input_dir=args.input,
            output_dir=args.output,
            bin_factor=args.bin_factor,
            target_conditions=args.conditions,
            target_regions=args.regions,
            target_timepoints=args.timepoints,
            target_channels=args.channels
        )
        
        # Display results
        print("\nProcessing Results:")
        print("-" * 60)
        print(f"Total files found: {results['total_found']}")
        print(f"Files processed: {results['processed']}")
        print(f"Files skipped: {results['skipped']}")
        print(f"Errors encountered: {results['errors']}")
        print("-" * 60)
        
        if results['errors'] == 0:
            print("Image binning completed successfully!")
            return 0
        else:
            print(f"Image binning completed with {results['errors']} errors.")
            return 1


def main():
    """Main entry point for the bin images CLI."""
    cli = BinImagesCLI()
    exit_code = cli.run()
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
