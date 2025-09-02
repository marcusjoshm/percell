#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Duplicate ROIs Service for Single Cell Analysis Workflow

This service takes ROI files created from the segmentation channel and creates
copies with naming conventions matching each analysis channel. This allows
downstream scripts to find the appropriate ROI files for each channel.
"""

import os
import shutil
import re
from pathlib import Path
from typing import List, Dict, Any, Optional
from percell.domain.ports import FileSystemPort, LoggingPort


class DuplicateROIsService:
    """
    Service for duplicating ROI files for analysis channels.
    
    This service creates copies of ROI files with naming conventions that match
    each analysis channel, enabling downstream analysis scripts to find the
    appropriate ROI files for each channel.
    """
    
    def __init__(
        self,
        filesystem_port: FileSystemPort,
        logging_port: LoggingPort
    ):
        """
        Initialize the Duplicate ROIs Service.
        
        Args:
            filesystem_port: Port for file system operations
            logging_port: Port for logging operations
        """
        self.filesystem_port = filesystem_port
        self.logging_port = logging_port
        self.logger = self.logging_port.get_logger("DuplicateROIsService")
    
    def find_segmentation_roi_files(
        self,
        roi_dir: str,
        conditions: Optional[List[str]] = None,
        regions: Optional[List[str]] = None,
        timepoints: Optional[List[str]] = None,
        segmentation_channel: Optional[str] = None
    ) -> List[str]:
        """
        Locate ROI zip files corresponding to the segmentation channel, filtered by
        selected conditions/regions/timepoints.
        
        Args:
            roi_dir: Directory containing ROI files
            conditions: List of conditions to include
            regions: List of regions to include
            timepoints: List of timepoints to include
            segmentation_channel: Segmentation channel used for ROI generation
            
        Returns:
            List of paths to matching ROI files
        """
        try:
            roi_path = Path(roi_dir)
            if not self.filesystem_port.path_exists(roi_dir):
                self.logger.error(f"ROI directory not found: {roi_dir}")
                return []
            
            matched = []
            conditions = conditions or []
            regions = regions or []
            timepoints = timepoints or []
            
            # Iterate through condition directories
            for condition_dir in self.filesystem_port.list_directory(roi_dir):
                if condition_dir.startswith('.'):
                    continue
                
                condition_path = os.path.join(roi_dir, condition_dir)
                if not self.filesystem_port.is_directory(condition_path):
                    continue
                
                # Check if condition is in the filter list
                if conditions and condition_dir not in conditions:
                    continue
                
                # Look for ROI zip files directly under condition directory
                for item in self.filesystem_port.list_directory(condition_path):
                    if not item.endswith("_rois.zip"):
                        continue
                    
                    # Check segmentation channel filter
                    if segmentation_channel and segmentation_channel not in item:
                        continue
                    
                    # Check regions filter
                    if regions and not any(r in item for r in regions):
                        continue
                    
                    # Check timepoints filter
                    if timepoints and not any(t in item for t in timepoints):
                        continue
                    
                    matched.append(os.path.join(condition_path, item))
            
            self.logger.info(f"Found {len(matched)} ROI files matching criteria")
            return matched
            
        except Exception as e:
            self.logger.error(f"Error finding ROI files: {e}")
            return []
    
    def extract_channel_from_filename(self, filename: str) -> Optional[str]:
        """
        Extract channel name from ROI filename.
        
        Args:
            filename: ROI filename
            
        Returns:
            Channel name (e.g., 'ch00', 'ch01', etc.) or None if not found
        """
        try:
            # Look for channel pattern in filename
            match = re.search(r'_ch\d+_', filename)
            if match:
                return match.group(0).strip('_')
            return None
            
        except Exception as e:
            self.logger.error(f"Error extracting channel from filename: {e}")
            return None
    
    def create_roi_filename_for_channel(
        self,
        original_filename: str,
        original_channel: str,
        target_channel: str
    ) -> str:
        """
        Create a new ROI filename by replacing the channel.
        
        Args:
            original_filename: Original ROI filename
            original_channel: Original channel (e.g., 'ch00')
            target_channel: Target channel (e.g., 'ch02')
            
        Returns:
            New filename with target channel
        """
        try:
            if original_channel in original_filename:
                return original_filename.replace(original_channel, target_channel)
            
            # Insert the target channel before the suffix if no token present
            new_name = re.sub(r'(\.zip)$', f'_{target_channel}\\1', original_filename)
            return new_name
            
        except Exception as e:
            self.logger.error(f"Error creating filename for channel: {e}")
            return original_filename
    
    def duplicate_rois_for_channels(
        self,
        roi_dir: str,
        conditions: Optional[List[str]] = None,
        regions: Optional[List[str]] = None,
        timepoints: Optional[List[str]] = None,
        segmentation_channel: Optional[str] = None,
        channels: Optional[List[str]] = None,
        verbose: bool = False
    ) -> Dict[str, Any]:
        """
        Duplicate ROI files for each analysis channel.
        
        Args:
            roi_dir: Directory containing ROI files
            conditions: List of conditions to include
            regions: List of regions to include
            timepoints: List of timepoints to include
            segmentation_channel: Segmentation channel used for ROI generation
            channels: List of channel names to duplicate ROIs for
            verbose: Enable verbose logging
            
        Returns:
            Dictionary with results including success status and statistics
        """
        try:
            if not channels:
                return {
                    'success': False,
                    'error': 'No channels specified for duplication'
                }
            
            self.logger.info(f"Duplicating ROI files for analysis channels: {channels}")
            
            # Find ROI files for the segmentation channel using the provided selections
            roi_files = self.find_segmentation_roi_files(
                roi_dir, conditions, regions, timepoints, segmentation_channel
            )
            
            if not roi_files:
                return {
                    'success': False,
                    'error': f'No ROI files found in {roi_dir}'
                }
            
            self.logger.info(f"Found {len(roi_files)} ROI files to process")
            successful_copies = 0
            channels_processed = set()
            errors = []
            
            for roi_file in roi_files:
                if verbose:
                    self.logger.debug(f"Processing ROI file: {roi_file}")
                
                # Create a copy for each analysis channel different from segmentation channel
                for target_channel in channels:
                    if target_channel == segmentation_channel:
                        continue
                    
                    base_name = os.path.basename(roi_file)
                    if segmentation_channel and segmentation_channel in base_name:
                        new_name = base_name.replace(segmentation_channel, target_channel)
                    else:
                        # Insert the target channel before the suffix if no token present
                        new_name = re.sub(r'(\.zip)$', f'_{target_channel}\\1', base_name)
                    
                    new_path = os.path.join(os.path.dirname(roi_file), new_name)
                    
                    if verbose:
                        self.logger.debug(f"Creating ROI file for {target_channel}: {new_name}")
                    
                    try:
                        if not self.filesystem_port.path_exists(new_path):
                            # Read the original file and write the copy
                            original_content = self.filesystem_port.read_file(roi_file, binary=True)
                            self.filesystem_port.write_file(new_path, original_content, binary=True)
                        
                        successful_copies += 1
                        channels_processed.add(target_channel)
                        
                    except Exception as e:
                        error_msg = f"Failed to copy ROI file {roi_file} to {new_path}: {e}"
                        self.logger.error(error_msg)
                        errors.append(error_msg)
                        continue
            
            self.logger.info(
                f"Successfully created or verified ROI files for channels: {sorted(list(channels_processed))}"
            )
            
            return {
                'success': True,
                'total_files_processed': len(roi_files),
                'successful_copies': successful_copies,
                'channels_processed': sorted(list(channels_processed)),
                'errors': errors,
                'message': f'Successfully processed {len(roi_files)} ROI files for {len(channels_processed)} channels'
            }
            
        except Exception as e:
            error_msg = f"Error duplicating ROIs: {e}"
            self.logger.error(error_msg)
            return {
                'success': False,
                'error': error_msg
            }
    
    def validate_inputs(
        self,
        roi_dir: str,
        channels: Optional[List[str]] = None,
        segmentation_channel: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Validate inputs for ROI duplication.
        
        Args:
            roi_dir: Directory containing ROI files
            channels: List of channel names to duplicate ROIs for
            segmentation_channel: Segmentation channel used for ROI generation
            
        Returns:
            Dictionary with validation results
        """
        try:
            # Check if ROI directory exists
            if not self.filesystem_port.path_exists(roi_dir):
                return {
                    'valid': False,
                    'error': f'ROI directory does not exist: {roi_dir}'
                }
            
            if not self.filesystem_port.is_directory(roi_dir):
                return {
                    'valid': False,
                    'error': f'ROI path is not a directory: {roi_dir}'
                }
            
            # Check if channels are specified
            if not channels:
                return {
                    'valid': False,
                    'error': 'No channels specified for duplication'
                }
            
            # Check if segmentation channel is specified
            if not segmentation_channel:
                return {
                    'valid': False,
                    'error': 'Segmentation channel is required'
                }
            
            # Check if channels list contains valid channel names
            invalid_channels = [ch for ch in channels if not re.match(r'^ch\d+$', ch)]
            if invalid_channels:
                return {
                    'valid': False,
                    'error': f'Invalid channel names: {invalid_channels}. Expected format: ch00, ch01, etc.'
                }
            
            return {
                'valid': True,
                'message': 'Inputs validated successfully'
            }
            
        except Exception as e:
            return {
                'valid': False,
                'error': f'Error validating inputs: {e}'
            }
    
    def get_available_conditions(self, roi_dir: str) -> List[str]:
        """
        Get list of available conditions in the ROI directory.
        
        Args:
            roi_dir: Directory containing ROI files
            
        Returns:
            List of available condition names
        """
        try:
            conditions = []
            
            if not self.filesystem_port.path_exists(roi_dir):
                return conditions
            
            for item in self.filesystem_port.list_directory(roi_dir):
                item_path = os.path.join(roi_dir, item)
                if self.filesystem_port.is_directory(item_path) and not item.startswith('.'):
                    conditions.append(item)
            
            return sorted(conditions)
            
        except Exception as e:
            self.logger.error(f"Error getting available conditions: {e}")
            return []
    
    def get_available_regions(self, roi_dir: str) -> List[str]:
        """
        Get list of available regions from ROI filenames.
        
        Args:
            roi_dir: Directory containing ROI files
            
        Returns:
            List of available region names
        """
        try:
            regions = set()
            
            if not self.filesystem_port.path_exists(roi_dir):
                return []
            
            # Look for region patterns in ROI filenames
            for condition_dir in self.filesystem_port.list_directory(roi_dir):
                if condition_dir.startswith('.'):
                    continue
                
                condition_path = os.path.join(roi_dir, condition_dir)
                if not self.filesystem_port.is_directory(condition_path):
                    continue
                
                for item in self.filesystem_port.list_directory(condition_path):
                    if item.endswith("_rois.zip"):
                        # Extract region from filename (e.g., "R_1_t00_ch00_rois.zip" -> "R_1")
                        parts = item.split('_')
                        if len(parts) >= 2:
                            region = f"{parts[0]}_{parts[1]}"
                            regions.add(region)
            
            return sorted(list(regions))
            
        except Exception as e:
            self.logger.error(f"Error getting available regions: {e}")
            return []
    
    def get_available_timepoints(self, roi_dir: str) -> List[str]:
        """
        Get list of available timepoints from ROI filenames.
        
        Args:
            roi_dir: Directory containing ROI files
            
        Returns:
            List of available timepoint names
        """
        try:
            timepoints = set()
            
            if not self.filesystem_port.path_exists(roi_dir):
                return []
            
            # Look for timepoint patterns in ROI filenames
            for condition_dir in self.filesystem_port.list_directory(roi_dir):
                if condition_dir.startswith('.'):
                    continue
                
                condition_path = os.path.join(roi_dir, condition_dir)
                if not self.filesystem_port.is_directory(condition_path):
                    continue
                
                for item in self.filesystem_port.list_directory(condition_path):
                    if item.endswith("_rois.zip"):
                        # Extract timepoint from filename (e.g., "R_1_t00_ch00_rois.zip" -> "t00")
                        timepoint_match = re.search(r'_t(\d+)_', item)
                        if timepoint_match:
                            timepoints.add(f"t{timepoint_match.group(1)}")
            
            return sorted(list(timepoints))
            
        except Exception as e:
            self.logger.error(f"Error getting available timepoints: {e}")
            return []
