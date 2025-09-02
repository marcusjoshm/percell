"""
Analyze Cell Masks CLI Adapter.

This module provides a thin CLI interface for the AnalyzeCellMasksService,
handling argument parsing and user interaction while delegating business
logic to the application service.
"""

import argparse
import sys
from pathlib import Path

from percell.main.composition_root import get_composition_root


class AnalyzeCellMasksCLI:
    """
    CLI adapter for the AnalyzeCellMasksService.
    
    This adapter handles user interaction and argument parsing,
    delegating all business logic to the AnalyzeCellMasksService.
    """
    
    def __init__(self):
        """Initialize the CLI adapter."""
        self.composition_root = get_composition_root()
        self.service = self.composition_root.get_service('analyze_cell_masks_service')
    
    def create_parser(self) -> argparse.ArgumentParser:
        """Create the argument parser for the CLI."""
        parser = argparse.ArgumentParser(
            description='Analyze cell masks using ImageJ with dedicated macro'
        )
        
        parser.add_argument('--input', '-i', required=True,
                            help='Directory containing mask files')
        parser.add_argument('--output', '-o', required=True,
                            help='Directory for output analysis files')
        parser.add_argument('--imagej', required=True,
                            help='Path to ImageJ executable')
        parser.add_argument('--macro', default='percell/macros/analyze_cell_masks.ijm',
                           help='Path to the dedicated ImageJ macro file (default: percell/macros/analyze_cell_masks.ijm)')
        parser.add_argument('--regions', nargs='+',
                            help='Specific regions to process (e.g., R_1 R_2)')
        parser.add_argument('--timepoints', '-t', nargs='+',
                            help='Specific timepoints to process (e.g., t00 t03)')
        parser.add_argument('--max-files', type=int, default=50,
                            help='Maximum number of files to process per directory')
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
            
            # Call the service
            results = self.service.analyze_cell_masks(
                input_directory=parsed_args.input,
                output_directory=parsed_args.output,
                imagej_path=parsed_args.imagej,
                macro_path=parsed_args.macro,
                regions=parsed_args.regions,
                timepoints=parsed_args.timepoints,
                max_files=parsed_args.max_files,
                channels=parsed_args.channels
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
        if not Path(args.input).exists():
            print(f"Error: Input directory does not exist: {args.input}")
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
        """Print a summary of successful analysis results."""
        print("\n" + "="*60)
        print("✅ CELL MASK ANALYSIS COMPLETED SUCCESSFULLY")
        print("="*60)
        print(f"Total directories processed: {results['total_directories']}")
        print(f"Successful directories: {results['successful_directories']}")
        print(f"Output directory: {results['output_directory']}")
        
        if results.get('combined_csv_file'):
            print(f"Combined CSV file: {results['combined_csv_file']}")
        
        if results['failed_directories']:
            print(f"\n⚠️  Failed directories: {len(results['failed_directories'])}")
            for failed_dir in results['failed_directories']:
                print(f"  - {failed_dir}")
        
        print("="*60)
    
    def _print_error_summary(self, results: dict) -> None:
        """Print a summary of analysis errors."""
        print("\n" + "="*60)
        print("❌ CELL MASK ANALYSIS FAILED")
        print("="*60)
        print(f"Error: {results.get('error', 'Unknown error')}")
        
        if 'failed_directories' in results and results['failed_directories']:
            print(f"\nFailed directories: {len(results['failed_directories'])}")
            for failed_dir in results['failed_directories']:
                print(f"  - {failed_dir}")
        
        print("="*60)


def main():
    """Main entry point for the CLI."""
    cli = AnalyzeCellMasksCLI()
    sys.exit(cli.run())


if __name__ == "__main__":
    main()
