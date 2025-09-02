"""
Measure ROI Area CLI Adapter.

This module provides a thin CLI interface for the MeasureROIAreaService,
handling argument parsing and user interaction while delegating business
logic to the application service.
"""

import argparse
import sys
from pathlib import Path

from percell.main.composition_root import get_composition_root


class MeasureROIAreaCLI:
    """
    CLI adapter for the MeasureROIAreaService.
    
    This adapter handles user interaction and argument parsing,
    delegating all business logic to the MeasureROIAreaService.
    """
    
    def __init__(self):
        """Initialize the CLI adapter."""
        self.composition_root = get_composition_root()
        self.service = self.composition_root.get_service('measure_roi_area_service')
    
    def create_parser(self) -> argparse.ArgumentParser:
        """Create the argument parser for the CLI."""
        parser = argparse.ArgumentParser(
            description='Measure ROI areas from ROI files and corresponding raw image files using ImageJ'
        )
        
        parser.add_argument('input_dir', 
                            help='Input directory containing raw data')
        parser.add_argument('output_dir', 
                            help='Output directory containing processed data')
        parser.add_argument('imagej_path', 
                            help='Path to ImageJ executable')
        parser.add_argument('--auto-close', action='store_true', default=True,
                            help='Auto-close ImageJ after each measurement (default: True)')
        parser.add_argument('--no-auto-close', dest='auto_close', action='store_false',
                            help='Do not auto-close ImageJ after each measurement')
        
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
            results = self.service.measure_roi_areas(
                input_directory=parsed_args.input_dir,
                output_directory=parsed_args.output_dir,
                imagej_path=parsed_args.imagej_path,
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
        if not Path(args.input_dir).exists():
            print(f"Error: Input directory does not exist: {args.input_dir}")
            return False
        
        if not Path(args.imagej_path).exists():
            print(f"Error: ImageJ executable does not exist: {args.imagej_path}")
            return False
        
        return True
    
    def _print_success_summary(self, results: dict) -> None:
        """Print a summary of successful measurement results."""
        print("\n" + "="*60)
        print("✅ ROI AREA MEASUREMENT COMPLETED SUCCESSFULLY")
        print("="*60)
        print(f"Total pairs processed: {results['total_pairs']}")
        print(f"Successful pairs: {results['successful_pairs']}")
        print(f"Output directory: {results['output_directory']}")
        
        if results.get('message'):
            print(f"\nMessage: {results['message']}")
        
        if results.get('failed_pairs'):
            print(f"\n⚠️  Failed pairs: {len(results['failed_pairs'])}")
            for roi_file, image_file, reason in results['failed_pairs']:
                print(f"  - ROI: {Path(roi_file).name}")
                print(f"    Image: {Path(image_file).name}")
                print(f"    Reason: {reason}")
                print()
        
        print("="*60)
    
    def _print_error_summary(self, results: dict) -> None:
        """Print a summary of measurement errors."""
        print("\n" + "="*60)
        print("❌ ROI AREA MEASUREMENT FAILED")
        print("="*60)
        print(f"Error: {results.get('error', 'Unknown error')}")
        
        if 'failed_pairs' in results and results['failed_pairs']:
            print(f"\nFailed pairs: {len(results['failed_pairs'])}")
            for roi_file, image_file, reason in results['failed_pairs']:
                print(f"  - ROI: {Path(roi_file).name}")
                print(f"    Image: {Path(image_file).name}")
                print(f"    Reason: {reason}")
        
        print("="*60)


def main():
    """Main entry point for the CLI."""
    cli = MeasureROIAreaCLI()
    sys.exit(cli.run())


if __name__ == "__main__":
    main()
