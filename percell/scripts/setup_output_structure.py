#!/usr/bin/env python
"""
Setup Output Structure - Cross-Platform Version

This script sets up the output directory structure for the microscopy analysis workflow.
It creates all the necessary directories but does NOT copy files yet.
Files will be copied later after data selection is complete.

Replaces the bash script with a cross-platform Python implementation.
"""
import sys
from pathlib import Path


# ANSI color codes for better readability (work on most terminals)
class Colors:
    """Terminal color codes."""
    RED = '\033[0;31m'
    GREEN = '\033[0;32m'
    BLUE = '\033[0;34m'
    YELLOW = '\033[1;33m'
    NC = '\033[0m'  # No Color

    @staticmethod
    def disable_on_windows():
        """Disable colors on Windows if colorama not available."""
        try:
            import colorama
            colorama.init()
        except ImportError:
            # Disable colors if colorama not available
            Colors.RED = ''
            Colors.GREEN = ''
            Colors.BLUE = ''
            Colors.YELLOW = ''
            Colors.NC = ''


# Initialize colors
if sys.platform == 'win32':
    Colors.disable_on_windows()


def print_color(message: str, color: str = Colors.NC):
    """Print colored message."""
    print(f"{color}{message}{Colors.NC}")


def print_directory_structure(output_dir: Path, max_depth: int = 3):
    """
    Print the directory structure.

    Args:
        output_dir: Root directory to display
        max_depth: Maximum depth to display
    """
    print_color("Final output directory structure:", Colors.BLUE)

    # Get all directories up to max_depth and sort them
    directories = [output_dir]

    def get_dirs_recursive(path: Path, current_depth: int = 0):
        """Recursively get directories up to max_depth."""
        if current_depth >= max_depth:
            return

        for item in sorted(path.iterdir()):
            if item.is_dir():
                directories.append(item)
                get_dirs_recursive(item, current_depth + 1)

    get_dirs_recursive(output_dir)

    # Print directory tree
    for directory in sorted(directories):
        # Calculate relative depth
        try:
            rel_path = directory.relative_to(output_dir)
            depth = len(rel_path.parts)
        except ValueError:
            depth = 0

        indent = "  " * depth
        print(f"{indent}{directory.name}/")


def setup_output_structure(input_dir: Path, output_dir: Path):
    """
    Set up the output directory structure.

    Creates all necessary directories for the microscopy analysis workflow.

    Args:
        input_dir: Path to input directory (for validation)
        output_dir: Path to output directory to create
    """
    print_color(f"Setting up output directory structure: {output_dir}", Colors.GREEN)

    # Create the main output directories
    print_color("Creating main output directories...", Colors.BLUE)

    # List of main directories to create
    main_directories = [
        "analysis",
        "cells",
        "combined_masks",
        "grouped_cells",
        "grouped_masks",
        "masks",
        "raw_data",
        "ROIs",
        "preprocessed",
    ]

    for dir_name in main_directories:
        dir_path = output_dir / dir_name
        dir_path.mkdir(parents=True, exist_ok=True)

    print_color("Base directory structure created", Colors.GREEN)

    # Note about raw_data subdirectories
    print_color(
        "Base raw_data directory created. Condition subdirectories will be created based on user selections.",
        Colors.BLUE
    )

    print_color("Output directory structure setup completed", Colors.GREEN)

    # Print final directory structure for verification
    print()
    print_directory_structure(output_dir)

    print()
    print_color("Setup complete!", Colors.GREEN)
    print_color("Note: Directory structure created. Files will be copied after data selection.", Colors.YELLOW)


def main():
    """Main entry point."""
    if len(sys.argv) != 3:
        print_color("Error: Missing required arguments", Colors.RED)
        print(f"Usage: {sys.argv[0]} <input_directory> <output_directory>")
        print("  <input_directory>: Path to the directory containing microscopy data")
        print("  <output_directory>: Path to the output directory for analysis")
        sys.exit(1)

    input_dir = Path(sys.argv[1])
    output_dir = Path(sys.argv[2])

    # Check if input directory exists
    if not input_dir.exists():
        print_color(f"Error: Input directory does not exist: {input_dir}", Colors.RED)
        sys.exit(1)

    if not input_dir.is_dir():
        print_color(f"Error: Input path is not a directory: {input_dir}", Colors.RED)
        sys.exit(1)

    try:
        setup_output_structure(input_dir, output_dir)
        sys.exit(0)
    except Exception as e:
        print_color(f"Error: {e}", Colors.RED)
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
