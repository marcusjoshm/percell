#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Combine Masks Service

This service combines binary masks (with values 0 or 255) into a single mask image.
It processes masks with the naming pattern *_bin_*.tif from the grouped_masks
directory and saves the combined masks to the combined_masks directory.

Part of Microscopy Single-Cell Analysis Pipeline
"""

import os
import numpy as np
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import cv2

from percell.domain.ports import FileSystemPort, LoggingPort


class CombineMasksService:
    """
    Service for combining binary masks into single combined mask images.
    
    This service implements the mask combination functionality previously contained in
    the combine_masks.py module, following hexagonal architecture principles.
    """
    
    def __init__(
        self,
        filesystem_port: FileSystemPort,
        logging_port: LoggingPort
    ):
        """
        Initialize the combine masks service.
        
        Args:
            filesystem_port: Port for file system operations
            logging_port: Port for logging operations
        """
        self.filesystem_port = filesystem_port
        self.logging_port = logging_port
        self.logger = logging_port.get_logger("CombineMasksService")
        
        # Check for optional dependencies
        self._check_dependencies()
    
    def _check_dependencies(self):
        """Check for optional dependencies and log availability."""
        try:
            import tifffile
            self.have_tifffile = True
            self.logger.debug("tifffile available for metadata preservation")
        except ImportError:
            self.have_tifffile = False
            self.logger.warning("tifffile not available, metadata preservation disabled")
    
    def get_mask_prefix(self, filename: str) -> Optional[str]:
        """
        Extract the mask prefix from a filename.
        
        Args:
            filename (str): The mask filename (e.g., any region name format with _bin_ pattern)
            
        Returns:
            str: The mask prefix (everything before _bin_), or None if invalid
        """
        # Split by "_bin_" which appears in all mask files
        parts = filename.split("_bin_")
        if len(parts) < 2:
            return None
        
        # Return the part before "_bin_", which will preserve any region naming convention
        return parts[0]
    
    def find_mask_groups(self, mask_dir: Path) -> Dict[str, List[Path]]:
        """
        Find all mask groups in the given directory.
        
        Args:
            mask_dir (Path): Directory containing mask files
            
        Returns:
            dict: Dictionary of mask groups, where key is the group prefix and value is a list of mask file paths
        """
        mask_groups = {}
        
        # Look for mask files with the pattern *_bin_*.tif
        mask_files = list(mask_dir.glob("*_bin_*.tif"))
        
        if not mask_files:
            self.logger.warning(f"No mask files matching *_bin_*.tif found in {mask_dir}")
            return mask_groups
        
        # Group mask files based on their prefix
        for mask_file in mask_files:
            mask_name = mask_file.name
            prefix = self.get_mask_prefix(mask_name)
            
            if prefix is None:
                self.logger.warning(f"Could not extract prefix from {mask_name}. Skipping.")
                continue
                
            # Add mask file to its group
            if prefix not in mask_groups:
                mask_groups[prefix] = []
            mask_groups[prefix].append(mask_file)
        
        return mask_groups
    
    def read_image_with_metadata(self, image_path: Path) -> Tuple[np.ndarray, Optional[Dict]]:
        """
        Read an image file with its metadata if available.
        
        Args:
            image_path (Path): Path to the image file
            
        Returns:
            tuple: The loaded image and metadata if available, or (image, None) if not
        """
        metadata = None
        
        # Try tifffile first if available (best for metadata preservation)
        if self.have_tifffile:
            try:
                import tifffile
                with tifffile.TiffFile(image_path) as tif:
                    img = tif.asarray()
                    # Try to extract resolution information
                    if hasattr(tif, 'pages') and len(tif.pages) > 0:
                        page = tif.pages[0]
                        if hasattr(page, 'tags'):
                            # Extract resolution information if available
                            metadata = {}
                            if 'XResolution' in page.tags:
                                metadata['XResolution'] = page.tags['XResolution'].value
                            if 'YResolution' in page.tags:
                                metadata['YResolution'] = page.tags['YResolution'].value
                            if 'ResolutionUnit' in page.tags:
                                metadata['ResolutionUnit'] = page.tags['ResolutionUnit'].value
                            # Also check for ImageJ metadata
                            if hasattr(page, 'imagej_tags') and page.imagej_tags:
                                metadata.update(page.imagej_tags)
                
                # Convert to grayscale if image has multiple channels
                if len(img.shape) > 2:
                    img = np.mean(img, axis=2).astype(img.dtype)
                
                return img, metadata
                
            except Exception as e:
                self.logger.debug(f"Failed to read with tifffile: {e}, falling back to OpenCV")
        
        # Fallback to OpenCV
        try:
            img = cv2.imread(str(image_path), cv2.IMREAD_GRAYSCALE)
            if img is None:
                raise ValueError(f"Failed to read image: {image_path}")
            return img, None
        except Exception as e:
            self.logger.error(f"Failed to read image {image_path}: {e}")
            raise
    
    def combine_mask_group(
        self,
        mask_files: List[Path],
        output_path: Path,
        preserve_metadata: bool = True
    ) -> bool:
        """
        Combine a group of mask files into a single combined mask.
        
        Args:
            mask_files (List[Path]): List of mask file paths to combine
            output_path (Path): Output path for the combined mask
            preserve_metadata (bool): Whether to preserve metadata in output
            
        Returns:
            bool: True if successful, False otherwise
        """
        if not mask_files:
            self.logger.warning("No mask files provided for combination")
            return False
        
        try:
            # Read the first mask to get dimensions and metadata
            first_mask, metadata = self.read_image_with_metadata(mask_files[0])
            if first_mask is None:
                return False
            
            height, width = first_mask.shape
            combined_mask = np.zeros((height, width), dtype=np.uint8)
            
            # Combine all masks
            for mask_file in mask_files:
                try:
                    mask, _ = self.read_image_with_metadata(mask_file)
                    if mask is not None:
                        # Ensure mask is binary (0 or 255)
                        binary_mask = (mask > 0).astype(np.uint8) * 255
                        combined_mask = np.maximum(combined_mask, binary_mask)
                except Exception as e:
                    self.logger.error(f"Error reading mask {mask_file}: {e}")
                    continue
            
            # Save combined mask
            if preserve_metadata and metadata and self.have_tifffile:
                try:
                    import tifffile
                    tifffile.imwrite(
                        str(output_path),
                        combined_mask,
                        metadata=metadata
                    )
                except Exception as e:
                    self.logger.warning(f"Failed to save with metadata: {e}, falling back to OpenCV")
                    cv2.imwrite(str(output_path), combined_mask)
            else:
                cv2.imwrite(str(output_path), combined_mask)
            
            self.logger.info(f"Combined {len(mask_files)} masks into: {output_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error combining mask group: {e}")
            return False
    
    def combine_all_masks(
        self,
        grouped_masks_dir: str,
        combined_masks_dir: str,
        preserve_metadata: bool = True
    ) -> Dict[str, bool]:
        """
        Combine all mask groups in the grouped_masks directory.
        
        Args:
            grouped_masks_dir (str): Directory containing grouped mask files
            combined_masks_dir (str): Directory to save combined masks
            preserve_metadata (bool): Whether to preserve metadata in output
            
        Returns:
            Dict[str, bool]: Results for each mask group (group_name: success_status)
        """
        grouped_masks_path = Path(grouped_masks_dir)
        combined_masks_path = Path(combined_masks_dir)
        
        # Ensure output directory exists
        combined_masks_path.mkdir(parents=True, exist_ok=True)
        
        # Find all mask groups
        mask_groups = self.find_mask_groups(grouped_masks_path)
        
        if not mask_groups:
            self.logger.warning(f"No mask groups found in {grouped_masks_dir}")
            return {}
        
        self.logger.info(f"Found {len(mask_groups)} mask groups to combine")
        
        results = {}
        
        # Process each group
        for group_name, mask_files in mask_groups.items():
            self.logger.info(f"Processing group: {group_name} ({len(mask_files)} masks)")
            
            # Sort mask files for consistent ordering
            mask_files.sort()
            
            # Create output filename
            output_filename = f"{group_name}_combined.tif"
            output_path = combined_masks_path / output_filename
            
            # Combine masks
            success = self.combine_mask_group(
                mask_files=mask_files,
                output_path=output_path,
                preserve_metadata=preserve_metadata
            )
            
            results[group_name] = success
            
            if success:
                self.logger.info(f"Successfully combined {group_name}")
            else:
                self.logger.error(f"Failed to combine {group_name}")
        
        # Summary
        successful = sum(results.values())
        total = len(results)
        self.logger.info(f"Mask combination complete: {successful}/{total} groups successful")
        
        return results
    
    def combine_specific_groups(
        self,
        grouped_masks_dir: str,
        combined_masks_dir: str,
        group_names: List[str],
        preserve_metadata: bool = True
    ) -> Dict[str, bool]:
        """
        Combine specific mask groups by name.
        
        Args:
            grouped_masks_dir (str): Directory containing grouped mask files
            combined_masks_dir (str): Directory to save combined masks
            group_names (List[str]): List of specific group names to combine
            preserve_metadata (bool): Whether to preserve metadata in output
            
        Returns:
            Dict[str, bool]: Results for each requested mask group
        """
        grouped_masks_path = Path(grouped_masks_dir)
        combined_masks_path = Path(combined_masks_dir)
        
        # Ensure output directory exists
        combined_masks_path.mkdir(parents=True, exist_ok=True)
        
        # Find all mask groups
        all_mask_groups = self.find_mask_groups(grouped_masks_path)
        
        results = {}
        
        for group_name in group_names:
            if group_name not in all_mask_groups:
                self.logger.warning(f"Group '{group_name}' not found in {grouped_masks_dir}")
                results[group_name] = False
                continue
            
            mask_files = all_mask_groups[group_name]
            self.logger.info(f"Processing group: {group_name} ({len(mask_files)} masks)")
            
            # Sort mask files for consistent ordering
            mask_files.sort()
            
            # Create output filename
            output_filename = f"{group_name}_combined.tif"
            output_path = combined_masks_path / output_filename
            
            # Combine masks
            success = self.combine_mask_group(
                mask_files=mask_files,
                output_path=output_path,
                preserve_metadata=preserve_metadata
            )
            
            results[group_name] = success
        
        return results
