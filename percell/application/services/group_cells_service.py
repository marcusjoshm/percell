#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Group Cells Service

This service groups cells by expression level using clustering algorithms
and creates summed images for each group.

Part of Microscopy Single-Cell Analysis Pipeline
"""

import os
import csv
import numpy as np
import cv2
from pathlib import Path
from typing import List, Dict, Tuple, Optional, Any
from sklearn.mixture import GaussianMixture
from sklearn.cluster import KMeans
import matplotlib.pyplot as plt
from scipy import stats
import re
import shutil
import json

from percell.domain.ports import FileSystemPort, LoggingPort


class GroupCellsService:
    """
    Service for grouping cells by expression level using clustering algorithms.
    
    This service implements the cell grouping functionality previously contained in
    the group_cells.py module, following hexagonal architecture principles.
    """
    
    def __init__(
        self,
        filesystem_port: FileSystemPort,
        logging_port: LoggingPort
    ):
        """
        Initialize the group cells service.
        
        Args:
            filesystem_port: Port for file system operations
            logging_port: Port for logging operations
        """
        self.filesystem_port = filesystem_port
        self.logging_port = logging_port
        self.logger = logging_port.get_logger("GroupCellsService")
        
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
        
        try:
            from skimage import io as skio
            self.have_skimage = True
            self.logger.debug("skimage available for image reading")
        except ImportError:
            self.have_skimage = False
            self.logger.warning("skimage not available, using OpenCV fallback")
    
    def compute_auc(self, img: np.ndarray) -> float:
        """
        Compute the area under the histogram curve of the image.
        Using integrated intensity (sum of pixel values) as a proxy for AUC.
        
        Args:
            img (numpy.ndarray): Input grayscale image
            
        Returns:
            float: The sum of all pixel values
        """
        return np.sum(img)
    
    def read_image(self, image_path: Path, verbose: bool = False) -> Tuple[Optional[np.ndarray], Optional[Dict]]:
        """
        Read an image file with better handling of different TIFF formats.
        Tries multiple methods to ensure proper reading.
        
        Args:
            image_path (Path): Path to the image file
            verbose (bool): Whether to print diagnostic information
            
        Returns:
            tuple: The loaded image and any metadata if available, or (None, None) if failed
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
                    
                    if verbose:
                        self.logger.info(f"Read image {image_path} with tifffile")
                        self.logger.info(f"  Shape: {img.shape}, Type: {img.dtype}")
                        self.logger.info(f"  Min: {np.min(img)}, Max: {np.max(img)}, Mean: {np.mean(img):.2f}")
                        self.logger.info(f"  Sum: {np.sum(img)}")
                        if metadata:
                            self.logger.info(f"  Metadata: {metadata}")
                    
                    return img, metadata
            except Exception as e:
                self.logger.warning(f"tifffile failed to read {image_path}: {e}")
        
        # Next try scikit-image if available
        if self.have_skimage:
            try:
                img = skio.imread(image_path)
                # Convert to grayscale if image has multiple channels
                if len(img.shape) > 2:
                    img = np.mean(img, axis=2).astype(img.dtype)
                
                if verbose:
                    self.logger.info(f"Read image {image_path} with skimage")
                    self.logger.info(f"  Shape: {img.shape}, Type: {img.dtype}")
                    self.logger.info(f"  Min: {np.min(img)}, Max: {np.max(img)}, Mean: {np.mean(img):.2f}")
                    self.logger.info(f"  Sum: {np.sum(img)}")
                
                return img, None
            except Exception as e:
                self.logger.warning(f"skimage failed to read {image_path}: {e}")
        
        # Fallback to OpenCV
        try:
            # Try reading as-is
            img = cv2.imread(str(image_path), cv2.IMREAD_UNCHANGED)
            if img is None:
                # If failed, try grayscale
                img = cv2.imread(str(image_path), cv2.IMREAD_GRAYSCALE)
                
            if img is not None:
                if verbose:
                    self.logger.info(f"Read image {image_path} with OpenCV")
                    self.logger.info(f"  Shape: {img.shape}, Type: {img.dtype}")
                    self.logger.info(f"  Min: {np.min(img)}, Max: {np.max(img)}, Mean: {np.mean(img):.2f}")
                    self.logger.info(f"  Sum: {np.sum(img)}")
                    
                return img, None
            else:
                self.logger.warning(f"OpenCV failed to read {image_path}")
                return None, None
        except Exception as e:
            self.logger.warning(f"OpenCV error reading {image_path}: {e}")
            return None, None
    
    def find_cell_directories(self, cells_dir: str) -> List[Tuple[str, Path]]:
        """
        Find all directories containing cell images.
        
        Args:
            cells_dir (str): Base directory containing cell subdirectories
            
        Returns:
            list: List of tuples (condition_name, region_dir_path)
        """
        cell_dirs = []
        
        # Find all condition directories (first level)
        for condition_dir in Path(cells_dir).glob("*"):
            if not condition_dir.is_dir() or condition_dir.name.startswith('.'):
                continue
                
            condition_name = condition_dir.name
            
            # Find all region/timepoint directories within each condition
            for region_dir in condition_dir.glob("*"):
                if not region_dir.is_dir() or region_dir.name.startswith('.'):
                    continue
                    
                # Check if this directory contains cell images
                cell_images = list(region_dir.glob("CELL*.tif"))
                if cell_images:
                    cell_dirs.append((condition_name, region_dir))
        
        return cell_dirs
    
    def resize_image_to_target(self, img: np.ndarray, target_height: int, target_width: int) -> np.ndarray:
        """
        Resize an image to the target dimensions, maintaining aspect ratio and adding padding if needed.
        
        Args:
            img (numpy.ndarray): Input image
            target_height (int): Target height
            target_width (int): Target width
            
        Returns:
            numpy.ndarray: Resized image with padding if necessary
        """
        # Get original dimensions
        height, width = img.shape[:2]
        
        # Calculate aspect ratios
        img_aspect = width / height
        target_aspect = target_width / target_height
        
        # Resize image while maintaining aspect ratio
        if img_aspect > target_aspect:
            # Image is wider than target aspect ratio
            new_width = target_width
            new_height = int(new_width / img_aspect)
        else:
            # Image is taller than target aspect ratio
            new_height = target_height
            new_width = int(new_height * img_aspect)
        
        # Resize the image
        resized = cv2.resize(img, (new_width, new_height), interpolation=cv2.INTER_AREA)
        
        # Create a black canvas of the target size
        result = np.zeros((target_height, target_width), dtype=img.dtype)
        
        # Calculate padding to center the image
        pad_top = (target_height - new_height) // 2
        pad_left = (target_width - new_width) // 2
        
        # Place the resized image on the canvas
        result[pad_top:pad_top+new_height, pad_left:pad_left+new_width] = resized
        
        return result
    
    def group_and_sum_cells(
        self,
        cell_dir: Path,
        output_dir: Path,
        num_bins: int,
        method: str = 'gmm',
        force_clusters: bool = False,
        verbose: bool = False
    ) -> bool:
        """
        Group cell images by expression level and create summed images.
        
        Args:
            cell_dir (Path): Directory containing cell images
            output_dir (Path): Directory to save output summed images
            num_bins (int): Number of groups to cluster cells into
            method (str): Clustering method ('gmm' or 'kmeans')
            force_clusters (bool): Force creation of num_bins clusters even with similar data
            verbose (bool): Whether to print verbose diagnostic information
            
        Returns:
            bool: True if successful, False otherwise
        """
        # Get all cell image files
        image_files = list(cell_dir.glob("CELL*.tif"))
        
        if not image_files:
            self.logger.warning(f"No cell images found in {cell_dir}")
            return False
        
        self.logger.info(f"Processing {len(image_files)} cells from {cell_dir}")
        
        # List to store tuples of (filename, auc, image, metadata)
        image_data = []
        zero_count = 0
        nonzero_count = 0
        
        # Variable to store metadata - we'll use the first non-empty one
        reference_metadata = None
        
        for image_file in image_files:
            # Use the enhanced image reading function
            img, metadata = self.read_image(image_file, verbose=verbose)
            
            if img is None:
                self.logger.warning(f"Unable to read {image_file}. Skipping.")
                continue
            
            # Store the first metadata we find for reference
            if metadata is not None and reference_metadata is None:
                reference_metadata = metadata
                if verbose:
                    self.logger.info(f"Using metadata from {image_file} as reference")
                    self.logger.info(f"Reference metadata: {reference_metadata}")
                
            auc_value = self.compute_auc(img)
            
            # Track zero vs. non-zero images for diagnostics
            if auc_value == 0:
                zero_count += 1
                if verbose:
                    self.logger.warning(f"Image {image_file} has zero sum (all black)")
            else:
                nonzero_count += 1
                
            image_data.append((str(image_file), auc_value, img, metadata))
        
        if not image_data:
            self.logger.warning(f"No valid images to process in {cell_dir}")
            return False
            
        # Report zero vs non-zero statistics
        self.logger.info(f"Found {zero_count} images with zero intensity and {nonzero_count} with non-zero intensity")
        
        if zero_count == len(image_data):
            self.logger.error("All images have zero intensity. Check image format or file corruption.")
            # Even with all zeros, we'll continue with forced binning if requested
            if not force_clusters:
                self.logger.info("Try using --force-clusters to create bins with equal cell counts")
        
        # Prepare an array of AUC values for clustering
        auc_values = np.array([data[1] for data in image_data]).reshape(-1, 1)
        
        # Apply log transformation to better handle wide dynamic ranges of intensity
        if np.min(auc_values) > 0:  # Only apply log if all values are positive
            auc_values_log = np.log1p(auc_values)  # log(1+x) to handle small values better
        else:
            auc_values_log = auc_values
            
        # Show some statistics about the intensity values
        if len(auc_values) > 0:
            min_val = np.min(auc_values)
            max_val = np.max(auc_values) 
            mean_val = np.mean(auc_values)
            median_val = np.median(auc_values)
            self.logger.info(f"Intensity stats - Min: {min_val}, Max: {max_val}, Mean: {mean_val:.2f}, Median: {median_val:.2f}")
        
        # Check if all values are the same or very close
        intensity_range = max_val - min_val if len(auc_values) > 0 else 0
        if intensity_range < 1e-6 and not force_clusters:
            self.logger.warning("All images have nearly identical intensity. Clustering may not be effective.")
            self.logger.info("Try using --force-clusters to create bins with equal cell counts")
        
        # Ensure we don't try to create more clusters than we have samples
        actual_num_bins = min(num_bins, len(auc_values))
        if actual_num_bins < num_bins:
            self.logger.warning(f"Reducing bins from {num_bins} to {actual_num_bins} due to limited samples")
        
        # Perform clustering based on method and conditions
        labels, cluster_means = self._perform_clustering(
            auc_values, auc_values_log, actual_num_bins, method, force_clusters, intensity_range, zero_count
        )
        
        # Sort clusters by mean intensity for consistent binning
        sorted_clusters = sorted(cluster_means, key=lambda k: cluster_means[k])
        
        # Create a deterministic mapping from old cluster IDs to new sorted cluster IDs
        label_mapping = {old_label: new_label for new_label, old_label in enumerate(sorted_clusters)}
        
        # Log the mapping for debugging
        self.logger.info("Cluster mapping (original_cluster_id -> sorted_group_id):")
        for old_label, new_label in label_mapping.items():
            self.logger.info(f"  Cluster {old_label} (mean: {cluster_means[old_label]:.2f}) -> Group {new_label+1}")
        
        # Process images and create summed images
        return self._create_summed_images(
            image_data, labels, label_mapping, actual_num_bins, cluster_means,
            cell_dir, output_dir, reference_metadata
        )
    
    def _perform_clustering(
        self,
        auc_values: np.ndarray,
        auc_values_log: np.ndarray,
        actual_num_bins: int,
        method: str,
        force_clusters: bool,
        intensity_range: float,
        zero_count: int
    ) -> Tuple[np.ndarray, Dict[int, float]]:
        """
        Perform clustering based on the specified method and conditions.
        
        Args:
            auc_values: Original AUC values
            auc_values_log: Log-transformed AUC values
            actual_num_bins: Number of bins to create
            method: Clustering method ('gmm' or 'kmeans')
            force_clusters: Whether to force cluster creation
            intensity_range: Range of intensity values
            zero_count: Number of zero-intensity images
            
        Returns:
            Tuple of (labels, cluster_means)
        """
        # If all values are zero or identical and force_clusters is enabled, 
        # bypass clustering and just divide evenly
        if (zero_count == len(auc_values) or intensity_range < 1e-6) and force_clusters:
            self.logger.info("Using forced equal distribution due to identical intensity values")
            return self._create_forced_distribution(auc_values, actual_num_bins)
        
        # Use quantile-based binning if force_clusters is enabled and we have a wide range of intensities
        elif force_clusters and intensity_range > 1e-6:
            self.logger.info(f"Using quantile-based binning to force {actual_num_bins} equally sized groups")
            return self._create_quantile_binning(auc_values, actual_num_bins)
        
        # Otherwise, proceed with the selected clustering method
        elif method.lower() == 'gmm':
            return self._perform_gmm_clustering(auc_values_log, actual_num_bins, force_clusters)
        
        # Default: Use K-means clustering
        else:
            return self._perform_kmeans_clustering(auc_values_log, actual_num_bins, force_clusters)
    
    def _create_forced_distribution(self, auc_values: np.ndarray, actual_num_bins: int) -> Tuple[np.ndarray, Dict[int, float]]:
        """Create forced equal distribution of cells."""
        sorted_indices = np.argsort(auc_values.flatten())
        cells_per_cluster = len(auc_values) // actual_num_bins
        remainder = len(auc_values) % actual_num_bins
        
        labels = np.zeros(len(auc_values), dtype=int)
        start_idx = 0
        for i in range(actual_num_bins):
            cluster_size = cells_per_cluster + (1 if i < remainder else 0)
            end_idx = start_idx + cluster_size
            labels[sorted_indices[start_idx:end_idx]] = i
            start_idx = end_idx
            
        # Calculate cluster means
        cluster_means = {}
        for label in range(actual_num_bins):
            cluster_values = auc_values[labels == label]
            cluster_means[label] = cluster_values.mean() if len(cluster_values) > 0 else 0
        
        return labels, cluster_means
    
    def _create_quantile_binning(self, auc_values: np.ndarray, actual_num_bins: int) -> Tuple[np.ndarray, Dict[int, float]]:
        """Create quantile-based binning."""
        sorted_indices = np.argsort(auc_values.flatten())
        cells_per_cluster = len(auc_values) // actual_num_bins
        remainder = len(auc_values) % actual_num_bins
        
        labels = np.zeros(len(auc_values), dtype=int)
        start_idx = 0
        for i in range(actual_num_bins):
            cluster_size = cells_per_cluster + (1 if i < remainder else 0)
            end_idx = start_idx + cluster_size
            labels[sorted_indices[start_idx:end_idx]] = i
            start_idx = end_idx
        
        # Calculate cluster means
        cluster_means = {}
        for label in range(actual_num_bins):
            cluster_values = auc_values[labels == label]
            cluster_means[label] = cluster_values.mean() if len(cluster_values) > 0 else 0
            
        return labels, cluster_means
    
    def _perform_gmm_clustering(
        self,
        auc_values_log: np.ndarray,
        actual_num_bins: int,
        force_clusters: bool
    ) -> Tuple[np.ndarray, Dict[int, float]]:
        """Perform Gaussian Mixture Model clustering."""
        gmm = GaussianMixture(
            n_components=actual_num_bins, 
            random_state=0,
            n_init=10,
            max_iter=300,
            reg_covar=1e-4,
            init_params='kmeans'
        )
        
        gmm.fit(auc_values_log)
        labels = gmm.predict(auc_values_log)
        
        # Get unique labels actually assigned
        unique_labels = np.unique(labels)
        
        # Print convergence information
        self.logger.info(f"GMM convergence: {gmm.converged_}")
        if not gmm.converged_:
            self.logger.warning("GMM did not converge. Consider using K-means or forced clustering.")
            
        # Print cluster sizes to diagnose uneven distributions
        for label in unique_labels:
            count = np.sum(labels == label)
            self.logger.info(f"GMM cluster {label} has {count} cells ({count/len(labels)*100:.1f}%)")
        
        # Calculate cluster means using original values
        cluster_means = {}
        for label in unique_labels:
            cluster_values = auc_values_log[labels == label]
            cluster_means[label] = cluster_values.mean() if len(cluster_values) > 0 else 0
        
        # If all cells are in one cluster or forcing clusters and some clusters are empty
        if len(unique_labels) == 1 or (force_clusters and len(unique_labels) < actual_num_bins):
            self.logger.warning(f"GMM only found {len(unique_labels)} clusters but {actual_num_bins} were requested. "
                               f"Falling back to K-means.")
            return self._perform_kmeans_clustering(auc_values_log, actual_num_bins, force_clusters)
        
        return labels, cluster_means
    
    def _perform_kmeans_clustering(
        self,
        auc_values_log: np.ndarray,
        actual_num_bins: int,
        force_clusters: bool
    ) -> Tuple[np.ndarray, Dict[int, float]]:
        """Perform K-means clustering."""
        kmeans = KMeans(
            n_clusters=actual_num_bins, 
            random_state=0, 
            n_init=10,
            max_iter=300,
        )
        
        labels = kmeans.fit_predict(auc_values_log)
        
        # Get cluster centers for sorting
        centers = kmeans.cluster_centers_.flatten()
        unique_labels = np.unique(labels)
        cluster_means = {label: centers[label] for label in unique_labels}
        
        # Print cluster sizes to diagnose distribution
        for label in unique_labels:
            count = np.sum(labels == label)
            self.logger.info(f"K-means cluster {label} has {count} cells ({count/len(labels)*100:.1f}%)")
        
        # If forcing clusters and some clusters are empty
        if force_clusters and len(unique_labels) < actual_num_bins:
            self.logger.warning(f"K-means only found {len(unique_labels)} clusters but {actual_num_bins} were requested. "
                               f"Redistributing data to force {actual_num_bins} clusters.")
            return self._create_quantile_binning(auc_values_log, actual_num_bins)
        
        return labels, cluster_means
    
    def _create_summed_images(
        self,
        image_data: List[Tuple[str, float, np.ndarray, Optional[Dict]]],
        labels: np.ndarray,
        label_mapping: Dict[int, int],
        actual_num_bins: int,
        cluster_means: Dict[int, float],
        cell_dir: Path,
        output_dir: Path,
        reference_metadata: Optional[Dict]
    ) -> bool:
        """
        Create summed images for each group.
        
        Args:
            image_data: List of (filename, auc, image, metadata) tuples
            labels: Cluster labels for each image
            label_mapping: Mapping from original to sorted cluster IDs
            actual_num_bins: Number of bins created
            cluster_means: Mean intensity for each cluster
            cell_dir: Input cell directory
            output_dir: Output directory
            reference_metadata: Metadata to preserve in output
            
        Returns:
            bool: True if successful
        """
        # First pass: determine maximum dimensions for each group
        group_dimensions = {}
        for i in range(actual_num_bins):
            group_dimensions[i] = (0, 0)  # (height, width)
        
        # Find the maximum dimensions for each group
        for idx, (filename, _, img, _) in enumerate(image_data):
            original_label = labels[idx]
            # Map to sorted group index
            if original_label in label_mapping:
                mapped_label = label_mapping[original_label]
            else:
                mapped_label = original_label % actual_num_bins
            
            # Get image dimensions
            if img is not None:
                height, width = img.shape[:2]
                current_height, current_width = group_dimensions[mapped_label]
                group_dimensions[mapped_label] = (max(current_height, height), max(current_width, width))
        
        self.logger.info(f"Maximum dimensions for each group: {group_dimensions}")
        
        # Initialize list to hold summed images for each group
        sum_images = [None] * actual_num_bins
        cell_counts = [0] * actual_num_bins
        
        # Second pass: resize images to match group dimensions and sum them
        for idx, (filename, auc_value, img, metadata) in enumerate(image_data):
            original_label = labels[idx]
            # Only use label mapping if we have the original label in the mapping
            if original_label in label_mapping:
                mapped_label = label_mapping[original_label]
            else:
                mapped_label = original_label % actual_num_bins
            
            # Get target dimensions for this group
            target_height, target_width = group_dimensions[mapped_label]
            
            if target_height == 0 or target_width == 0:
                self.logger.warning(f"Zero dimensions for group {mapped_label + 1}, skipping image {filename}")
                continue
            
            # Resize image to target dimensions
            resized_img = self.resize_image_to_target(img, target_height, target_width)
            
            # Initialize sum image if needed
            if sum_images[mapped_label] is None:
                sum_images[mapped_label] = np.zeros((target_height, target_width), dtype=np.float64)
            
            # Add resized image to sum
            sum_images[mapped_label] += resized_img.astype(np.float64)
            cell_counts[mapped_label] += 1
        
        # Create output directory if it doesn't exist
        output_subdir = output_dir / cell_dir.parent.name / cell_dir.name
        output_subdir.mkdir(parents=True, exist_ok=True)
        
        # Save the summed images as 16-bit TIFF files
        for i, sum_img in enumerate(sum_images):
            if sum_img is None:
                self.logger.warning(f"No images in group {i+1}")
                continue
            
            # Normalize the summed image to 0-65535 for a 16-bit image
            norm_img = cv2.normalize(sum_img, None, 0, 65535, cv2.NORM_MINMAX)
            norm_img = norm_img.astype(np.uint16)
            
            # Remove the cell count from the filename to ensure files get overwritten when rerunning with more bins
            output_file = output_subdir / f"{cell_dir.name}_bin_{i+1}.tif"
            
            # Use tifffile to save with metadata if available
            if self.have_tifffile and reference_metadata is not None:
                try:
                    # Prepare metadata dictionary
                    metadata_dict = {}
                    
                    # Try to use the original resolution metadata
                    if reference_metadata:
                        # Check for ImageJ tags
                        if 'unit' in reference_metadata and 'resolution' in reference_metadata:
                            resolution = reference_metadata.get('resolution', 1.0)
                            unit = reference_metadata.get('unit', 'µm')
                            metadata_dict['resolution'] = resolution
                            metadata_dict['unit'] = unit
                            self.logger.info(f"Using ImageJ scale information: {resolution} pixels/{unit}")
                        
                        # Standard TIFF resolution tags
                        if 'XResolution' in reference_metadata and 'YResolution' in reference_metadata:
                            metadata_dict['XResolution'] = reference_metadata['XResolution']
                            metadata_dict['YResolution'] = reference_metadata['YResolution']
                            if 'ResolutionUnit' in reference_metadata:
                                metadata_dict['ResolutionUnit'] = reference_metadata['ResolutionUnit']
                    
                    # Save with metadata
                    import tifffile
                    tifffile.imwrite(
                        str(output_file), 
                        norm_img, 
                        imagej=True,
                        resolution=(metadata_dict.get('XResolution'), metadata_dict.get('YResolution')),
                        metadata={'unit': 'um'}
                    )
                    self.logger.info(f"Saved summed image with metadata for group {i+1} with {cell_counts[i]} cells: {output_file}")
                except Exception as e:
                    self.logger.warning(f"Failed to save with tifffile, falling back to OpenCV: {e}")
                    cv2.imwrite(str(output_file), norm_img)
            else:
                # Fallback to OpenCV (doesn't preserve scale/units)
                cv2.imwrite(str(output_file), norm_img)
                self.logger.info(f"Saved summed image for group {i+1} with {cell_counts[i]} cells: {output_file}")
                if not self.have_tifffile:
                    self.logger.warning("tifffile library not available - scale information not preserved. Install with: pip install tifffile")
        
        # Save grouping information and CSV
        self._save_grouping_info(
            cell_dir, output_subdir, actual_num_bins, cluster_means, 
            label_mapping, image_data, labels, cell_counts
        )
        
        return True
    
    def _save_grouping_info(
        self,
        cell_dir: Path,
        output_subdir: Path,
        actual_num_bins: int,
        cluster_means: Dict[int, float],
        label_mapping: Dict[int, int],
        image_data: List[Tuple[str, float, np.ndarray, Optional[Dict]]],
        labels: np.ndarray,
        cell_counts: List[int]
    ):
        """Save grouping information and CSV files."""
        # Save a text file with information about the grouping
        info_file = output_subdir / f"{cell_dir.name}_grouping_info.txt"
        with open(info_file, 'w') as f:
            f.write(f"Cell directory: {cell_dir}\n")
            f.write(f"Number of cells: {len(image_data)}\n")
            f.write(f"Number of groups: {actual_num_bins}\n")
            f.write(f"Images with zero intensity: {sum(1 for _, auc, _, _ in image_data if auc == 0)}\n")
            f.write(f"Images with non-zero intensity: {sum(1 for _, auc, _, _ in image_data if auc > 0)}\n\n")
            
            for i in range(actual_num_bins):
                f.write(f"Group {i+1}:\n")
                f.write(f"  Cells: {cell_counts[i]}\n")
                original_label = next((l for l, m in label_mapping.items() if m == i), i)
                if original_label in cluster_means:
                    f.write(f"  Mean intensity: {cluster_means[original_label]:.2f}\n")
                f.write("\n")
        
        # Save a CSV file with cell-to-group mapping
        csv_file = output_subdir / f"{cell_dir.name}_cell_groups.csv"
        self.logger.info(f"Saving cell group mapping to {csv_file}")
        
        with open(csv_file, 'w', newline='') as csvfile:
            fieldnames = ['cell_filename', 'cell_id', 'group_id', 'group_name', 'group_mean_auc', 'cell_auc']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            
            for idx, (filename, auc_value, _, _) in enumerate(image_data):
                original_label = labels[idx]
                # Map to sorted group index (1-based for user-friendliness)
                if original_label in label_mapping:
                    mapped_label = label_mapping[original_label] + 1
                else:
                    mapped_label = (original_label % actual_num_bins) + 1
                
                # Extract cell_id from filename
                basename = os.path.basename(filename)
                cell_id = basename.replace('.tif', '')
                if 'CELL' in cell_id:
                    numeric_part = ''.join(c for c in cell_id if c.isdigit())
                    if numeric_part:
                        cell_id = numeric_part
                
                # Ensure the group_id is an integer for consistency
                mapped_label_int = int(mapped_label)
                
                writer.writerow({
                    'cell_filename': filename,
                    'cell_id': cell_id,
                    'group_id': mapped_label_int,
                    'group_name': f"Group_{mapped_label_int}",
                    'group_mean_auc': cluster_means.get(original_label, 0),
                    'cell_auc': auc_value
                })
    
    def process_cell_directories(
        self,
        cells_dir: str,
        output_dir: str,
        bins: int = 5,
        method: str = 'gmm',
        force_clusters: bool = False,
        channels: Optional[List[str]] = None,
        verbose: bool = False
    ) -> Dict[str, Any]:
        """
        Process multiple cell directories and group them based on intensity.
        
        Args:
            cells_dir (str): Directory containing cell images
            output_dir (str): Directory to save grouped images
            bins (int): Number of intensity bins
            method (str): Clustering method ('gmm' or 'kmeans')
            force_clusters (bool): Force clustering even if few cells
            channels (Optional[List[str]]): List of channels to process
            verbose (bool): Whether to print verbose diagnostic information
            
        Returns:
            Dict[str, Any]: Summary of processing results
        """
        cells_path = Path(cells_dir)
        output_path = Path(output_dir)
        
        # Create output directory if it doesn't exist
        output_path.mkdir(parents=True, exist_ok=True)
        
        # Find all cell directories (directories that contain CELL*.tif files)
        cell_dirs = []
        for item in cells_path.rglob("*"):
            if item.is_dir() and list(item.glob("CELL*.tif")):
                cell_dirs.append(item)
        
        if not cell_dirs:
            self.logger.error(f"No cell directories found in {cells_dir}")
            return {'success': False, 'error': 'No cell directories found'}
        
        self.logger.info(f"Found {len(cell_dirs)} cell directories to process")
        successful = 0
        failed = 0
        results = []
        
        # Process each cell directory
        for cell_dir in cell_dirs:
            # Check if directory matches any of the specified channels
            if channels:
                dir_channels = [ch for ch in channels if ch in str(cell_dir)]
                if not dir_channels:
                    self.logger.info(f"Skipping {cell_dir} - no matching channels")
                    continue
                self.logger.info(f"Processing channels {dir_channels} for {cell_dir}")
            
            # Use group_and_sum_cells to create merged bin images
            if self.group_and_sum_cells(
                cell_dir, output_path, bins, method, force_clusters, verbose
            ):
                successful += 1
                results.append({
                    'directory': str(cell_dir),
                    'status': 'success',
                    'channels': dir_channels if channels else []
                })
            else:
                failed += 1
                results.append({
                    'directory': str(cell_dir),
                    'status': 'failed',
                    'channels': dir_channels if channels else []
                })
        
        self.logger.info(f"Successfully processed {successful} out of {len(cell_dirs)} cell directories")
        
        return {
            'success': successful > 0,
            'total_directories': len(cell_dirs),
            'successful': successful,
            'failed': failed,
            'results': results
        }
