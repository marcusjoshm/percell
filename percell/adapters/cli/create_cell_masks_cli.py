"""
CLI adapter for create cell masks functionality.

This adapter handles user interaction and delegates to the
CreateCellMasksService through the composition root.
"""

import argparse
from pathlib import Path
from typing import Optional

from percell.main.composition_root import get_composition_root
from percell.domain.exceptions import DomainError


class CreateCellMasksCLI:
    """
    CLI adapter for creating cell masks.
    
    This is a thin adapter that:
    1. Handles command line argument parsing
    2. Validates user input
    3. Delegates to the application service
    4. Handles user-friendly error reporting
    """
    
    def __init__(self):
        self.composition_root = get_composition_root()
        self.service = self.composition_root.get_service('create_cell_masks_service')
        self.config = self.composition_root.get_config()
    
    def create_parser(self) -> argparse.ArgumentParser:
        """Create the argument parser for this command."""
        parser = argparse.ArgumentParser(
            description="Create individual cell masks from ROIs and combined masks"
        )
        
        parser.add_argument(
            '--roi-dir',
            type=str,
            help='Directory containing ROI files',
            required=True
        )
        
        parser.add_argument(
            '--mask-dir',
            type=str,
            help='Directory containing combined masks',
            required=True
        )
        
        parser.add_argument(
            '--output-dir',
            type=str,
            help='Directory to save cell masks',
            required=True
        )
        
        parser.add_argument(
            '--imagej-path',
            type=str,
            help='Path to ImageJ executable (uses config default if not specified)',
            required=False
        )
        
        parser.add_argument(
            '--no-auto-close',
            action='store_true',
            help='Keep ImageJ open after execution',
            default=False
        )
        
        return parser
    
    def validate_arguments(self, args: argparse.Namespace) -> bool:
        """
        Validate command line arguments.
        
        Args:
            args: Parsed command line arguments
            
        Returns:
            bool: True if arguments are valid
            
        Raises:
            ValueError: If arguments are invalid
        """
        # Validate directories exist
        roi_dir = Path(args.roi_dir)
        if not roi_dir.exists():
            raise ValueError(f"ROI directory does not exist: {args.roi_dir}")
        
        mask_dir = Path(args.mask_dir)
        if not mask_dir.exists():
            raise ValueError(f"Mask directory does not exist: {args.mask_dir}")
        
        # Validate ImageJ path
        imagej_path = args.imagej_path or self.config.get('imagej_path')
        if not imagej_path:
            raise ValueError("ImageJ path not specified and not found in configuration")
        
        imagej_path_obj = Path(imagej_path)
        if not imagej_path_obj.exists():
            raise ValueError(f"ImageJ executable does not exist: {imagej_path}")
        
        return True
    
    def run(self, args: Optional[argparse.Namespace] = None) -> int:
        """
        Run the create cell masks command.
        
        Args:
            args: Parsed command line arguments (if None, will parse from sys.argv)
            
        Returns:
            int: Exit code (0 for success, non-zero for failure)
        """
        try:
            # Parse arguments if not provided
            if args is None:
                parser = self.create_parser()
                args = parser.parse_args()
            
            # Validate arguments
            self.validate_arguments(args)
            
            # Get ImageJ path
            imagej_path = args.imagej_path or self.config.get('imagej_path')
            
            # Create output directory if it doesn't exist
            output_dir = Path(args.output_dir)
            output_dir.mkdir(parents=True, exist_ok=True)
            
            # Delegate to application service
            success = self.service.create_cell_masks(
                roi_directory=args.roi_dir,
                mask_directory=args.mask_dir,
                output_directory=args.output_dir,
                imagej_path=imagej_path,
                auto_close=not args.no_auto_close
            )
            
            if success:
                print("✅ Cell mask creation completed successfully")
                return 0
            else:
                print("❌ Cell mask creation failed")
                return 1
                
        except ValueError as e:
            print(f"❌ Validation error: {e}")
            return 1
        except DomainError as e:
            print(f"❌ Domain error: {e}")
            return 1
        except Exception as e:
            print(f"❌ Unexpected error: {e}")
            return 1


def main():
    """Main entry point for the CLI."""
    cli = CreateCellMasksCLI()
    return cli.run()


if __name__ == "__main__":
    exit(main())
