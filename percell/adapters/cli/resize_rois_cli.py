"""
Resize ROIs CLI Adapter.

This module provides a thin CLI interface for the ResizeROIsService,
handling argument parsing and user interaction while delegating business
logic to the application service.
"""

import argparse
import sys
from pathlib import Path

from percell.main.composition_root import get_composition_root


class ResizeROIsCLI:
    """
    CLI adapter for the ResizeROIsService.
    
    This adapter handles user interaction and argument parsing,
    delegating all business logic to the ResizeROIsService.
    """
    
    def __init__(self):
        """Initialize the CLI adapter."""
        self.composition_root = get_composition_root()
        self.service = self.composition_root.get_service('resize_rois_service')
    
    def create_parser(self) -> argparse.ArgumentParser:
        """Create the argument parser for the CLI."""
        parser = argparse.ArgumentParser(
            description='Resize ROIs from binned images using dedicated macro'
        )
        
        parser.add_argument('--input', '-i', required=True,
                            help='Input directory containing preprocessed images and ROIs')
        parser.add_argument('--output', '-o', required=True,
                            help='Output directory for resized ROIs')
        parser.add_argument('--imagej', required=True,
                            help='Path to ImageJ executable')
        parser.add_argument('--channel', required=True,
                            help='Segmentation channel to process ROIs for (e.g., ch00)')
        parser.add_argument('--macro', default='percell/macros/resize_rois.ijm',
                            help='Path to the dedicated ImageJ macro file (default: percell/macros/resize_rois.ijm)')
        parser.add_argument('--auto-close', action='store_true',
                            help='Close ImageJ when the macro completes')
        parser.add_argument('--verbose', '-v', action='store_true',
                            help='Enable verbose logging')
        
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
            
            # Set logging level if verbose
            if parsed_args.verbose:
                # Note: This would need to be implemented in the logging port
                # For now, we'll just log that verbose mode was requested
                print("Verbose logging requested (implementation pending)")
            
            # Validate arguments
            if not self._validate_args(parsed_args):
                return 1
            
            # Call the service
            results = self.service.resize_rois(
                input_directory=parsed_args.input,
                output_directory=parsed_args.output,
                imagej_path=parsed_args.imagej,
                channel=parsed_args.channel,
                macro_path=parsed_args.macro,
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
        """Print a summary of successful resizing results."""
        print("\n" + "="*60)
        print("✅ ROI RESIZING COMPLETED SUCCESSFULLY")
        print("="*60)
        print(f"Input directory: {results['input_directory']}")
        print(f"Output directory: {results['output_directory']}")
        print(f"Channel: {results['channel']}")
        print(f"Macro file: {results['macro_file']}")
        print("="*60)
    
    def _print_error_summary(self, results: dict) -> None:
        """Print a summary of resizing errors."""
        print("\n" + "="*60)
        print("❌ ROI RESIZING FAILED")
        print("="*60)
        print(f"Error: {results.get('error', 'Unknown error')}")
        print("="*60)


def main():
    """Main entry point for the CLI."""
    cli = ResizeROIsCLI()
    sys.exit(cli.run())


if __name__ == "__main__":
    main()
