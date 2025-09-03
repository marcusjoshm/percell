#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Bin Images Service

This service bins microscopy images for cell segmentation by performing
4x4 binning and saving the processed images to the output directory.

Part of Microscopy Single-Cell Analysis Pipeline
"""

import os
import re
import numpy as np
from pathlib import Path
from typing import List, Set, Optional, Dict, Tuple
from skimage import io, exposure
from skimage.transform import downscale_local_mean
import tifffile

from percell.domain.ports import FileSystemPort, LoggingPort


class BinImagesService:
    """
    Service for binning microscopy images for cell segmentation.
    
    This service implements the image binning functionality previously contained in
    the bin_images.py module, following hexagonal architecture principles.
    """
    
    def __init__(
        self,
        filesystem_port: FileSystemPort,
        logging_port: LoggingPort
    ):
        """
        Initialize the bin images service.
        
        Args:
            filesystem_port: Port for file system operations
            logging_port: Port for logging operations
        """
        self.filesystem_port = filesystem_port
        self.logging_port = logging_port
        self.logger = logging_port.get_logger("BinImagesService")
    
    def bin_image(self, image: np.ndarray, bin_factor: int = 4) -> np.ndarray:
        """
        Bin an image by the specified factor using local mean.
        
        Args:
            image (numpy.ndarray): Input image
            bin_factor (int): Binning factor
            
        Returns:
            numpy.ndarray: Binned image
        """
        return downscale_local_mean(image, (bin_factor, bin_factor))

    def bin_images(
        self,
        input_dir: str,
        output_dir: str,
        *,
        bin_factor: int = 4,
        conditions: Optional[List[str]] = None,
        regions: Optional[List[str]] = None,
        timepoints: Optional[List[str]] = None,
        channels: Optional[List[str]] = None,
    ) -> int:
        """
        Bin multiple images in a directory structure.
        
        Args:
            input_dir: Input directory containing images
            output_dir: Output directory for binned images
            bin_factor: Binning factor (default: 4)
            conditions: List of conditions to process
            regions: List of regions to process
            timepoints: List of timepoints to process
            channels: List of channels to process
            
        Returns:
            0 on success, 1 on failure
        """
        try:
            input_path = Path(input_dir)
            output_path = Path(output_dir)
            output_path.mkdir(parents=True, exist_ok=True)

            # Find TIFF images (both .tif and .tiff, case-insensitive)
            patterns = ["**/*.tif", "**/*.tiff", "**/*.TIF", "**/*.TIFF"]
            seen: Set[Path] = set()
            all_files: List[Path] = []
            for pat in patterns:
                for p in input_path.glob(pat):
                    if p not in seen:
                        seen.add(p)
                        all_files.append(p)
            
            self.logger.info(f"[Binning] Input dir: {input_path} | Found files: {len(all_files)}")
            if not all_files:
                # Early exit: nothing to process
                return 0

            # Convert selection lists to sets; treat None, [] or ["all"] as no filter
            selected_conditions = set(conditions) if conditions else None
            selected_regions = set(regions) if regions else None
            selected_timepoints = set(timepoints) if timepoints else None
            selected_channels = set(channels) if channels else None

            self.logger.info(
                f"[Binning] Filters -> conditions={selected_conditions} "
                f"regions={selected_regions} timepoints={selected_timepoints} "
                f"channels={selected_channels}"
            )

            processed = 0
            skipped_cond = skipped_region = skipped_time = skipped_chan = 0

            for file_path in all_files:
                try:
                    file_path = Path(file_path)
                    # Determine condition (top-level directory)
                    relative_path = file_path.relative_to(input_path)
                    current_condition = relative_path.parts[0] if len(relative_path.parts) > 1 else None
                    
                    # Apply condition filter only when requested
                    if selected_conditions and (not current_condition or current_condition not in selected_conditions):
                        skipped_cond += 1
                        continue

                    # Parse metadata from filename
                    filename = file_path.name
                    region, timepoint, channel = self._extract_metadata_from_filename(filename)

                    if selected_regions and (not region or region not in selected_regions):
                        skipped_region += 1
                        continue
                    if selected_timepoints and (not timepoint or timepoint not in selected_timepoints):
                        skipped_time += 1
                        continue
                    if selected_channels and (not channel or channel not in selected_channels):
                        self.logger.info(
                            f"[Binning] Skip by channel | file={filename} parsed={channel} filters={selected_channels}"
                        )
                        skipped_chan += 1
                        continue
                    
                    self.logger.info(
                        f"[Binning] Accept file: {filename} | cond={current_condition} "
                        f"region={region} time={timepoint} channel={channel}"
                    )

                    # Compute output path, preserving structure
                    out_file = output_path / relative_path.parent / (f"bin{bin_factor}x{bin_factor}_" + filename)
                    self.logger.info(f"[Binning] Output path: {out_file}")
                    out_file.parent.mkdir(parents=True, exist_ok=True)

                    # Read, bin, write
                    image = io.imread(file_path)
                    self.logger.info(f"[Binning] Read image: shape={getattr(image, 'shape', None)} dtype={getattr(image, 'dtype', None)}")
                    binned = self.bin_image(image, bin_factor)
                    out_array = binned.astype(image.dtype, copy=False)
                    
                    # Write binned image
                    io.imsave(out_file, out_array)
                    self.logger.info(f"[Binning] Wrote: {out_file}")
                    processed += 1

                except Exception as e:
                    self.logger.error(f"Error processing {file_path}: {e}")
                    continue

            # Log summary
            self.logger.info(
                f"[Binning] Summary -> processed={processed}, skipped: "
                f"cond={skipped_cond} region={skipped_region} timepoint={skipped_time} "
                f"channel={skipped_chan}"
            )

            return 0 if processed > 0 else 1

        except Exception as e:
            self.logger.error(f"Error in bin_images: {e}")
            return 1
    
    def _extract_metadata_from_filename(self, filename: str) -> Tuple[Optional[str], Optional[str], Optional[str]]:
        """
        Extract region, timepoint, and channel from filename.
        
        Args:
            filename (str): Filename to parse
            
        Returns:
            tuple: (region, timepoint, channel) or (None, None, None) if parsing fails
        """
        try:
            # Match region from filename based on actual naming convention in the dataset
            # Pattern for filenames like: 60min_washout_P_10_RAW_ch01_t00.tif
            region_pattern = r'(.+?)_(ch\d+)_(t\d+)'
            
            region_match = re.search(region_pattern, filename)
            if region_match:
                current_region = region_match.group(1)  # This will capture '60min_washout_P_10_RAW'
            else:
                # Fallback for other potential naming patterns
                # Try to extract everything before the channel and timepoint
                parts = filename.split('_')
                ch_index = -1
                t_index = -1
                for i, part in enumerate(parts):
                    if part.startswith('ch'):
                        ch_index = i
                    if part.startswith('t'):
                        t_index = i
                
                if ch_index > 0:  # If we found a channel marker
                    current_region = '_'.join(parts[:ch_index])
                else:
                    current_region = None
                    
                self.logger.debug(f"Fallback region extraction: {current_region} from {filename}")
            
            # Match timepoint and channel patterns (t00, ch01 format)
            timepoint_match = re.search(r'(t\d+)', filename)
            channel_match = re.search(r'(ch\d+)', filename)
            
            current_timepoint = timepoint_match.group(1) if timepoint_match else None
            current_channel = channel_match.group(1) if channel_match else None
            
            return current_region, current_timepoint, current_channel
            
        except Exception as e:
            self.logger.debug(f"Error extracting metadata from {filename}: {e}")
            return None, None, None
    
    def _should_process_file(
        self,
        file_path: Path,
        input_path: Path,
        selected_conditions: Optional[Set[str]],
        selected_regions: Optional[Set[str]],
        selected_timepoints: Optional[Set[str]],
        selected_channels: Optional[Set[str]]
    ) -> bool:
        """
        Determine if a file should be processed based on selection criteria.
        
        Args:
            file_path (Path): Path to the file to check
            input_path (Path): Base input directory path
            selected_conditions (Optional[Set[str]]): Set of selected conditions
            selected_regions (Optional[Set[str]]): Set of selected regions
            selected_timepoints (Optional[Set[str]]): Set of selected timepoints
            selected_channels (Optional[Set[str]]): Set of selected channels
            
        Returns:
            bool: True if file should be processed, False otherwise
        """
        try:
            # Extract condition from parent directory path
            # The condition is usually the first directory under the input directory
            relative_path = file_path.relative_to(input_path)
            if len(relative_path.parts) > 0:
                current_condition = relative_path.parts[0]
            else:
                self.logger.warning(f"Could not determine condition directory for {file_path}. Skipping.")
                return False
            
            # Extract region, timepoint, channel from filename
            filename = file_path.name
            current_region, current_timepoint, current_channel = self._extract_metadata_from_filename(filename)
            
            self.logger.debug(f"Parsed metadata - Condition: {current_condition}, Region: {current_region}, Timepoint: {current_timepoint}, Channel: {current_channel}")
            
            # Apply filters
            if selected_conditions is not None and current_condition not in selected_conditions:
                return False
            
            if selected_regions is not None and (not current_region or current_region not in selected_regions):
                self.logger.debug(f"Skipping file due to region filter: {current_region} not in {selected_regions}")
                return False
            
            if selected_timepoints is not None and (not current_timepoint or current_timepoint not in selected_timepoints):
                self.logger.debug(f"Skipping file due to timepoint filter: {current_timepoint} not in {selected_timepoints}")
                return False
                
            if selected_channels is not None and (not current_channel or current_channel not in selected_channels):
                self.logger.debug(f"Skipping file due to channel filter: {current_channel} not in {selected_channels}")
                return False
            
            return True
            
        except Exception as e:
            self.logger.warning(f"Could not parse metadata or apply filters for {file_path}. Skipping. Error: {e}")
            return False
    
    def _process_single_image(
        self,
        file_path: Path,
        input_path: Path,
        output_path: Path,
        bin_factor: int
    ) -> bool:
        """
        Process a single image file.
        
        Args:
            file_path (Path): Path to the input image file
            input_path (Path): Base input directory path
            output_path (Path): Base output directory path
            bin_factor (int): Binning factor to apply
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Determine output path maintaining directory structure
            # For example: input/condition/timepoint_1/file.tif -> output/condition/timepoint_1/bin4x4_file.tif
            relative_path = file_path.relative_to(input_path)
            output_file = output_path / relative_path.parent / f"bin4x4_{file_path.name}"
            
            # Create output directory structure
            output_file.parent.mkdir(parents=True, exist_ok=True)

            # Read the image
            image = io.imread(file_path)
            
            # Bin the image
            binned_image = self.bin_image(image, bin_factor=bin_factor)
            
            # Save the processed image
            tifffile.imwrite(output_file, binned_image.astype(image.dtype))
            
            self.logger.info(f"Saved binned image to {output_file}")
            return True

        except Exception as e:
            self.logger.error(f"Error processing or saving file {file_path}: {e}")
            return False
    
    def process_images(
        self,
        input_dir: str,
        output_dir: str,
        bin_factor: int = 4,
        target_conditions: Optional[List[str]] = None,
        target_regions: Optional[List[str]] = None,
        target_timepoints: Optional[List[str]] = None,
        target_channels: Optional[List[str]] = None
    ) -> Dict[str, int]:
        """
        Process images in input directory and save to output directory, filtering by selections.
        
        Args:
            input_dir (str): Input directory path
            output_dir (str): Output directory path
            bin_factor (int): Binning factor
            target_conditions (Optional[List[str]]): List of conditions to process
            target_regions (Optional[List[str]]): List of regions to process
            target_timepoints (Optional[List[str]]): List of timepoints to process
            target_channels (Optional[List[str]]): List of channels to process
            
        Returns:
            Dict[str, int]: Summary of processing results
        """
        input_path = Path(input_dir)
        output_path = Path(output_dir)
        
        self.logger.info(f"Starting image binning process.")
        self.logger.info(f"Input directory: {input_path}")
        self.logger.info(f"Output directory: {output_path}")
        self.logger.info(f"Bin factor: {bin_factor}")
        self.logger.info(f"Target Conditions: {target_conditions}")
        self.logger.info(f"Target Regions: {target_regions}")
        self.logger.info(f"Target Timepoints: {target_timepoints}")
        self.logger.info(f"Target Channels: {target_channels}")
        
        # Create output directory if it doesn't exist
        output_path.mkdir(parents=True, exist_ok=True)
        
        # Find all .tif files recursively
        all_files = list(input_path.glob("**/*.tif"))
        self.logger.info(f"Found {len(all_files)} total .tif files in {input_path}.")

        # Convert selection lists to sets for efficient lookup, if they exist
        # Handle 'all' special value for selections
        all_selection = {'all'}
        
        if target_conditions and all_selection.issubset(set(target_conditions)):
            selected_conditions = None  # Process all conditions
        else:
            selected_conditions = set(target_conditions) if target_conditions else None
            
        if target_regions and all_selection.issubset(set(target_regions)):
            selected_regions = None  # Process all regions
        else:
            selected_regions = set(target_regions) if target_regions else None
            
        if target_timepoints and all_selection.issubset(set(target_timepoints)):
            selected_timepoints = None  # Process all timepoints
        else: 
            selected_timepoints = set(target_timepoints) if target_timepoints else None
            
        if target_channels and all_selection.issubset(set(target_channels)):
            selected_channels = None  # Process all channels
        else:
            selected_channels = set(target_channels) if target_channels else None
            
        self.logger.info(f"Filter sets created - Conditions: {selected_conditions}, Regions: {selected_regions}, Timepoints: {selected_timepoints}, Channels: {selected_channels}")

        processed_count = 0
        skipped_count = 0
        error_count = 0
        
        for file_path in all_files:
            # Convert to Path object for easier manipulation
            file_path = Path(file_path)
            
            # Check if file should be processed
            if not self._should_process_file(
                file_path, input_path, selected_conditions, selected_regions, 
                selected_timepoints, selected_channels
            ):
                skipped_count += 1
                continue
            
            self.logger.info(f"Processing {file_path}...")
            
            # Process the image
            if self._process_single_image(file_path, input_path, output_path, bin_factor):
                processed_count += 1
            else:
                error_count += 1
        
        # Log summary
        self.logger.info("Image binning completed.")
        self.logger.info(f"Processed {processed_count} files matching the criteria.")
        self.logger.info(f"Skipped {skipped_count} files due to filters.")
        self.logger.info(f"Errors encountered: {error_count} files.")
        
        return {
            'processed': processed_count,
            'skipped': skipped_count,
            'errors': error_count,
            'total_found': len(all_files)
        }
    
    def get_available_conditions(self, input_dir: str) -> List[str]:
        """
        Get list of available conditions in the input directory.
        
        Args:
            input_dir (str): Input directory path
            
        Returns:
            List[str]: List of available condition names
        """
        input_path = Path(input_dir)
        conditions = []
        
        if input_path.exists() and input_path.is_dir():
            for item in input_path.iterdir():
                if item.is_dir():
                    conditions.append(item.name)
        
        return sorted(conditions)
    
    def get_available_regions(self, input_dir: str) -> List[str]:
        """
        Get list of available regions from filenames in the input directory.
        
        Args:
            input_dir (str): Input directory path
            
        Returns:
            List[str]: List of available region names
        """
        input_path = Path(input_dir)
        regions = set()
        
        if input_path.exists() and input_path.is_dir():
            for file_path in input_path.glob("**/*.tif"):
                region, _, _ = self._extract_metadata_from_filename(file_path.name)
                if region:
                    regions.add(region)
        
        return sorted(list(regions))
    
    def get_available_timepoints(self, input_dir: str) -> List[str]:
        """
        Get list of available timepoints from filenames in the input directory.
        
        Args:
            input_dir (str): Input directory path
            
        Returns:
            List[str]: List of available timepoint names
        """
        input_path = Path(input_dir)
        timepoints = set()
        
        if input_path.exists() and input_path.is_dir():
            for file_path in input_path.glob("**/*.tif"):
                _, timepoint, _ = self._extract_metadata_from_filename(file_path.name)
                if timepoint:
                    timepoints.add(timepoint)
        
        return sorted(list(timepoints))
    
    def get_available_channels(self, input_dir: str) -> List[str]:
        """
        Get list of available channels from filenames in the input directory.
        
        Args:
            input_dir (str): Input directory path
            
        Returns:
            List[str]: List of available channel names
        """
        input_path = Path(input_dir)
        channels = set()
        
        if input_path.exists() and input_path.is_dir():
            for file_path in input_path.glob("**/*.tif"):
                _, _, channel = self._extract_metadata_from_filename(file_path.name)
                if channel:
                    channels.add(channel)
        
        return sorted(list(channels))
