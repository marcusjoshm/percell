#!/usr/bin/env python
"""
Prepare Input Structure - Cross-Platform Version

This script prepares the input directory structure for the microscopy analysis workflow.
It handles three possible input structures:
1. .tif files directly in the input directory -> moves to condition_1/
2. One layer of subdirectories containing .tif files -> keeps as condition directories
3. Two layers of subdirectories containing .tif files -> flattens timepoint subdirs into condition

Timepoint information is now extracted from filename tokens (_tNN) rather than directory structure.

Replaces the bash script with a cross-platform Python implementation.
"""
import os
import sys
import re
import shutil
from pathlib import Path
from typing import List


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


def count_tif_files(directory: Path) -> int:
    """
    Count .tif files in a directory (non-recursive).

    Args:
        directory: Directory to search

    Returns:
        Number of .tif files found
    """
    return len(list(directory.glob("*.tif")))


def has_subdirectories(directory: Path) -> bool:
    """
    Check if a directory contains subdirectories.

    Args:
        directory: Directory to check

    Returns:
        True if subdirectories exist, False otherwise
    """
    return any(item.is_dir() for item in directory.iterdir())


def has_timepoint_pattern(filename: str) -> bool:
    """
    Check if a filename contains a timepoint pattern (tXX).

    Args:
        filename: Filename to check

    Returns:
        True if pattern found, False otherwise
    """
    return bool(re.search(r't\d+', filename))


def has_channel_pattern(filename: str) -> bool:
    """
    Check if a filename contains a channel pattern (chXX).

    Args:
        filename: Filename to check

    Returns:
        True if pattern found, False otherwise
    """
    return bool(re.search(r'ch\d+', filename))


def process_condition_directory(condition_dir: Path):
    """
    Process files in a condition directory.

    Adds required patterns (timepoint and channel) to filenames if missing.
    Timepoint information is stored in the filename, not directory structure.

    Args:
        condition_dir: Path to condition directory containing .tif files
    """
    print_color(f"Processing files in: {condition_dir}", Colors.BLUE)
    region_counter = 1

    for tif_file in condition_dir.glob("*.tif"):
        if tif_file.is_file():
            filename = tif_file.name
            new_filename = filename

            # Check if missing timepoint pattern
            if not has_timepoint_pattern(filename):
                print_color(f"File missing timepoint pattern: {filename}", Colors.YELLOW)
                new_filename = new_filename.replace('.tif', '_t00.tif')
                print_color(f"Adding timepoint pattern: {new_filename}", Colors.GREEN)

            # Check if missing channel pattern
            if not has_channel_pattern(new_filename):
                print_color(f"File missing channel pattern: {new_filename}", Colors.YELLOW)
                new_filename = new_filename.replace('.tif', '_ch00.tif')
                print_color(f"Adding channel pattern: {new_filename}", Colors.GREEN)

            # Rename file if needed
            if new_filename != filename:
                new_path = condition_dir / new_filename
                tif_file.rename(new_path)
                filename = new_filename

            # Each file is considered its own region
            print_color(f"File will be treated as Region {region_counter}: {filename}", Colors.GREEN)
            region_counter += 1


def remove_metadata_directories(input_dir: Path):
    """
    Remove all MetaData directories at any level.

    Args:
        input_dir: Root directory to search
    """
    print_color("Searching for and removing MetaData directories...", Colors.BLUE)

    metadata_dirs = list(input_dir.rglob("MetaData"))

    for metadata_dir in metadata_dirs:
        if metadata_dir.is_dir():
            print_color(f"Removing MetaData directory: {metadata_dir}", Colors.YELLOW)
            shutil.rmtree(metadata_dir)

    # Report results
    remaining = len(list(input_dir.rglob("MetaData")))
    if remaining == 0:
        print_color("No MetaData directories found or all have been successfully removed", Colors.GREEN)
    else:
        print_color(f"Warning: {remaining} MetaData directories could not be removed", Colors.RED)


def print_directory_structure(input_dir: Path):
    """
    Print the final directory structure.

    Args:
        input_dir: Root directory to display
    """
    print_color("Final directory structure:", Colors.BLUE)

    # Get all directories and sort them
    directories = sorted([input_dir] + list(input_dir.rglob("*")))

    for directory in directories:
        if directory.is_dir():
            # Calculate relative depth
            try:
                rel_path = directory.relative_to(input_dir)
                depth = len(rel_path.parts)
            except ValueError:
                depth = 0

            indent = "  " * depth
            print(f"{indent}{directory.name}/")


def print_tif_files(input_dir: Path):
    """
    Print all .tif files found.

    Args:
        input_dir: Root directory to search
    """
    print_color("Final .tif files:", Colors.BLUE)

    tif_files = sorted(input_dir.rglob("*.tif"))

    for tif_file in tif_files:
        rel_path = tif_file.relative_to(input_dir)
        print(f"  {rel_path}")


