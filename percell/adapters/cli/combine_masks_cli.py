#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Combine Masks CLI Adapter

This CLI adapter provides a command-line interface for the CombineMasksService,
allowing users to combine binary masks into single combined mask images.

Part of Microscopy Single-Cell Analysis Pipeline
"""

import argparse
import sys
from pathlib import Path
from typing import List

from percell.main.composition_root import get_composition_root


class CombineMasksCLI:
    """
    CLI adapter for the CombineMasksService.
    
    This adapter handles user interaction and delegates business logic
    to the CombineMasksService through the composition root.
    """
    
    def __init__(self):
        """Initialize the CLI adapter."""
        self.composition_root = get_composition_root()
        self.service = self.composition_root.get_service('combine_masks_service')
    
    def _create_parser(self) -> argparse.ArgumentParser:
        """Create the command line argument parser."""
        parser = argparse.ArgumentParser(
            description="Combine binary masks into single combined mask images",
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog="""
Examples:
  # Combine all mask groups
  combine_masks --grouped-masks /path/to/grouped_masks --output /path/to/combined_masks
  
  # Combine specific mask groups only
  combine_masks --grouped-masks /path/to/grouped_masks --output /path/to/combined_masks --groups region1 region2
  
  # Disable metadata preservation
  combine_masks --grouped-masks /path/to/grouped_masks --output /path/to/combined_masks --no-metadata
            """
        )
        
        # Required arguments
        parser.add_argument(
            '--grouped-masks', '-g',
            type=str,
            required=True,
            help='Directory containing grouped mask files (*_bin_*.tif)'
        )
        parser.add_argument(
            '--output', '-o',
            type=str,
            required=True,
            help='Output directory for combined masks'
        )
        
        # Optional arguments
        parser.add_argument(
            '--groups',
            nargs='+',
            type=str,
            help='Specific mask groups to combine (if not specified, combines all groups)'
        )
        parser.add_argument(
            '--no-metadata',
            action='store_false',
            dest='preserve_metadata',
            default=True,
            help='Disable metadata preservation in output files'
        )
        parser.add_argument(
            '--verbose', '-v',
            action='store_true',
            help='Enable verbose output'
        )
        
        return parser
    
    def _validate_arguments(self, args: argparse.Namespace) -> bool:
        """
        Validate command line arguments.
        
        Args:
            args: Parsed command line arguments
            
        Returns:
            bool: True if arguments are valid, False otherwise
        """
        # Check if grouped masks directory exists
        grouped_masks_path = Path(args.grouped_masks)
        if not grouped_masks_path.exists():
            print(f"Error: Grouped masks directory does not exist: {args.grouped_masks}")
            return False
        
        if not grouped_masks_path.is_dir():
            print(f"Error: Grouped masks path is not a directory: {args.grouped_masks}")
            return False
        
        # Check if output directory can be created
        output_path = Path(args.output)
        try:
            output_path.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            print(f"Error: Cannot create output directory {args.output}: {e}")
            return False
        
        return True
    
    def run(self, args: List[str] = None) -> int:
        """
        Run the combine masks CLI.
        
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
            
            # Perform mask combination
            if parsed_args.groups:
                return self._combine_specific_groups(parsed_args)
            else:
                return self._combine_all_groups(parsed_args)
            
        except KeyboardInterrupt:
            print("\nOperation cancelled by user")
            return 1
        except Exception as e:
            print(f"Error: {e}")
            if 'parsed_args' in locals() and parsed_args.verbose:
                import traceback
                traceback.print_exc()
            return 1
    
    def _combine_all_groups(self, args: argparse.ArgumentParser) -> int:
        """
        Combine all mask groups found in the directory.
        
        Args:
            args: Parsed command line arguments
            
        Returns:
            int: Exit code
        """
        print(f"Combining all mask groups from: {args.grouped_masks}")
        print(f"Output directory: {args.output}")
        print(f"Metadata preservation: {'Enabled' if args.preserve_metadata else 'Disabled'}")
        print("-" * 60)
        
        # Perform combination
        results = self.service.combine_all_masks(
            grouped_masks_dir=args.grouped_masks,
            combined_masks_dir=args.output,
            preserve_metadata=args.preserve_metadata
        )
        
        if not results:
            print("No mask groups found to combine.")
            return 0
        
        # Display results
        print("\nCombination Results:")
        print("-" * 60)
        
        successful = 0
        for group_name, success in results.items():
            status = "SUCCESS" if success else "FAILED"
            print(f"{group_name:30} | {status:10}")
            if success:
                successful += 1
        
        print("-" * 60)
        print(f"Completed: {successful}/{len(results)} groups successful")
        
        if successful == len(results):
            print("All mask groups combined successfully!")
            return 0
        else:
            print(f"Warning: {len(results) - successful} groups failed to combine")
            return 1
    
    def _combine_specific_groups(self, args: argparse.ArgumentParser) -> int:
        """
        Combine specific mask groups by name.
        
        Args:
            args: Parsed command line arguments
            
        Returns:
            int: Exit code
        """
        print(f"Combining specific mask groups from: {args.grouped_masks}")
        print(f"Output directory: {args.output}")
        print(f"Groups to combine: {', '.join(args.groups)}")
        print(f"Metadata preservation: {'Enabled' if args.preserve_metadata else 'Disabled'}")
        print("-" * 60)
        
        # Perform combination
        results = self.service.combine_specific_groups(
            grouped_masks_dir=args.grouped_masks,
            combined_masks_dir=args.output,
            group_names=args.groups,
            preserve_metadata=args.preserve_metadata
        )
        
        if not results:
            print("No mask groups found to combine.")
            return 0
        
        # Display results
        print("\nCombination Results:")
        print("-" * 60)
        
        successful = 0
        for group_name, success in results.items():
            status = "SUCCESS" if success else "FAILED"
            print(f"{group_name:30} | {status:10}")
            if success:
                successful += 1
        
        print("-" * 60)
        print(f"Completed: {successful}/{len(results)} groups successful")
        
        if successful == len(results):
            print("All requested mask groups combined successfully!")
            return 0
        else:
            print(f"Warning: {len(results) - successful} groups failed to combine")
            return 1


def main():
    """Main entry point for the combine masks CLI."""
    cli = CombineMasksCLI()
    exit_code = cli.run()
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
