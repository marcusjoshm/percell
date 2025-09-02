#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Cleanup Directories CLI Adapter

This CLI adapter provides a command-line interface for the CleanupDirectoriesService,
allowing users to clean up analysis directories to free up disk space.

Part of Microscopy Single-Cell Analysis Pipeline
"""

import argparse
import sys
from pathlib import Path
from typing import List

from percell.main.composition_root import get_composition_root


class CleanupDirectoriesCLI:
    """
    CLI adapter for the CleanupDirectoriesService.
    
    This adapter handles user interaction and delegates business logic
    to the CleanupDirectoriesService through the composition root.
    """
    
    def __init__(self):
        """Initialize the CLI adapter."""
        self.composition_root = get_composition_root()
        self.service = self.composition_root.get_service('cleanup_directories_service')
    
    def _create_parser(self) -> argparse.ArgumentParser:
        """Create the command line argument parser."""
        parser = argparse.ArgumentParser(
            description="Clean up analysis directories to free up disk space",
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog="""
Examples:
  # Scan directories to see what can be cleaned up (dry run)
  cleanup_directories --output /path/to/output --scan-only
  
  # Clean up cells and masks directories only (dry run)
  cleanup_directories --output /path/to/output --cells --masks
  
  # Clean up all analysis directories (dry run)
  cleanup_directories --output /path/to/output --all
  
  # Actually perform cleanup (use with caution!)
  cleanup_directories --output /path/to/output --all --confirm --no-dry-run
            """
        )
        
        # Required arguments
        parser.add_argument(
            '--output', '-o',
            type=str,
            required=True,
            help='Output directory containing analysis results'
        )
        
        # Directory selection
        parser.add_argument(
            '--cells',
            action='store_true',
            help='Include cells directory in cleanup'
        )
        parser.add_argument(
            '--masks',
            action='store_true',
            help='Include masks directory in cleanup'
        )
        parser.add_argument(
            '--combined-masks',
            action='store_true',
            help='Include combined_masks directory in cleanup'
        )
        parser.add_argument(
            '--grouped-cells',
            action='store_true',
            help='Include grouped_cells directory in cleanup'
        )
        parser.add_argument(
            '--grouped-masks',
            action='store_true',
            help='Include grouped_masks directory in cleanup'
        )
        parser.add_argument(
            '--all',
            action='store_true',
            help='Clean up all analysis directories'
        )
        
        # Operation mode
        parser.add_argument(
            '--scan-only',
            action='store_true',
            help='Only scan directories, do not perform cleanup'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            default=True,
            help='Show what would be deleted without actually deleting (default)'
        )
        parser.add_argument(
            '--no-dry-run',
            action='store_false',
            dest='dry_run',
            help='Actually perform the deletion (use with caution!)'
        )
        parser.add_argument(
            '--confirm',
            action='store_true',
            help='Skip confirmation prompts (required for actual deletion)'
        )
        
        # Output options
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
        # Check if output directory exists
        output_path = Path(args.output)
        if not output_path.exists():
            print(f"Error: Output directory does not exist: {args.output}")
            return False
        
        if not output_path.is_dir():
            print(f"Error: Output path is not a directory: {args.output}")
            return False
        
        # Check if any directories are selected for cleanup
        directories_selected = any([
            args.cells,
            args.masks,
            args.combined_masks,
            args.grouped_cells,
            args.grouped_masks,
            args.all
        ])
        
        if not directories_selected and not args.scan_only:
            print("Error: No directories selected for cleanup. Use --cells, --masks, --all, etc.")
            return False
        
        # Safety check for actual deletion
        if not args.dry_run and not args.confirm:
            print("Error: --confirm is required when --no-dry-run is specified")
            print("This prevents accidental deletion of data")
            return False
        
        return True
    
    def _get_directories_to_clean(self, args: argparse.Namespace) -> List[str]:
        """
        Determine which directories to clean based on command line arguments.
        
        Args:
            args: Parsed command line arguments
            
        Returns:
            List[str]: List of directory names to clean
        """
        if args.all:
            return ['cells', 'masks', 'combined_masks', 'grouped_cells', 'grouped_masks']
        
        directories = []
        if args.cells:
            directories.append('cells')
        if args.masks:
            directories.append('masks')
        if args.combined_masks:
            directories.append('combined_masks')
        if args.grouped_cells:
            directories.append('grouped_cells')
        if args.grouped_masks:
            directories.append('grouped_masks')
        
        return directories
    
    def run(self, args: List[str] = None) -> int:
        """
        Run the cleanup directories CLI.
        
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
            
            # Handle scan-only mode
            if parsed_args.scan_only:
                return self._run_scan_only(parsed_args)
            
            # Handle cleanup mode
            return self._run_cleanup(parsed_args)
            
        except KeyboardInterrupt:
            print("\nOperation cancelled by user")
            return 1
        except Exception as e:
            print(f"Error: {e}")
            if parsed_args.verbose:
                import traceback
                traceback.print_exc()
            return 1
    
    def _run_scan_only(self, args: argparse.Namespace) -> int:
        """
        Run in scan-only mode to show directory information.
        
        Args:
            args: Parsed command line arguments
            
        Returns:
            int: Exit code
        """
        print(f"Scanning directories in: {args.output}")
        print("-" * 50)
        
        # Scan all directories to show current state
        scan_results = self.service.scan_cleanup_directories(
            output_dir=args.output,
            include_cells=True,
            include_masks=True,
            include_combined_masks=True,
            include_grouped_cells=True,
            include_grouped_masks=True
        )
        
        total_size = 0
        for dir_name, dir_info in scan_results.items():
            status = "EXISTS" if dir_info['exists'] else "NOT FOUND"
            size = dir_info['size_formatted']
            print(f"{dir_name:20} | {status:10} | {size:>10}")
            if dir_info['exists']:
                total_size += dir_info['size_bytes']
        
        print("-" * 50)
        total_formatted = self.service.format_size(total_size)
        print(f"{'TOTAL':20} | {'':10} | {total_formatted:>10}")
        
        return 0
    
    def _run_cleanup(self, args: argparse.Namespace) -> int:
        """
        Run the actual cleanup operation.
        
        Args:
            args: Parsed command line arguments
            
        Returns:
            int: Exit code
        """
        directories_to_clean = self._get_directories_to_clean(args)
        
        print(f"Cleanup operation for: {', '.join(directories_to_clean)}")
        print(f"Output directory: {args.output}")
        print(f"Mode: {'DRY RUN' if args.dry_run else 'ACTUAL CLEANUP'}")
        print("-" * 50)
        
        # Perform cleanup
        results = self.service.cleanup_directories(
            output_dir=args.output,
            directories_to_clean=directories_to_clean,
            dry_run=args.dry_run,
            confirm=args.confirm
        )
        
        # Display results
        print("\nCleanup Results:")
        print("-" * 50)
        
        for dir_name, result in results.items():
            status = result['status'].upper()
            size = result['size_freed']
            message = result['message']
            print(f"{dir_name:20} | {status:10} | {size:>10} | {message}")
        
        # Summary
        successful_cleanups = sum(1 for r in results.values() if r['status'] == 'deleted')
        total_cleanups = len(results)
        
        print("-" * 50)
        print(f"Completed: {successful_cleanups}/{total_cleanups} directories cleaned")
        
        if args.dry_run:
            print("\nThis was a dry run. No files were actually deleted.")
            print("Use --no-dry-run --confirm to perform actual cleanup.")
        
        return 0


def main():
    """Main entry point for the cleanup directories CLI."""
    cli = CleanupDirectoriesCLI()
    exit_code = cli.run()
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