def prepare_input_structure(input_dir: Path):
    """
    Main function to prepare input directory structure.

    Args:
        input_dir: Path to input directory
    """
    print_color(f"Preparing input directory structure: {input_dir}", Colors.GREEN)

    # Remove MetaData directories
    remove_metadata_directories(input_dir)

    # Count .tif files directly in the input directory
    tif_count = count_tif_files(input_dir)

    if tif_count > 0:
        # Case 1: .tif files are directly in the input directory
        print_color(f"Found {tif_count} .tif files directly in input directory", Colors.BLUE)
        print_color("Creating condition_1/ structure and moving files", Colors.YELLOW)

        # Create the directory structure (flat - no timepoint subdirectory)
        target_dir = input_dir / "condition_1"
        target_dir.mkdir(parents=True, exist_ok=True)

        # Move all .tif files into the new structure
        for tif_file in input_dir.glob("*.tif"):
            if tif_file.is_file():
                shutil.move(str(tif_file), str(target_dir / tif_file.name))

        # Process files in the condition directory
        process_condition_directory(target_dir)

        print_color("Successfully reorganized .tif files into condition_1/", Colors.GREEN)

    else:
        # Check for subdirectories in the input dir
        if has_subdirectories(input_dir):
            print_color("Found subdirectories in the input directory", Colors.BLUE)

            # Iterate through each subdirectory
            for subdir in input_dir.iterdir():
                if not subdir.is_dir() or subdir.name == "MetaData":
                    continue

                # Count .tif files in this subdirectory
                subdir_tif_count = count_tif_files(subdir)

                if subdir_tif_count > 0:
                    # Case 2: One layer of subdirectories with .tif files
                    # Files are already in the right place (condition directory)
                    condition_name = subdir.name
                    print_color(f"Found {subdir_tif_count} .tif files in: {condition_name}", Colors.BLUE)

                    # Process files in the condition directory (add tokens if missing)
                    process_condition_directory(subdir)

                    print_color(f"Condition {condition_name}/ structure is correct", Colors.GREEN)

                else:
                    # Check if this might be a condition directory with subdirectories
                    if has_subdirectories(subdir):
                        condition_name = subdir.name
                        print_color(f"Subdirectory {condition_name} has nested subdirs", Colors.BLUE)

                        # Check subdirectories for .tif files and flatten them
                        tif_files_found = False

                        for nested_dir in subdir.iterdir():
                            if nested_dir.is_dir():
                                nested_tif_count = count_tif_files(nested_dir)

                                if nested_tif_count > 0:
                                    tif_files_found = True
                                    nested_name = nested_dir.name
                                    print_color(
                                        f"Found {nested_tif_count} .tif files in "
                                        f"{condition_name}/{nested_name}",
                                        Colors.BLUE
                                    )
                                    print_color(
                                        f"Flattening: moving files to {condition_name}/",
                                        Colors.YELLOW
                                    )

                                    # Move files up to condition directory
                                    for tif_file in nested_dir.glob("*.tif"):
                                        if tif_file.is_file():
                                            dest = subdir / tif_file.name
                                            shutil.move(str(tif_file), str(dest))

                                    # Remove empty nested directory
                                    try:
                                        nested_dir.rmdir()
                                        print_color(
                                            f"Removed empty directory: {nested_name}",
                                            Colors.BLUE
                                        )
                                    except OSError:
                                        # Directory not empty, leave it
                                        pass

                        if tif_files_found:
                            # Process all files now in condition directory
                            process_condition_directory(subdir)
                            print_color(
                                f"Flattened {condition_name}/ structure",
                                Colors.GREEN
                            )
                        else:
                            print_color(
                                f"No .tif files found in subdirs of {condition_name}",
                                Colors.YELLOW
                            )
                    else:
                        print_color(
                            f"No .tif files or subdirs found in {subdir.name}",
                            Colors.YELLOW
                        )
        else:
            print_color("No .tif files or subdirectories found in the input directory", Colors.YELLOW)

    print_color("Input directory preparation completed", Colors.GREEN)

    # Print final directory structure for verification
    print()
    print_directory_structure(input_dir)

    # Print final TIFF files for verification
    print()
    print_tif_files(input_dir)


def main():
    """Main entry point."""
    if len(sys.argv) != 2:
        print_color("Error: Missing input directory", Colors.RED)
        print(f"Usage: {sys.argv[0]} <input_directory>")
        print("  <input_directory>: Path to the directory containing microscopy data")
        sys.exit(1)

    input_dir = Path(sys.argv[1])

    # Check if input directory exists
    if not input_dir.exists():
        print_color(f"Error: Input directory does not exist: {input_dir}", Colors.RED)
        sys.exit(1)

    if not input_dir.is_dir():
        print_color(f"Error: Path is not a directory: {input_dir}", Colors.RED)
        sys.exit(1)

    try:
        prepare_input_structure(input_dir)
        sys.exit(0)
    except Exception as e:
        print_color(f"Error: {e}", Colors.RED)
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
