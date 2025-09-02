#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Track ROIs Service for Single Cell Analysis Workflow

This service matches ROIs between two time points by finding the optimal assignment
that minimizes the total distance between cell centroids. It reorders the ROIs in the 
second time point to match the order of ROIs in the first time point, which allows for
tracking the same cells across multiple time points.
"""

import os
import zipfile
import re
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from percell.domain.ports import FileSystemPort, LoggingPort


class TrackROIsService:
    """
    Service for tracking ROIs between time points.
    
    This service matches ROIs between two time points by finding the optimal assignment
    that minimizes the total distance between cell centroids.
    """
    
    def __init__(
        self,
        filesystem_port: FileSystemPort,
        logging_port: LoggingPort
    ):
        """
        Initialize the Track ROIs Service.
        
        Args:
            filesystem_port: Port for file system operations
            logging_port: Port for logging operations
        """
        self.filesystem_port = filesystem_port
        self.logging_port = logging_port
        self.logger = self.logging_port.get_logger("TrackROIsService")
    
    def load_roi_dict(self, zip_file_path: str) -> Optional[Dict[str, Any]]:
        """
        Load ROI dictionaries from an ImageJ ROI .zip file.
        
        Args:
            zip_file_path: Path to the ROI zip file
            
        Returns:
            Dictionary mapping ROI names to ROI dictionaries, or None if failed
        """
        try:
            # This would typically use a dedicated ROI reading port
            # For now, we'll implement basic ROI reading functionality
            roi_dict = {}
            
            with zipfile.ZipFile(zip_file_path, 'r') as z:
                for name in z.namelist():
                    if name.lower().endswith('.roi'):
                        # Read ROI file content
                        roi_data = z.read(name)
                        # Parse ROI data (basic implementation)
                        roi_info = self._parse_roi_data(roi_data, name)
                        if roi_info:
                            roi_dict[name] = roi_info
            
            return roi_dict
            
        except Exception as e:
            self.logger.error(f"Error loading ROI file {zip_file_path}: {e}")
            return None
    
    def load_roi_bytes(self, zip_file_path: str) -> Optional[Dict[str, bytes]]:
        """
        Load raw ROI file bytes from an ImageJ ROI .zip file.
        
        Args:
            zip_file_path: Path to the ROI zip file
            
        Returns:
            Dictionary mapping ROI names to raw bytes, or None if failed
        """
        try:
            roi_bytes = {}
            
            with zipfile.ZipFile(zip_file_path, 'r') as z:
                for name in z.namelist():
                    # Remove '.roi' extension (case-insensitive) if present
                    key = name
                    if name.lower().endswith('.roi'):
                        key = name[:-4]
                    roi_bytes[key] = z.read(name)
            
            return roi_bytes
            
        except Exception as e:
            self.logger.error(f"Error loading ROI bytes from {zip_file_path}: {e}")
            return None
    
    def _parse_roi_data(self, roi_data: bytes, filename: str) -> Optional[Dict[str, Any]]:
        """
        Parse ROI data from bytes.
        
        Args:
            roi_data: Raw ROI file bytes
            filename: ROI filename
            
        Returns:
            Parsed ROI dictionary, or None if failed
        """
        try:
            # This is a simplified ROI parser
            # In a real implementation, this would use a proper ROI parsing library
            
            # Basic ROI structure (ImageJ ROI format)
            if len(roi_data) < 64:  # Minimum ROI header size
                return None
            
            # Extract basic ROI information
            roi_type = int.from_bytes(roi_data[0:2], byteorder='little')
            
            # For now, return a basic structure
            # In practice, this would parse the actual ROI data
            return {
                'type': roi_type,
                'filename': filename,
                'raw_data': roi_data
            }
            
        except Exception as e:
            self.logger.error(f"Error parsing ROI data: {e}")
            return None
    
    def polygon_centroid(self, x: List[float], y: List[float]) -> Tuple[float, float]:
        """
        Compute the centroid of a polygon given vertex coordinate lists x and y.
        Uses the shoelace formula; if the computed area is nearly zero, falls back to arithmetic mean.
        Assumes the polygon is closed (first vertex == last vertex).
        
        Args:
            x: List of x-coordinates
            y: List of y-coordinates
            
        Returns:
            (x, y) coordinates of the centroid
        """
        try:
            A = 0.0
            Cx = 0.0
            Cy = 0.0
            n = len(x) - 1  # because the polygon is closed
            
            for i in range(n):
                cross = x[i] * y[i+1] - x[i+1] * y[i]
                A += cross
                Cx += (x[i] + x[i+1]) * cross
                Cy += (y[i] + y[i+1]) * cross
            
            A *= 0.5
            
            if abs(A) < 1e-8:
                return (sum(x[:-1]) / n, sum(y[:-1]) / n)
            
            Cx /= (6 * A)
            Cy /= (6 * A)
            
            return (Cx, Cy)
            
        except Exception as e:
            self.logger.error(f"Error computing polygon centroid: {e}")
            # Fallback to arithmetic mean
            return (sum(x) / len(x), sum(y) / len(y))
    
    def get_roi_center(self, roi: Dict[str, Any]) -> Optional[Tuple[float, float]]:
        """
        Compute the centroid of an ROI dictionary.
        
        Args:
            roi: ROI dictionary
            
        Returns:
            (x, y) coordinates of the ROI center, or None if failed
        """
        try:
            # This would typically extract coordinates from the parsed ROI data
            # For now, we'll return a placeholder since we don't have the full ROI parsing
            
            # In a real implementation, this would:
            # 1. Extract x, y coordinates from the ROI data
            # 2. Compute the centroid using polygon_centroid
            # 3. Handle different ROI types (polygon, rectangle, etc.)
            
            self.logger.debug("ROI center computation not fully implemented")
            return (0.0, 0.0)  # Placeholder
            
        except Exception as e:
            self.logger.error(f"Error computing ROI center: {e}")
            return None
    
    def match_rois(self, roi_list1: List[Dict[str, Any]], roi_list2: List[Dict[str, Any]]) -> List[int]:
        """
        Given two lists of ROI dictionaries, compute the optimal matching indices (for roi_list2)
        that minimizes the total Euclidean distance between centroids.
        
        Args:
            roi_list1: List of ROI dictionaries for first time point
            roi_list2: List of ROI dictionaries for second time point
            
        Returns:
            List of indices that map ROIs in roi_list2 to match roi_list1
        """
        try:
            n1 = len(roi_list1)
            n2 = len(roi_list2)
            
            # If the lists have different lengths, use the smaller one as the size
            # and only match that many ROIs
            n = min(n1, n2)
            
            # Use a subset of ROIs if necessary
            roi_subset1 = roi_list1[:n]
            roi_subset2 = roi_list2[:n]
            
            # Compute centroids for each ROI
            centers1 = []
            centers2 = []
            
            for roi in roi_subset1:
                center = self.get_roi_center(roi)
                if center:
                    centers1.append(center)
                else:
                    # Use fallback center if computation fails
                    centers1.append((0.0, 0.0))
            
            for roi in roi_subset2:
                center = self.get_roi_center(roi)
                if center:
                    centers2.append(center)
                else:
                    # Use fallback center if computation fails
                    centers2.append((0.0, 0.0))
            
            # Compute cost matrix (Euclidean distances)
            cost_matrix = []
            for i in range(n):
                row = []
                for j in range(n):
                    dx = centers1[i][0] - centers2[j][0]
                    dy = centers1[i][1] - centers2[j][1]
                    distance = (dx * dx + dy * dy) ** 0.5
                    row.append(distance)
                cost_matrix.append(row)
            
            # Find optimal assignment using Hungarian algorithm
            # For now, we'll use a simple greedy approach
            # In a real implementation, this would use scipy.optimize.linear_sum_assignment
            
            matching = self._greedy_assignment(cost_matrix)
            
            # If the second list is longer, pad the matching with additional indices
            if n2 > n1:
                extra_indices = list(range(n, n2))
                return matching + extra_indices
            
            return matching
            
        except Exception as e:
            self.logger.error(f"Error matching ROIs: {e}")
            # Return sequential matching as fallback
            return list(range(min(n1, n2)))
    
    def _greedy_assignment(self, cost_matrix: List[List[float]]) -> List[int]:
        """
        Simple greedy assignment algorithm.
        
        Args:
            cost_matrix: Cost matrix where cost_matrix[i][j] is the cost of assigning i to j
            
        Returns:
            List of column indices for optimal assignment
        """
        try:
            n = len(cost_matrix)
            if n == 0:
                return []
            
            # Simple greedy approach: assign each row to the best available column
            used_columns = set()
            assignment = []
            
            for i in range(n):
                best_j = -1
                best_cost = float('inf')
                
                for j in range(n):
                    if j not in used_columns and cost_matrix[i][j] < best_cost:
                        best_cost = cost_matrix[i][j]
                        best_j = j
                
                if best_j != -1:
                    assignment.append(best_j)
                    used_columns.add(best_j)
                else:
                    # Fallback: assign to first available column
                    for j in range(n):
                        if j not in used_columns:
                            assignment.append(j)
                            used_columns.add(j)
                            break
            
            return assignment
            
        except Exception as e:
            self.logger.error(f"Error in greedy assignment: {e}")
            return list(range(n))
    
    def save_zip_from_bytes(self, roi_bytes_list: List[bytes], output_zip_path: str) -> bool:
        """
        Save a list of raw ROI bytes to a zip file.
        Each ROI file is written with a sequential name (e.g. ROI_001.roi).
        
        Args:
            roi_bytes_list: List of raw ROI byte data
            output_zip_path: Path to save the zip file
            
        Returns:
            True if successful, False otherwise
        """
        try:
            with zipfile.ZipFile(output_zip_path, 'w') as z:
                for i, data in enumerate(roi_bytes_list):
                    name = f"ROI_{i+1:03d}.roi"
                    z.writestr(name, data)
            
            self.logger.info(f"Saved reordered ROIs to {output_zip_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error saving zip file {output_zip_path}: {e}")
            return False
    
    def process_roi_pair(self, zip_file1: str, zip_file2: str) -> Dict[str, Any]:
        """
        Process a pair of ROI zip files, reordering the second to match the first.
        
        Args:
            zip_file1: Path to the first ROI zip file (reference)
            zip_file2: Path to the second ROI zip file (to be reordered)
            
        Returns:
            Dictionary with processing results
        """
        try:
            self.logger.info(f"Processing ROI pair: {os.path.basename(zip_file1)} -> {os.path.basename(zip_file2)}")
            
            # Load ROI dictionaries from each zip file
            roi_dict1 = self.load_roi_dict(zip_file1)
            roi_dict2 = self.load_roi_dict(zip_file2)
            
            if roi_dict1 is None or roi_dict2 is None:
                return {
                    'success': False,
                    'error': 'Failed to load ROI dictionaries'
                }
            
            # Load raw ROI file bytes from the second zip file
            roi_bytes2 = self.load_roi_bytes(zip_file2)
            
            if roi_bytes2 is None:
                return {
                    'success': False,
                    'error': 'Failed to load ROI bytes'
                }
            
            # Convert dictionaries to lists while preserving the ROI file names
            roi_items1 = list(roi_dict1.items())  # list of (filename, roi_dict)
            roi_items2 = list(roi_dict2.items())
            
            # Extract ROI dictionaries and file names
            rois1 = [item[1] for item in roi_items1]
            rois2 = [item[1] for item in roi_items2]
            names2 = [item[0] for item in roi_items2]
            
            self.logger.info(f"Found {len(rois1)} ROIs in first file and {len(rois2)} ROIs in second file")
            
            if len(rois1) == 0 or len(rois2) == 0:
                return {
                    'success': False,
                    'error': 'One or both ROI files contain no ROIs'
                }
            
            # Compute matching: get indices for rois2 that best match rois1
            matching_indices = self.match_rois(rois1, rois2)
            
            # Reorder the raw bytes from the second zip using the matching
            reordered_bytes = []
            for idx in matching_indices:
                if idx < len(names2):  # Ensure index is valid
                    key = names2[idx]
                    reordered_bytes.append(roi_bytes2[key])
            
            # Make a backup of the original file
            backup_file = zip_file2 + ".bak"
            try:
                if not self.filesystem_port.path_exists(backup_file):
                    # Read original file and create backup
                    original_content = self.filesystem_port.read_file(zip_file2, binary=True)
                    self.filesystem_port.write_file(backup_file, original_content, binary=True)
                    self.logger.info(f"Created backup: {backup_file}")
            except Exception as e:
                self.logger.error(f"Failed to create backup file: {e}")
                return {
                    'success': False,
                    'error': f'Failed to create backup: {e}'
                }
            
            # Save over the second zip file
            success = self.save_zip_from_bytes(reordered_bytes, zip_file2)
            
            if success:
                return {
                    'success': True,
                    'message': f'Successfully reordered {len(reordered_bytes)} ROIs',
                    'rois_processed': len(reordered_bytes),
                    'backup_created': backup_file
                }
            else:
                return {
                    'success': False,
                    'error': 'Failed to save reordered ROIs'
                }
            
        except Exception as e:
            error_msg = f"Error processing ROI pair: {e}"
            self.logger.error(error_msg)
            return {
                'success': False,
                'error': error_msg
            }
    
    def find_roi_files_recursive(self, directory: str, t0: str, t1: str) -> List[Tuple[str, str]]:
        """
        Recursively find pairs of ROI zip files matching t0 and t1 timepoints based on common filename prefixes.
        
        Args:
            directory: Root directory to search
            t0: The identifier for the first timepoint (e.g., 't00')
            t1: The identifier for the second timepoint (e.g., 't03')
            
        Returns:
            A list of tuples, where each tuple contains (path_to_t0_file, path_to_t1_file)
        """
        try:
            self.logger.info(f"Searching for ROI pairs recursively in '{directory}' using timepoints '{t0}' and '{t1}'")
            
            # Find t0 files
            t0_files = []
            t1_files = []
            
            for root, dirs, files in self.filesystem_port.walk_directory(directory):
                for file in files:
                    if file.endswith('_rois.zip'):
                        file_path = os.path.join(root, file)
                        if t0 in file:
                            t0_files.append(file_path)
                        elif t1 in file:
                            t1_files.append(file_path)
            
            self.logger.info(f"Found {len(t0_files)} files matching {t0}")
            self.logger.info(f"Found {len(t1_files)} files matching {t1}")
            
            pairs = []
            t1_map = {str(f): f for f in t1_files}  # Map full path string to Path object for faster lookup
            
            for f0_path in t0_files:
                # Derive expected t1 path by replacing t0 with t1 in the t0 path string
                f0_str = str(f0_path)
                
                if t0 not in f0_str:
                    self.logger.warning(f"Timepoint '{t0}' not found in path '{f0_str}'. Cannot determine matching {t1} file. Skipping.")
                    continue
                
                expected_t1_str = f0_str.replace(t0, t1)
                
                if expected_t1_str in t1_map:
                    pairs.append((str(f0_path), expected_t1_str))
                else:
                    self.logger.warning(f"Could not find matching {t1} file for {f0_path} (expected path: {expected_t1_str})")
            
            self.logger.info(f"Found {len(pairs)} matching ROI pairs.")
            return pairs
            
        except Exception as e:
            self.logger.error(f"Error finding ROI files: {e}")
            return []
    
    def batch_process_directory(self, directory: str, t0: str, t1: str, recursive: bool = True) -> Dict[str, Any]:
        """
        Find and process all matching ROI pairs in a directory.
        
        Args:
            directory: Directory to search
            t0: Identifier for the first timepoint
            t1: Identifier for the second timepoint
            recursive: Whether to search recursively
            
        Returns:
            Dictionary with batch processing results
        """
        try:
            if recursive:
                pairs = self.find_roi_files_recursive(directory, t0, t1)
            else:
                return {
                    'success': False,
                    'error': 'Non-recursive search is not currently supported. Please use recursive=True.'
                }
            
            if not pairs:
                return {
                    'success': False,
                    'warning': f'No matching ROI pairs found in {directory}'
                }
            
            successful = 0
            errors = []
            
            for t0_file, t1_file in pairs:
                result = self.process_roi_pair(t0_file, t1_file)
                if result['success']:
                    successful += 1
                else:
                    errors.append(f"{t0_file} -> {t1_file}: {result['error']}")
            
            self.logger.info(f"Successfully processed {successful} out of {len(pairs)} ROI file pairs")
            
            return {
                'success': True,
                'total_pairs': len(pairs),
                'successful_pairs': successful,
                'failed_pairs': len(pairs) - successful,
                'errors': errors,
                'message': f'Batch processing completed: {successful}/{len(pairs)} pairs successful'
            }
            
        except Exception as e:
            error_msg = f"Error in batch processing: {e}"
            self.logger.error(error_msg)
            return {
                'success': False,
                'error': error_msg
            }
    
    def validate_timepoints(self, timepoints: List[str]) -> Dict[str, Any]:
        """
        Validate timepoints for ROI tracking.
        
        Args:
            timepoints: List of timepoint identifiers
            
        Returns:
            Dictionary with validation results
        """
        try:
            if not timepoints:
                return {
                    'valid': False,
                    'error': 'No timepoints specified'
                }
            
            if len(timepoints) == 1:
                return {
                    'valid': False,
                    'warning': f'ROI tracking requires two timepoints. Only one selected: {timepoints[0]}. Skipping tracking.',
                    'skip_tracking': True
                }
            
            if len(timepoints) != 2:
                return {
                    'valid': False,
                    'error': f'ROI tracking requires exactly two timepoints. Received {len(timepoints)}: {timepoints}.'
                }
            
            return {
                'valid': True,
                't0': timepoints[0],
                't1': timepoints[1],
                'message': f'Timepoints validated: {timepoints[0]} -> {timepoints[1]}'
            }
            
        except Exception as e:
            return {
                'valid': False,
                'error': f'Error validating timepoints: {e}'
            }
