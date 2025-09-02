#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Group Cells CLI Adapter

This CLI adapter provides a command-line interface for the GroupCellsService,
allowing users to group cells by expression level using clustering algorithms.

Part of Microscopy Single-Cell Analysis Pipeline
"""

import argparse
import sys
from pathlib import Path
from typing import List

from percell.main.composition_root import get_composition_root


class GroupCellsCLI:
    """
    CLI adapter for the GroupCellsService.
    
    This adapter handles user interaction and delegates business logic
    to the GroupCellsService through the composition root.
    """
    
    def __init__(self):
        """Initialize the CLI adapter."""
        self.composition_root = get_composition_root()
        self.service = self.composition_root.get_service('group_cells_service')
    
    def _create_parser(self) -> argparse.ArgumentParser:
        """Create the command line argument parser."""
        parser = argparse.ArgumentParser(
            description="Group cells based on intensity using clustering algorithms",
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog="""
Examples:
  # Group cells with default 5 bins using GMM clustering
  group_cells --cells-dir /path/to/cells --output-dir /path/to/output --channels ch01 ch02
  
  # Group cells with custom number of bins
  group_cells --cells-dir /path/to/cells --output-dir /path/to/output --bins 8 --channels ch01
  
  # Use K-means clustering instead of GMM
  group_cells --cells-dir /path/to/cells --output-dir /path/to/output --method kmeans --channels ch01 ch02
  
  # Force clustering even with similar intensity values
  group_cells --cells-dir /path/to/cells --output-dir /path/to/output --force-clusters --channels ch01
  
  # Enable verbose output for debugging
  group_cells --cells-dir /path/to/cells --output-dir /path/to/output --verbose --channels ch01 ch02
            """
        )
        
        # Required arguments
        parser.add_argument(
            '--cells-dir',
            type=str,
            required=True,
            help='Directory containing cell images'
        )
        parser.add_argument(
            '--output-dir',
            type=str,
            required=True,
            help='Directory to save grouped cells'
        )
        parser.add_argument(
            '--channels',
            nargs='+',
            required=True,
            help='Channels to process (space-separated)'
        )
        
        # Optional arguments
        parser.add_argument(
            '--bins',
            type=int,
            default=5,
            help='Number of intensity bins (default: 5)'
        )
        parser.add_argument(
            '--method',
            choices=['gmm', 'kmeans'],
            default='gmm',
            help='Clustering method: gmm (Gaussian Mixture Model) or kmeans (default: gmm)'
        )
        parser.add_argument(
            '--force-clusters',
            action='store_true',
            help='Force clustering even if few cells or similar intensity values'
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
        # Check if cells directory exists
        cells_path = Path(args.cells_dir)
        if not cells_path.exists():
            print(f"Error: Cells directory does not exist: {args.cells_dir}")
            return False
        
        if not cells_path.is_dir():
            print(f"Error: Cells path is not a directory: {args.cells_dir}")
            return False
        
        # Check if output directory can be created
        output_path = Path(args.output_dir)
        try:
            output_path.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            print(f"Error: Cannot create output directory {args.output_dir}: {e}")
            return False
        
        # Validate bins
        if args.bins <= 0:
            print(f"Error: Number of bins must be positive: {args.bins}")
            return False
        
        # Validate channels
        if not args.channels:
            print("Error: At least one channel must be specified")
            return False
        
        return True
    
    def run(self, args: List[str] = None) -> int:
        """
        Run the group cells CLI.
        
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
            
            # Set log level based on verbosity
            if parsed_args.verbose:
                # This would need to be implemented in the logging port
                pass
            
            # Perform cell grouping
            return self._process_cell_grouping(parsed_args)
            
        except KeyboardInterrupt:
            print("\nOperation cancelled by user")
            return 1
        except Exception as e:
            print(f"Error: {e}")
            if 'parsed_args' in locals() and parsed_args.verbose:
                import traceback
                traceback.print_exc()
            return 1
    
    def _process_cell_grouping(self, args: argparse.ArgumentParser) -> int:
        """
        Process cell grouping using the group cells service.
        
        Args:
            args: Parsed command line arguments
            
        Returns:
            int: Exit code
        """
        print(f"Starting cell grouping process...")
        print(f"Cells directory: {args.cells_dir}")
        print(f"Output directory: {args.output_dir}")
        print(f"Channels: {', '.join(args.channels)}")
        print(f"Number of bins: {args.bins}")
        print(f"Clustering method: {args.method.upper()}")
        print(f"Force clusters: {'Yes' if args.force_clusters else 'No'}")
        print(f"Verbose mode: {'Yes' if args.verbose else 'No'}")
        print("-" * 60)
        
        # Process cell grouping
        results = self.service.process_cell_directories(
            cells_dir=args.cells_dir,
            output_dir=args.output_dir,
            bins=args.bins,
            method=args.method,
            force_clusters=args.force_clusters,
            channels=args.channels,
            verbose=args.verbose
        )
        
        # Display results
        print("\nProcessing Results:")
        print("-" * 60)
        print(f"Total directories found: {results['total_directories']}")
        print(f"Successfully processed: {results['successful']}")
        print(f"Failed: {results['failed']}")
        print("-" * 60)
        
        if results['successful'] > 0:
            print("\nSuccessfully processed directories:")
            for result in results['results']:
                if result['status'] == 'success':
                    channels_str = f" (channels: {', '.join(result['channels'])})" if result['channels'] else ""
                    print(f"  ✅ {result['directory']}{channels_str}")
        
        if results['failed'] > 0:
            print("\nFailed directories:")
            for result in results['results']:
                if result['status'] == 'failed':
                    channels_str = f" (channels: {', '.join(result['channels'])})" if result['channels'] else ""
                    print(f"  ❌ {result['directory']}{channels_str}")
        
        print("-" * 60)
        
        if results['success']:
            print("Cell grouping completed successfully!")
            print(f"\nOutput files created:")
            print(f"  - Summed images: {args.output_dir}/**/bin_*.tif")
            print(f"  - Grouping info: {args.output_dir}/**/grouping_info.txt")
            print(f"  - Cell mapping: {args.output_dir}/**/cell_groups.csv")
            return 0
        else:
            print("Cell grouping failed. No directories were successfully processed.")
            if 'error' in results:
                print(f"Error: {results['error']}")
            return 1


def main():
    """Main entry point for the group cells CLI."""
    cli = GroupCellsCLI()
    exit_code = cli.run()
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
