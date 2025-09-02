#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Cleanup Directories Service

This service provides functionality to clean up (delete) cells and masks
directories to free up disk space after analysis is complete.

Part of Microscopy Single-Cell Analysis Pipeline
"""

import os
import shutil
import logging
from pathlib import Path
from typing import List, Dict, Tuple, Optional

from percell.domain.ports import FileSystemPort, LoggingPort


class CleanupDirectoriesService:
    """
    Service for cleaning up analysis directories to free up disk space.
    
    This service implements the cleanup functionality previously contained in
    the cleanup_directories.py module, following hexagonal architecture principles.
    """
    
    def __init__(
        self,
        filesystem_port: FileSystemPort,
        logging_port: LoggingPort
    ):
        """
        Initialize the cleanup directories service.
        
        Args:
            filesystem_port: Port for file system operations
            logging_port: Port for logging operations
        """
        self.filesystem_port = filesystem_port
        self.logging_port = logging_port
        self.logger = logging_port.get_logger("CleanupDirectoriesService")
    
    def get_directory_size(self, path: Path) -> int:
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
                            self.logger.debug(f"Cannot access file {fp}: {e}")
        except Exception as e:
            self.logger.error(f"Error calculating size for {path}: {e}")
        return total
    
    def format_size(self, size_bytes: int) -> str:
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
    
    def scan_cleanup_directories(
        self,
        output_dir: str,
        include_cells: bool = True,
        include_masks: bool = True,
        include_combined_masks: bool = False,
        include_grouped_cells: bool = False,
        include_grouped_masks: bool = False
    ) -> Dict[str, Dict]:
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
        
        cleanup_info = {}
        
        for dir_name, include in dir_config.items():
            if not include:
                continue
                
            dir_path = output_path / dir_name
            exists = dir_path.exists() and dir_path.is_dir()
            
            if exists:
                size_bytes = self.get_directory_size(dir_path)
                size_formatted = self.format_size(size_bytes)
            else:
                size_bytes = 0
                size_formatted = "0 B"
            
            cleanup_info[dir_name] = {
                'path': str(dir_path),
                'exists': exists,
                'size_bytes': size_bytes,
                'size_formatted': size_formatted
            }
        
        return cleanup_info
    
    def cleanup_directories(
        self,
        output_dir: str,
        directories_to_clean: List[str],
        dry_run: bool = True,
        confirm: bool = False
    ) -> Dict[str, Dict]:
        """
        Clean up specified directories by deleting them.
        
        Args:
            output_dir (str): Base output directory path
            directories_to_clean (List[str]): List of directory names to clean up
            dry_run (bool): If True, only show what would be deleted without actually deleting
            confirm (bool): If True, skip confirmation prompts
            
        Returns:
            Dict: Results of cleanup operation for each directory
        """
        output_path = Path(output_dir)
        results = {}
        
        # Scan directories first to get size information
        scan_results = self.scan_cleanup_directories(
            output_dir,
            include_cells=True,
            include_masks=True,
            include_combined_masks=True,
            include_grouped_cells=True,
            include_grouped_masks=True
        )
        
        total_size_before = 0
        directories_found = []
        
        # Calculate total size and identify directories to clean
        for dir_name in directories_to_clean:
            if dir_name in scan_results:
                dir_info = scan_results[dir_name]
                if dir_info['exists']:
                    total_size_before += dir_info['size_bytes']
                    directories_found.append(dir_name)
        
        if not directories_found:
            self.logger.warning("No directories found to clean up")
            return results
        
        # Display cleanup summary
        total_size_formatted = self.format_size(total_size_before)
        self.logger.info(f"Cleanup Summary:")
        self.logger.info(f"  Directories to clean: {', '.join(directories_found)}")
        self.logger.info(f"  Total space to free: {total_size_formatted}")
        self.logger.info(f"  Mode: {'DRY RUN' if dry_run else 'ACTUAL CLEANUP'}")
        
        if not confirm and not dry_run:
            self.logger.warning("Set confirm=True to proceed with actual deletion")
            return results
        
        # Perform cleanup
        for dir_name in directories_found:
            dir_path = output_path / dir_name
            dir_info = scan_results[dir_name]
            
            try:
                if dry_run:
                    self.logger.info(f"[DRY RUN] Would delete: {dir_path} ({dir_info['size_formatted']})")
                    results[dir_name] = {
                        'status': 'dry_run',
                        'path': str(dir_path),
                        'size_freed': dir_info['size_formatted'],
                        'message': 'Would be deleted in actual cleanup'
                    }
                else:
                    # Actually delete the directory
                    if dir_path.exists():
                        shutil.rmtree(dir_path)
                        self.logger.info(f"Deleted: {dir_path} ({dir_info['size_formatted']})")
                        results[dir_name] = {
                            'status': 'deleted',
                            'path': str(dir_path),
                            'size_freed': dir_info['size_formatted'],
                            'message': 'Successfully deleted'
                        }
                    else:
                        self.logger.warning(f"Directory no longer exists: {dir_path}")
                        results[dir_name] = {
                            'status': 'not_found',
                            'path': str(dir_path),
                            'size_freed': '0 B',
                            'message': 'Directory not found during cleanup'
                        }
                        
            except Exception as e:
                error_msg = f"Error cleaning up {dir_name}: {e}"
                self.logger.error(error_msg)
                results[dir_name] = {
                    'status': 'error',
                    'path': str(dir_path),
                    'size_freed': '0 B',
                    'message': error_msg
                }
        
        # Final summary
        if dry_run:
            self.logger.info(f"[DRY RUN] Would free {total_size_formatted} of disk space")
        else:
            self.logger.info(f"Cleanup completed. Freed {total_size_formatted} of disk space")
        
        return results
    
    def cleanup_all_analysis_directories(
        self,
        output_dir: str,
        dry_run: bool = True,
        confirm: bool = False
    ) -> Dict[str, Dict]:
        """
        Clean up all analysis directories (cells, masks, combined_masks, grouped_cells, grouped_masks).
        
        Args:
            output_dir (str): Base output directory path
            dry_run (bool): If True, only show what would be deleted without actually deleting
            confirm (bool): If True, skip confirmation prompts
            
        Returns:
            Dict: Results of cleanup operation for all directories
        """
        all_directories = ['cells', 'masks', 'combined_masks', 'grouped_cells', 'grouped_masks']
        
        return self.cleanup_directories(
            output_dir=output_dir,
            directories_to_clean=all_directories,
            dry_run=dry_run,
            confirm=confirm
        )
    
    def cleanup_cells_and_masks_only(
        self,
        output_dir: str,
        dry_run: bool = True,
        confirm: bool = False
    ) -> Dict[str, Dict]:
        """
        Clean up only cells and masks directories (preserves grouped and combined data).
        
        Args:
            output_dir (str): Base output directory path
            dry_run (bool): If True, only show what would be deleted without actually deleting
            confirm (bool): If True, skip confirmation prompts
            
        Returns:
            Dict: Results of cleanup operation for cells and masks directories
        """
        basic_directories = ['cells', 'masks']
        
        return self.cleanup_directories(
            output_dir=output_dir,
            directories_to_clean=basic_directories,
            dry_run=dry_run,
            confirm=confirm
        )
