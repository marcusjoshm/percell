"""
Extract Cells CLI Adapter.

This module provides a thin CLI interface for the ExtractCellsService,
handling argument parsing and user interaction while delegating business
logic to the application service.
"""

import argparse
import sys
from pathlib import Path

from percell.main.composition_root import get_composition_root


class ExtractCellsCLI:
    """
    CLI adapter for the ExtractCellsService.
    
    This adapter handles user interaction and argument parsing,
    delegating all business logic to the ExtractCellsService.
    """
    
    def __init__(self):
        """Initialize the CLI adapter."""
        self.composition_root = get_composition_root()
        self.service = self.composition_root.get_service('extract_cells_service')
    
    def create_parser(self) -> argparse.ArgumentParser:
        """Create the argument parser for the CLI."""
        parser = argparse.ArgumentParser(
            description='Extract individual cells using ROIs with dedicated macro'
        )
        
        parser.add_argument('--roi-dir', '-i', required=True,
                            help='Directory containing ROI files')
        parser.add_argument('--raw-data-dir', '-d', required=True,
                            help='Directory containing original images')
        parser.add_argument('--output-dir', '-o', required=True,
                            help='Directory where individual cells will be saved')
        parser.add_argument('--imagej', required=True,
                            help='Path to ImageJ executable')
        parser.add_argument('--macro', default='percell/macros/extract_cells.ijm',
                           help='Path to the dedicated ImageJ macro file (default: percell/macros/extract_cells.ijm)')
        parser.add_argument('--regions', '-r', nargs='+',
                            help='List of regions to process')
        parser.add_argument('--timepoints', '-t', nargs='+',
                            help='List of timepoints to process')
        parser.add_argument('--conditions', '-c', nargs='+',
                            help='List of conditions to process')
        parser.add_argument('--auto-close', action='store_true',
                            help='Close ImageJ when the macro completes')
        parser.add_argument('--verbose', '-v', action='store_true',
                            help='Enable more verbose logging')
        parser.add_argument('--channels', nargs='+', 
                            help='Channels to process')
        
        return parser
    
    def run(self, args=None) -> int:
        """
        Run the CLI application.
        
        Args:
            args: Command line arguments (optional, will parse from sys.argv if None)
            
        Returns:
            Exit code (0 for success, non-zero for failure)
        """
        try:
            parser = self.create_parser()
            parsed_args = parser.parse_args(args)
            
            # Validate arguments
            if not self._validate_args(parsed_args):
                return 1
            
            # Create output directory if it doesn't exist
            Path(parsed_args.output_dir).mkdir(parents=True, exist_ok=True)
            
            # Call the service
            results = self.service.extract_cells(
                roi_directory=parsed_args.roi_dir,
                raw_data_directory=parsed_args.raw_data_dir,
                output_directory=parsed_args.output_dir,
                imagej_path=parsed_args.imagej,
                macro_path=parsed_args.macro,
                regions=parsed_args.regions,
                timepoints=parsed_args.timepoints,
                conditions=parsed_args.conditions,
                channels=parsed_args.channels,
                auto_close=parsed_args.auto_close
            )
            
            # Handle results
            if results["success"]:
                self._print_success_summary(results)
                return 0
            else:
                self._print_error_summary(results)
                return 1
                
        except KeyboardInterrupt:
            print("\nOperation cancelled by user")
            return 1
        except Exception as e:
            print(f"Unexpected error: {e}")
            return 1
    
    def _validate_args(self, args: argparse.Namespace) -> bool:
        """Validate command line arguments."""
        # Check if required directories exist
        if not Path(args.roi_dir).exists():
            print(f"Error: ROI directory does not exist: {args.roi_dir}")
            return False
        
        if not Path(args.raw_data_dir).exists():
            print(f"Error: Raw data directory does not exist: {args.raw_data_dir}")
            return False
        
        if not Path(args.imagej).exists():
            print(f"Error: ImageJ executable does not exist: {args.imagej}")
            return False
        
        # Check macro file if specified
        if args.macro and not Path(args.macro).exists():
            print(f"Error: Macro file does not exist: {args.macro}")
            return False
        
        return True
    
    def _print_success_summary(self, results: dict) -> None:
        """Print a summary of successful extraction results."""
        print("\n" + "="*60)
        print("✅ CELL EXTRACTION COMPLETED SUCCESSFULLY")
        print("="*60)
        print(f"Total ROI files processed: {results['total_roi_files']}")
        print(f"Successful extractions: {results['successful_extractions']}")
        print(f"Total cells extracted: {results['total_cells_extracted']}")
        
        if results['failed_extractions']:
            print(f"\n⚠️  Failed extractions: {len(results['failed_extractions'])}")
            for failure in results['failed_extractions']:
                print(f"  - {failure['roi_file']}: {failure['error']}")
        
        print("="*60)
    
    def _print_error_summary(self, results: dict) -> None:
        """Print a summary of extraction errors."""
        print("\n" + "="*60)
        print("❌ CELL EXTRACTION FAILED")
        print("="*60)
        print(f"Error: {results.get('error', 'Unknown error')}")
        
        if 'failed_extractions' in results and results['failed_extractions']:
            print(f"\nFailed extractions: {len(results['failed_extractions'])}")
            for failure in results['failed_extractions']:
                print(f"  - {failure['roi_file']}: {failure['error']}")
        
        print("="*60)


def main():
    """Main entry point for the CLI."""
    cli = ExtractCellsCLI()
    sys.exit(cli.run())


if __name__ == "__main__":
    main()
