#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Group Cells by Expression Level Script for Single Cell Analysis Workflow

This script takes the individual cell images, groups them based on their 
expression level (using integrated intensity) with Gaussian Mixture Model clustering,
and creates summed images for each group.
"""

import os
import sys
import argparse
import logging
import glob
import csv
from pathlib import Path
import numpy as np
import cv2
try:
    # Try to import skimage for better TIFF reading
    from skimage import io as skio
    HAVE_SKIMAGE = True
except ImportError:
    HAVE_SKIMAGE = False
try:
    # Import tifffile for preserving metadata when writing TIFF files
    import tifffile
    HAVE_TIFFFILE = True
except ImportError:
    HAVE_TIFFFILE = False
from sklearn.mixture import GaussianMixture
from sklearn.cluster import KMeans
import matplotlib.pyplot as plt
from scipy import stats
import re
import shutil
import json
from percell.domain import IntensityAnalysisService, CellMetrics

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stdout  # Ensure logging goes to stdout for visibility
)
logger = logging.getLogger("CellGrouper")

def compute_auc(img):
    """
    Compute the area under the histogram curve of the image.
    Using integrated intensity (sum of pixel values) as a proxy for AUC.
    
    Args:
        img (numpy.ndarray): Input grayscale image
        
    Returns:
        float: The sum of all pixel values
    """
    return np.sum(img)

def read_image(image_path, verbose=False):
    """
    Read an image file with better handling of different TIFF formats.
    Tries multiple methods to ensure proper reading.
    
    Args:
        image_path (str): Path to the image file
        verbose (bool): Whether to print diagnostic information
        
    Returns:
        tuple: The loaded image and any metadata if available, or (None, None) if failed
    """
    metadata = None
    
    # Try tifffile first if available (best for metadata preservation)
    if HAVE_TIFFFILE:
        try:
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
                    logger.info(f"Read image {image_path} with tifffile")
                    logger.info(f"  Shape: {img.shape}, Type: {img.dtype}")
                    logger.info(f"  Min: {np.min(img)}, Max: {np.max(img)}, Mean: {np.mean(img):.2f}")
                    logger.info(f"  Sum: {np.sum(img)}")
                    if metadata:
                        logger.info(f"  Metadata: {metadata}")
                
                return img, metadata
        except Exception as e:
            logger.warning(f"tifffile failed to read {image_path}: {e}")
    
    # Next try scikit-image if available
    if HAVE_SKIMAGE:
        try:
            img = skio.imread(image_path)
            # Convert to grayscale if image has multiple channels
            if len(img.shape) > 2:
                img = np.mean(img, axis=2).astype(img.dtype)
            
            if verbose:
                logger.info(f"Read image {image_path} with skimage")
                logger.info(f"  Shape: {img.shape}, Type: {img.dtype}")
                logger.info(f"  Min: {np.min(img)}, Max: {np.max(img)}, Mean: {np.mean(img):.2f}")
                logger.info(f"  Sum: {np.sum(img)}")
            
            return img, None
        except Exception as e:
            logger.warning(f"skimage failed to read {image_path}: {e}")
    
    # Fallback to OpenCV
    try:
        # Try reading as-is
        img = cv2.imread(str(image_path), cv2.IMREAD_UNCHANGED)
        if img is None:
            # If failed, try grayscale
            img = cv2.imread(str(image_path), cv2.IMREAD_GRAYSCALE)
            
        if img is not None:
            if verbose:
                logger.info(f"Read image {image_path} with OpenCV")
                logger.info(f"  Shape: {img.shape}, Type: {img.dtype}")
                logger.info(f"  Min: {np.min(img)}, Max: {np.max(img)}, Mean: {np.mean(img):.2f}")
                logger.info(f"  Sum: {np.sum(img)}")
                
            return img, None
        else:
            logger.warning(f"OpenCV failed to read {image_path}")
            return None, None
    except Exception as e:
        logger.warning(f"OpenCV error reading {image_path}: {e}")
        return None, None

def find_cell_directories(cells_dir):
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

def resize_image_to_target(img, target_height, target_width):
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

def group_and_sum_cells(cell_dir, output_dir, num_bins, method='gmm', force_clusters=False, verbose=False):
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
        logger.warning(f"No cell images found in {cell_dir}")
        return False
    
    logger.info(f"Processing {len(image_files)} cells from {cell_dir}")
    
    # List to store tuples of (filename, auc, image, metadata)
    image_data = []
    zero_count = 0
    nonzero_count = 0
    
    # Variable to store metadata - we'll use the first non-empty one
    reference_metadata = None
    
    for image_file in image_files:
        # Use the enhanced image reading function
        img, metadata = read_image(str(image_file), verbose=verbose)
        
        if img is None:
            logger.warning(f"Unable to read {image_file}. Skipping.")
            continue
        
        # Store the first metadata we find for reference
        if metadata is not None and reference_metadata is None:
            reference_metadata = metadata
            if verbose:
                logger.info(f"Using metadata from {image_file} as reference")
                logger.info(f"Reference metadata: {reference_metadata}")
            
        auc_value = compute_auc(img)
        
        # Track zero vs. non-zero images for diagnostics
        if auc_value == 0:
            zero_count += 1
            if verbose:
                logger.warning(f"Image {image_file} has zero sum (all black)")
        else:
            nonzero_count += 1
            
        image_data.append((str(image_file), auc_value, img, metadata))
    
    if not image_data:
        logger.warning(f"No valid images to process in {cell_dir}")
        return False
        
    # Report zero vs non-zero statistics
    logger.info(f"Found {zero_count} images with zero intensity and {nonzero_count} with non-zero intensity")
    
    if zero_count == len(image_data):
        logger.error("All images have zero intensity. Check image format or file corruption.")
        # Even with all zeros, we'll continue with forced binning if requested
        if not force_clusters:
            logger.info("Try using --force-clusters to create bins with equal cell counts")
    
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
        logger.info(f"Intensity stats - Min: {min_val}, Max: {max_val}, Mean: {mean_val:.2f}, Median: {median_val:.2f}")
    
    # Check if all values are the same or very close
    intensity_range = max_val - min_val if len(auc_values) > 0 else 0
    if intensity_range < 1e-6 and not force_clusters:
        logger.warning("All images have nearly identical intensity. Clustering may not be effective.")
        logger.info("Try using --force-clusters to create bins with equal cell counts")
    
    # Ensure we don't try to create more clusters than we have samples
    actual_num_bins = min(num_bins, len(auc_values))
    if actual_num_bins < num_bins:
        logger.warning(f"Reducing bins from {num_bins} to {actual_num_bins} due to limited samples")
    
    # If all values are zero or identical and force_clusters is enabled, 
    # bypass clustering and just divide evenly
    if (zero_count == len(image_data) or intensity_range < 1e-6) and force_clusters:
        logger.info("Using forced equal distribution due to identical intensity values")
        # Divide cells evenly among the requested bins
        sorted_indices = np.argsort(auc_values.flatten())  # Sort by intensity
        cells_per_cluster = len(auc_values) // actual_num_bins
        remainder = len(auc_values) % actual_num_bins
        
        labels = np.zeros(len(image_data), dtype=int)
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
    
    # Use quantile-based binning if force_clusters is enabled and we have a wide range of intensities
    elif force_clusters and intensity_range > 1e-6:
        logger.info(f"Using quantile-based binning to force {actual_num_bins} equally sized groups")
        
        # Sort cells by intensity
        sorted_indices = np.argsort(auc_values.flatten())
        
        # Divide into equal-sized groups
        cells_per_cluster = len(auc_values) // actual_num_bins
        remainder = len(auc_values) % actual_num_bins
        
        labels = np.zeros(len(image_data), dtype=int)
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
            
    # Attempt domain-based grouping for simple 2-bin strategies
    labels = None
    cluster_means = {}
    if actual_num_bins == 2 and method.lower() in ('median', 'otsu'):
        svc = IntensityAnalysisService()
        # Use AUC as intensity proxy
        metrics = [
            CellMetrics(cell_id=i + 1, area=float(img.size) if hasattr(img, 'size') else 0.0, mean_intensity=float(val))
            for i, ((_, val, img, _)) in enumerate(image_data)
        ]
        if method.lower() == 'median':
            groups = svc.group_cells_by_brightness(metrics)
            # groups: [(label, [ids]), ...]
            id_to_label = {}
            for idx, (label_name, members) in enumerate(groups):
                for cid in members:
                    id_to_label[cid] = idx
            labels = np.array([id_to_label.get(i + 1, 0) for i in range(len(image_data))], dtype=int)
        else:  # otsu delegated externally; fallback to median grouping in-app
            groups = svc.group_cells_by_brightness(metrics)
            id_to_label = {}
            for idx, (label_name, members) in enumerate(groups):
                for cid in members:
                    id_to_label[cid] = idx
            labels = np.array([id_to_label.get(i + 1, 0) for i in range(len(image_data))], dtype=int)
        # Compute cluster means for mapping
        for lab in (0, 1):
            vals = auc_values[labels == lab]
            cluster_means[lab] = vals.mean() if len(vals) > 0 else 0

    # Otherwise, proceed with the selected clustering method
    elif labels is None and method.lower() == 'gmm':
        # Gaussian Mixture Model with improved parameters
        gmm = GaussianMixture(
            n_components=actual_num_bins, 
            random_state=0,
            n_init=10,  # Multiple initializations for better convergence
            max_iter=300,  # More iterations
            reg_covar=1e-4,  # Regularization to improve numerical stability
            init_params='kmeans'  # Use K-means for initialization
        )
        
        # Use the log-transformed values for better clustering with wide dynamic ranges
        gmm.fit(auc_values_log)
        labels = gmm.predict(auc_values_log)
        
        # Get unique labels actually assigned
        unique_labels = np.unique(labels)
        
        # Print convergence information
        logger.info(f"GMM convergence: {gmm.converged_}")
        if not gmm.converged_:
            logger.warning("GMM did not converge. Consider using K-means or forced clustering.")
            
        # Print cluster sizes to diagnose uneven distributions
        for label in unique_labels:
            count = np.sum(labels == label)
            logger.info(f"GMM cluster {label} has {count} cells ({count/len(labels)*100:.1f}%)")
        
        # Calculate cluster means using original values
        cluster_means = {}
        for label in unique_labels:
            cluster_values = auc_values[labels == label]
            cluster_means[label] = cluster_values.mean() if len(cluster_values) > 0 else 0
        
        # If all cells are in one cluster or forcing clusters and some clusters are empty
        if len(unique_labels) == 1 or (force_clusters and len(unique_labels) < actual_num_bins):
            logger.warning(f"GMM only found {len(unique_labels)} clusters but {actual_num_bins} were requested. "
                           f"Falling back to K-means.")
            
            # Fall back to K-means clustering
            method = 'kmeans'  # Set method to kmeans to use the kmeans code path
    
    # Default: Use K-means clustering (either as primary method or as fallback from GMM)
    if labels is None and method.lower() == 'kmeans':
        # Use K-means clustering with multiple initializations and iterations for robustness
        kmeans = KMeans(
            n_clusters=actual_num_bins, 
            random_state=0, 
            n_init=10,  # Multiple initializations to avoid bad starting conditions
            max_iter=300,  # More iterations to ensure convergence
        )
        # Use the log-transformed values for better clustering with wide dynamic ranges
        labels = kmeans.fit_predict(auc_values_log)
        
        # Get cluster centers for sorting
        centers = kmeans.cluster_centers_.flatten()
        # Get unique labels actually assigned (in case some clusters are empty)
        unique_labels = np.unique(labels)
        cluster_means = {label: centers[label] for label in unique_labels}
        
        # Print cluster sizes to diagnose distribution
        for label in unique_labels:
            count = np.sum(labels == label)
            logger.info(f"K-means cluster {label} has {count} cells ({count/len(labels)*100:.1f}%)")
        
        # If forcing clusters and some clusters are empty
        if force_clusters and len(unique_labels) < actual_num_bins:
            logger.warning(f"K-means only found {len(unique_labels)} clusters but {actual_num_bins} were requested. "
                           f"Redistributing data to force {actual_num_bins} clusters.")
            
            # Force redistribution by manually assigning to n clusters
            # Sort data by intensity
            sorted_indices = np.argsort(auc_values.flatten())
            # Calculate number of cells per cluster for even distribution
            cells_per_cluster = len(auc_values) // actual_num_bins
            remainder = len(auc_values) % actual_num_bins
            
            # Assign new labels based on sorted indices
            new_labels = np.zeros_like(labels)
            start_idx = 0
            for i in range(actual_num_bins):
                # Give an extra cell to first 'remainder' clusters if division isn't even
                cluster_size = cells_per_cluster + (1 if i < remainder else 0)
                end_idx = start_idx + cluster_size
                new_labels[sorted_indices[start_idx:end_idx]] = i
                start_idx = end_idx
            
            # Replace original labels with new forced distribution
            labels = new_labels
            
            # Recalculate cluster means
            cluster_means = {}
            for label in range(actual_num_bins):
                cluster_values = auc_values[labels == label]
                cluster_means[label] = cluster_values.mean() if len(cluster_values) > 0 else 0
        
        # If K-means doesn't find the right number of clusters (which shouldn't happen in practice)
        if len(unique_labels) < actual_num_bins:
            logger.warning(f"K-means failed to find {actual_num_bins} clusters (found {len(unique_labels)}). "
                           f"Falling back to quantile-based binning.")
            
            # Fall back to quantile-based binning as last resort
            sorted_indices = np.argsort(auc_values.flatten())
            cells_per_cluster = len(auc_values) // actual_num_bins
            remainder = len(auc_values) % actual_num_bins
            
            new_labels = np.zeros_like(labels)
            start_idx = 0
            for i in range(actual_num_bins):
                cluster_size = cells_per_cluster + (1 if i < remainder else 0)
                end_idx = start_idx + cluster_size
                new_labels[sorted_indices[start_idx:end_idx]] = i
                start_idx = end_idx
            
            labels = new_labels
            
            # Recalculate cluster means
            cluster_means = {}
            for label in range(actual_num_bins):
                cluster_values = auc_values[labels == label]
                cluster_means[label] = cluster_values.mean() if len(cluster_values) > 0 else 0
    
    # Recalculate cluster means if not already done
    if not cluster_means:
        cluster_means = {}
        for label in range(actual_num_bins):
            cluster_values = auc_values[labels == label]
            cluster_means[label] = cluster_values.mean() if len(cluster_values) > 0 else 0
    
    # Sort clusters by mean intensity for consistent binning
    sorted_clusters = sorted(cluster_means, key=lambda k: cluster_means[k])
    
    # Create a deterministic mapping from old cluster IDs to new sorted cluster IDs
    # This ensures that cells are consistently mapped to intensity-based groups
    label_mapping = {old_label: new_label for new_label, old_label in enumerate(sorted_clusters)}
    
    # Log the mapping for debugging
    logger.info("Cluster mapping (original_cluster_id -> sorted_group_id):")
    for old_label, new_label in label_mapping.items():
        logger.info(f"  Cluster {old_label} (mean: {cluster_means[old_label]:.2f}) -> Group {new_label+1}")
    
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
            # This shouldn't happen, but just in case
            mapped_label = original_label % actual_num_bins
        
        # Get image dimensions
        if img is not None:
            height, width = img.shape[:2]
            current_height, current_width = group_dimensions[mapped_label]
            group_dimensions[mapped_label] = (max(current_height, height), max(current_width, width))
    
    logger.info(f"Maximum dimensions for each group: {group_dimensions}")
    
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
            # This shouldn't happen, but just in case
            mapped_label = original_label % actual_num_bins
        
        # Get target dimensions for this group
        target_height, target_width = group_dimensions[mapped_label]
        
        if target_height == 0 or target_width == 0:
            logger.warning(f"Zero dimensions for group {mapped_label + 1}, skipping image {filename}")
            continue
        
        # Resize image to target dimensions
        resized_img = resize_image_to_target(img, target_height, target_width)
        
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
            logger.warning(f"No images in group {i+1}")
            continue
        
        # Normalize the summed image to 0-65535 for a 16-bit image
        norm_img = cv2.normalize(sum_img, None, 0, 65535, cv2.NORM_MINMAX)
        norm_img = norm_img.astype(np.uint16)
        
        # Remove the cell count from the filename to ensure files get overwritten when rerunning with more bins
        output_file = output_subdir / f"{cell_dir.name}_bin_{i+1}.tif"
        
        # Use tifffile to save with metadata if available
        if HAVE_TIFFFILE and reference_metadata is not None:
            try:
                # Prepare metadata dictionary
                metadata_dict = {}
                
                # Try to use the original resolution metadata
                if reference_metadata:
                    # Check for ImageJ tags
                    if 'unit' in reference_metadata and 'resolution' in reference_metadata:
                        # These are common ImageJ metadata for units and scale
                        resolution = reference_metadata.get('resolution', 1.0)
                        unit = reference_metadata.get('unit', 'µm')
                        metadata_dict['resolution'] = resolution
                        metadata_dict['unit'] = unit
                        logger.info(f"Using ImageJ scale information: {resolution} pixels/{unit}")
                    
                    # Standard TIFF resolution tags
                    if 'XResolution' in reference_metadata and 'YResolution' in reference_metadata:
                        metadata_dict['XResolution'] = reference_metadata['XResolution']
                        metadata_dict['YResolution'] = reference_metadata['YResolution']
                        if 'ResolutionUnit' in reference_metadata:
                            metadata_dict['ResolutionUnit'] = reference_metadata['ResolutionUnit']
                
                # Save with metadata
                tifffile.imwrite(
                    str(output_file), 
                    norm_img, 
                    imagej=True,  # Use ImageJ format
                    resolution=(metadata_dict.get('XResolution'), metadata_dict.get('YResolution')),
                    metadata={'unit': 'um'}  # Using 'um' instead of 'µm' to avoid encoding issues
                )
                logger.info(f"Saved summed image with metadata for group {i+1} with {cell_counts[i]} cells: {output_file}")
            except Exception as e:
                logger.warning(f"Failed to save with tifffile, falling back to OpenCV: {e}")
                cv2.imwrite(str(output_file), norm_img)
        else:
            # Fallback to OpenCV (doesn't preserve scale/units)
            cv2.imwrite(str(output_file), norm_img)
            logger.info(f"Saved summed image for group {i+1} with {cell_counts[i]} cells: {output_file}")
            if not HAVE_TIFFFILE:
                logger.warning("tifffile library not available - scale information not preserved. Install with: pip install tifffile")
    
    # Save a text file with information about the grouping
    with open(output_subdir / f"{cell_dir.name}_grouping_info.txt", 'w') as f:
        f.write(f"Cell directory: {cell_dir}\n")
        f.write(f"Number of cells: {len(image_data)}\n")
        f.write(f"Clustering method: {method}\n")
        f.write(f"Force clusters: {force_clusters}\n")
        f.write(f"Number of groups: {actual_num_bins}\n")
        f.write(f"Images with zero intensity: {zero_count}\n")
        f.write(f"Images with non-zero intensity: {nonzero_count}\n")
        f.write(f"Intensity range: {intensity_range:.2f}\n\n")
        
        for i in range(actual_num_bins):
            f.write(f"Group {i+1}:\n")
            f.write(f"  Cells: {cell_counts[i]}\n")
            original_label = next((l for l, m in label_mapping.items() if m == i), i)
            if original_label in cluster_means:
                f.write(f"  Mean intensity: {cluster_means[original_label]:.2f}\n")
            f.write("\n")
    
    # Calculate mean AUC values for each group - using mapped group IDs (1-based)
    group_mean_auc = {}
    mapped_group_cells = {}
    
    # First, create a mapping of cells to their final mapped groups
    for idx, (_, auc_value, _, _) in enumerate(image_data):
        original_label = labels[idx]
        
        # Map to sorted group index (1-based for user-friendliness)
        if original_label in label_mapping:
            mapped_label = label_mapping[original_label] + 1  # 1-based group index
        else:
            # This shouldn't happen, but just in case
            mapped_label = (original_label % actual_num_bins) + 1
            
        # Add this cell's AUC to the appropriate group
        if mapped_label not in mapped_group_cells:
            mapped_group_cells[mapped_label] = []
        
        mapped_group_cells[mapped_label].append(auc_value)
    
    # Now calculate mean AUC for each final group
    for group_id in range(1, actual_num_bins + 1):  # 1-based groups
        if group_id in mapped_group_cells and mapped_group_cells[group_id]:
            group_mean_auc[group_id] = np.mean(mapped_group_cells[group_id])
        else:
            group_mean_auc[group_id] = 0
            logger.warning(f"Group {group_id} has no cells assigned to it")
    
    # Log mean AUC values for each group
    logger.info("Mean intensity (AUC) values for each group:")
    for group_id, mean_auc in sorted(group_mean_auc.items()):
        logger.info(f"  Group {group_id}: {mean_auc:.2f}")
    
    # Save a CSV file with cell-to-group mapping
    cell_group_csv = output_subdir / f"{cell_dir.name}_cell_groups.csv"
    logger.info(f"Saving cell group mapping to {cell_group_csv}")
    
    with open(cell_group_csv, 'w', newline='') as csvfile:
        fieldnames = ['cell_filename', 'cell_id', 'group_id', 'group_name', 'group_mean_auc', 'cell_auc']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        
        for idx, (filename, auc_value, _, _) in enumerate(image_data):
            original_label = labels[idx]
            # Map to sorted group index (1-based for user-friendliness)
            if original_label in label_mapping:
                mapped_label = label_mapping[original_label] + 1  # 1-based group index
            else:
                # This shouldn't happen, but just in case
                mapped_label = (original_label % actual_num_bins) + 1
            
            # Extract cell_id from filename, simplify to just the numeric part
            basename = os.path.basename(filename)
            # First get the base name without extension
            cell_id = basename.replace('.tif', '')
            # Then extract just the numeric part if it contains 'CELL'
            if 'CELL' in cell_id:
                # Extract the numeric part after 'CELL'
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
                'group_mean_auc': group_mean_auc.get(mapped_label_int, 0),
                'cell_auc': auc_value
            })
    
    return True

def process_cell_directory(cell_dir, output_dir, bins=5, force_clusters=False, channels=None):
    """
    Process a directory of cell images and group them based on intensity.
    
    Args:
        cell_dir (Path): Directory containing cell images
        output_dir (Path): Directory to save grouped images
        bins (int): Number of intensity bins
        force_clusters (bool): Force clustering even if few cells
        channels (list): List of channels to process (not used here, handled in main)
    """
    # Create output directory
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Get list of cell images
    cell_files = list(cell_dir.glob("CELL*.tif"))
    if not cell_files:
        logger.warning(f"No cell images found in {cell_dir}")
        return False
    
    logger.info(f"Processing {len(cell_files)} cells in {cell_dir}")
    
    # Calculate average intensity for each cell
    logger.info(f"Calculating intensities for {len(cell_files)} cells...")
    intensities = []
    processed_count = 0
    
    for cell_file in cell_files:
        try:
            img = cv2.imread(str(cell_file), cv2.IMREAD_GRAYSCALE)
            if img is None:
                logger.warning(f"Could not read image: {cell_file}")
                continue
            avg_intensity = np.mean(img)
            intensities.append((cell_file, avg_intensity))
            processed_count += 1
            
            # Log progress every 20 cells
            if processed_count % 20 == 0:
                logger.info(f"Processed {processed_count}/{len(cell_files)} cells...")
                
        except Exception as e:
            logger.error(f"Error processing {cell_file}: {e}")
            continue
    
    logger.info(f"Completed intensity calculation for {processed_count} cells")
    
    if not intensities:
        logger.error(f"No valid cell images found in {cell_dir}")
        return False
    
    # Sort cells by intensity
    logger.info(f"Sorting {len(intensities)} cells by intensity...")
    intensities.sort(key=lambda x: x[1])
    
    # Group cells into bins
    n_cells = len(intensities)
    if n_cells < bins and not force_clusters:
        logger.warning(f"Not enough cells ({n_cells}) for {bins} bins. Skipping clustering.")
        return False
    
    cells_per_bin = n_cells // bins
    remainder = n_cells % bins
    
    logger.info(f"Creating {bins} groups with approximately {cells_per_bin} cells each...")
    
    # Create groups
    groups = []
    start_idx = 0
    for i in range(bins):
        # Add one extra cell to early bins if there's a remainder
        bin_size = cells_per_bin + (1 if i < remainder else 0)
        end_idx = start_idx + bin_size
        groups.append(intensities[start_idx:end_idx])
        start_idx = end_idx
        logger.info(f"Group {i+1}: {len(groups[i])} cells")
    
    # Save grouped cells
    logger.info(f"Copying cells to group directories...")
    total_copied = 0
    for i, group in enumerate(groups):
        group_dir = output_dir / f"group_{i+1}"
        group_dir.mkdir(exist_ok=True)
        
        group_copied = 0
        for cell_file, _ in group:
            try:
                shutil.copy2(cell_file, group_dir / cell_file.name)
                group_copied += 1
                total_copied += 1
            except Exception as e:
                logger.error(f"Error copying {cell_file} to {group_dir}: {e}")
                continue
        
        logger.info(f"Copied {group_copied} cells to group_{i+1}")
    
    logger.info(f"Successfully grouped {n_cells} cells into {bins} groups in {output_dir}")
    logger.info(f"Total files copied: {total_copied}")
    return True

def main():
    parser = argparse.ArgumentParser(description='Group cells based on intensity')
    parser.add_argument('--cells-dir', required=True, help='Directory containing cell images')
    parser.add_argument('--output-dir', required=True, help='Directory to save grouped cells')
    parser.add_argument('--bins', type=int, default=5, help='Number of intensity bins')
    parser.add_argument('--force-clusters', action='store_true', help='Force clustering even if few cells')
    parser.add_argument('--channels', required=True, help='Channels to process (space-separated)')
    
    args = parser.parse_args()
    
    # Handle channels as either a single string or multiple arguments
    if isinstance(args.channels, list):
        channels = args.channels
    else:
        # Split the string on spaces to get individual channels
        channels = args.channels.split()
    
    # Convert paths to Path objects
    cells_dir = Path(args.cells_dir)
    output_dir = Path(args.output_dir)
    
    # Create output directory if it doesn't exist
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Find all cell directories (directories that contain CELL*.tif files)
    cell_dirs = []
    for item in cells_dir.rglob("*"):
        if item.is_dir() and list(item.glob("CELL*.tif")):
            cell_dirs.append(item)
    
    if not cell_dirs:
        logger.error(f"No cell directories found in {cells_dir}")
        return 1
    
    logger.info(f"Found {len(cell_dirs)} cell directories to process")
    successful = 0
    
    # Process each cell directory
    for cell_dir in cell_dirs:
        # Check if directory matches any of the specified channels
        if channels:
            dir_channels = [ch for ch in channels if ch in str(cell_dir)]
            if not dir_channels:
                logger.info(f"Skipping {cell_dir} - no matching channels")
                continue
            logger.info(f"Processing channels {dir_channels} for {cell_dir}")
        
        # Use group_and_sum_cells to create merged bin images instead of individual cell files
        if group_and_sum_cells(cell_dir, output_dir, args.bins, method='gmm', force_clusters=args.force_clusters, verbose=False):
            successful += 1
    
    logger.info(f"Successfully processed {successful} out of {len(cell_dirs)} cell directories")
    
    if successful == 0:
        logger.error("No cell directories were successfully processed")
        return 1
    
    return 0

if __name__ == '__main__':
    sys.exit(main())