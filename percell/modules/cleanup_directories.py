#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Cleanup Directories Module
===========================

This module provides functionality to clean up (delete) cells and masks
directories to free up disk space after analysis is complete.

Part of Microscopy Single-Cell Analysis Pipeline
"""

import os
import shutil
import argparse
import logging
import sys
from pathlib import Path
from typing import List, Dict, Tuple, Optional
import json

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s', stream=sys.stdout)
logger = logging.getLogger(__name__)


def get_directory_size(path: Path) -> int:
    """
    Calculate the total size of a directory in bytes.
    
    Args:
        path (Path): Directory path to calculate size for
        
    Returns:
        int: Total size in bytes
    """
    total = 0
    try:
        if path.exists() and path.is_dir():
            for dirpath, dirnames, filenames in os.walk(path):
                for filename in filenames:
                    fp = os.path.join(dirpath, filename)
                    try:
                        total += os.path.getsize(fp)
                    except (OSError, IOError) as e:
                        logger.debug(f"Cannot access file {fp}: {e}")
    except Exception as e:
        logger.error(f"Error calculating size for {path}: {e}")
    return total


def format_size(size_bytes: int) -> str:
    """
    Format size in bytes to human-readable format.
    
    Args:
        size_bytes (int): Size in bytes
        
    Returns:
        str: Human-readable size string
    """
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.2f} PB"


def scan_cleanup_directories(output_dir: str, 
                           include_cells: bool = True,
                           include_masks: bool = True,
                           include_combined_masks: bool = False,
                           include_grouped_cells: bool = False,
                           include_grouped_masks: bool = False) -> Dict[str, Dict]:
    """
    Scan directories that can be cleaned up and calculate their sizes.
    
    Args:
        output_dir (str): Base output directory path
        include_cells (bool): Include cells directory
        include_masks (bool): Include masks directory
        include_combined_masks (bool): Include combined_masks directory
        include_grouped_cells (bool): Include grouped_cells directory
        include_grouped_masks (bool): Include grouped_masks directory
        
    Returns:
        Dict: Dictionary with directory names as keys and info dict as values
              Each info dict contains 'path', 'exists', 'size_bytes', 'size_formatted'
    """
    output_path = Path(output_dir)
    
    # Define directory names to check based on parameters
    dir_config = {
        'cells': include_cells,
        'masks': include_masks,
        'combined_masks': include_combined_masks,
        'grouped_cells': include_grouped_cells,
        'grouped_masks': include_grouped_masks
    }
    
    directories_info = {}
    
    for dir_name, should_include in dir_config.items():
        if should_include:
            dir_path = output_path / dir_name
            size_bytes = get_directory_size(dir_path) if dir_path.exists() else 0
            
            directories_info[dir_name] = {
                'path': str(dir_path),
                'exists': dir_path.exists(),
                'size_bytes': size_bytes,
                'size_formatted': format_size(size_bytes)
            }
    
    return directories_info


def cleanup_directories(output_dir: str,
                       delete_cells: bool = False,
                       delete_masks: bool = False,
                       delete_combined_masks: bool = False,
                       delete_grouped_cells: bool = False,
                       delete_grouped_masks: bool = False,
                       dry_run: bool = False,
                       force: bool = False) -> Tuple[int, int]:
    """
    Clean up (empty contents of) specified directories to free up space.
    
    Args:
        output_dir (str): Base output directory path
        delete_cells (bool): Empty cells directory
        delete_masks (bool): Empty masks directory
        delete_combined_masks (bool): Empty combined_masks directory
        delete_grouped_cells (bool): Empty grouped_cells directory
        delete_grouped_masks (bool): Empty grouped_masks directory
        dry_run (bool): If True, only show what would be deleted without actually deleting
        force (bool): If True, skip confirmation prompt
        
    Returns:
        Tuple[int, int]: (number of directories emptied, total bytes freed)
    """
    output_path = Path(output_dir)
    
    if not output_path.exists():
        logger.error(f"Output directory does not exist: {output_dir}")
        return 0, 0
    
    # Scan directories first
    directories_info = scan_cleanup_directories(
        output_dir,
        include_cells=delete_cells,
        include_masks=delete_masks,
        include_combined_masks=delete_combined_masks,
        include_grouped_cells=delete_grouped_cells,
        include_grouped_masks=delete_grouped_masks
    )
    
    if not directories_info:
        logger.info("No directories selected for cleanup.")
        return 0, 0
    
    # Calculate total size
    total_size = sum(info['size_bytes'] for info in directories_info.values())
    
    # Display what will be emptied
    logger.info("=" * 80)
    logger.info("Directories to be emptied:")
    logger.info("-" * 80)
    
    for dir_name, info in directories_info.items():
        if info['exists']:
            logger.info(f"  • {dir_name:<20} {info['size_formatted']:>15}")
        else:
            logger.info(f"  • {dir_name:<20} {'(not found)':>15}")
    
    logger.info("-" * 80)
    logger.info(f"  Total space to free: {format_size(total_size):>15}")
    logger.info("=" * 80)
    
    if dry_run:
        logger.info("\n🔍 DRY RUN MODE - No files will be deleted")
        return 0, 0
    
    # Ask for confirmation if not forced
    if not force:
        logger.info("\n⚠️  WARNING: This action cannot be undone!")
        response = input("Are you sure you want to empty these directories? (yes/no): ").strip().lower()
        if response not in ['yes', 'y']:
            logger.info("Cleanup cancelled by user.")
            return 0, 0
    
    # Perform emptying
    emptied_count = 0
    freed_bytes = 0
    
    logger.info("\nEmptying directories...")
    for dir_name, info in directories_info.items():
        if info['exists']:
            dir_path = Path(info['path'])
            try:
                dir_size = info['size_bytes']
                # Remove all contents but keep the directory
                for item in dir_path.iterdir():
                    if item.is_file():
                        item.unlink()
                    elif item.is_dir():
                        shutil.rmtree(item)
                emptied_count += 1
                freed_bytes += dir_size
                logger.info(f"  ✅ Emptied: {dir_name} (freed {format_size(dir_size)})")
            except Exception as e:
                logger.error(f"  ❌ Failed to empty {dir_name}: {e}")
    
    logger.info("\n" + "=" * 80)
    logger.info(f"Cleanup complete!")
    logger.info(f"  • Directories emptied: {emptied_count}")
    logger.info(f"  • Total space freed: {format_size(freed_bytes)}")
    logger.info("=" * 80)
    
    return emptied_count, freed_bytes


def interactive_cleanup(output_dir: str) -> None:
    """
    Interactive mode for selecting directories to empty.
    
    Args:
        output_dir (str): Base output directory path
    """
    output_path = Path(output_dir)
    
    if not output_path.exists():
        logger.error(f"Output directory does not exist: {output_dir}")
        return
    
    logger.info("\n" + "=" * 80)
    logger.info("Interactive Directory Cleanup")
    logger.info("=" * 80)
    logger.info(f"Output directory: {output_dir}\n")
    
    # Scan all possible directories
    all_dirs = scan_cleanup_directories(
        output_dir,
        include_cells=True,
        include_masks=True,
        include_combined_masks=False,
        include_grouped_cells=False,
        include_grouped_masks=False
    )
    
    # Display available directories
    logger.info("Available directories:")
    logger.info("-" * 80)
    
    available_dirs = []
    for dir_name, info in all_dirs.items():
        if info['exists']:
            logger.info(f"  [{len(available_dirs) + 1}] {dir_name:<20} {info['size_formatted']:>15}")
            available_dirs.append(dir_name)
        else:
            logger.info(f"  [ ] {dir_name:<20} {'(not found)':>15}")
    
    if not available_dirs:
        logger.info("\nNo directories found to empty.")
        return
    
    logger.info("\n  [A] Select all")
    logger.info("  [Q] Quit without cleaning")
    logger.info("-" * 80)
    
    # Get user selection
    while True:
        selection = input("\nEnter your selection (comma-separated numbers, A for all, Q to quit): ").strip().upper()
        
        if selection == 'Q':
            logger.info("Cleanup cancelled.")
            return
        
        selected_dirs = []
        
        if selection == 'A':
            selected_dirs = available_dirs
        else:
            try:
                indices = [int(x.strip()) for x in selection.split(',')]
                for idx in indices:
                    if 1 <= idx <= len(available_dirs):
                        selected_dirs.append(available_dirs[idx - 1])
                    else:
                        logger.warning(f"Invalid selection: {idx}")
            except ValueError:
                logger.error("Invalid input. Please enter numbers separated by commas.")
                continue
        
        if selected_dirs:
            # Prepare emptying arguments
            delete_args = {
                'delete_cells': 'cells' in selected_dirs,
                'delete_masks': 'masks' in selected_dirs,
                'delete_combined_masks': 'combined_masks' in selected_dirs,
                'delete_grouped_cells': 'grouped_cells' in selected_dirs,
                'delete_grouped_masks': 'grouped_masks' in selected_dirs
            }
            
            # Perform cleanup
            cleanup_directories(output_dir, **delete_args, dry_run=False, force=False)
            break
        else:
            logger.warning("No valid directories selected.")


def main():
    """Main entry point for the cleanup module."""
    parser = argparse.ArgumentParser(
        description="Empty cells and masks directories to free up disk space (preserves grouped and combined data)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Interactive mode (cells and masks only)
  %(prog)s --output /path/to/output --interactive
  
  # Empty cells and masks directories
  %(prog)s --output /path/to/output --delete-cells --delete-masks
  
  # Dry run to see what would be emptied
  %(prog)s --output /path/to/output --delete-cells --delete-masks --dry-run
  
  # Force emptying without confirmation
  %(prog)s --output /path/to/output --delete-cells --force
  
  # Empty all cell and mask related directories (including grouped/combined)
  %(prog)s --output /path/to/output --delete-all
        """
    )
    
    parser.add_argument("--output", "-o", required=True, 
                       help="Output directory containing subdirectories to clean")
    
    # Interactive mode
    parser.add_argument("--interactive", "-i", action="store_true",
                       help="Interactive mode for selecting directories")
    
    # Specific directory options
    parser.add_argument("--delete-cells", action="store_true",
                       help="Empty cells directory")
    parser.add_argument("--delete-masks", action="store_true",
                       help="Empty masks directory")
    parser.add_argument("--delete-combined-masks", action="store_true",
                       help="Empty combined_masks directory")
    parser.add_argument("--delete-grouped-cells", action="store_true",
                       help="Empty grouped_cells directory")
    parser.add_argument("--delete-grouped-masks", action="store_true",
                       help="Empty grouped_masks directory")
    
    # Convenience option
    parser.add_argument("--delete-all", action="store_true",
                       help="Empty all cell and mask related directories")
    
    # Control options
    parser.add_argument("--dry-run", "-n", action="store_true",
                       help="Show what would be deleted without actually deleting")
    parser.add_argument("--force", "-f", action="store_true",
                       help="Skip confirmation prompt")
    parser.add_argument("--verbose", "-v", action="store_true",
                       help="Enable verbose debug logging")
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
        logger.setLevel(logging.DEBUG)
        logger.info("Verbose logging enabled.")
    
    # Handle interactive mode
    if args.interactive:
        interactive_cleanup(args.output)
    else:
        # Check if any deletion options were specified
        if args.delete_all:
            delete_cells = True
            delete_masks = True
            delete_combined_masks = True
            delete_grouped_cells = True
            delete_grouped_masks = True
        else:
            delete_cells = args.delete_cells
            delete_masks = args.delete_masks
            delete_combined_masks = args.delete_combined_masks
            delete_grouped_cells = args.delete_grouped_cells
            delete_grouped_masks = args.delete_grouped_masks
        
        # Check if at least one directory was selected
        if not any([delete_cells, delete_masks, delete_combined_masks, 
                   delete_grouped_cells, delete_grouped_masks]):
            logger.error("No directories selected for cleanup.")
            logger.info("Use --help to see available options.")
            sys.exit(1)
        
        # Perform cleanup
        cleanup_directories(
            args.output,
            delete_cells=delete_cells,
            delete_masks=delete_masks,
            delete_combined_masks=delete_combined_masks,
            delete_grouped_cells=delete_grouped_cells,
            delete_grouped_masks=delete_grouped_masks,
            dry_run=args.dry_run,
            force=args.force
        )


if __name__ == "__main__":
    main()
