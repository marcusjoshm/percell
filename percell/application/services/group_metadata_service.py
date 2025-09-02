#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Group Metadata Service for Single Cell Analysis Workflow

This service takes the cell group metadata created during cell clustering
and incorporates it into the final analysis table, allowing for correlation
between expression level groups and cell phenotypes.
"""

import os
import re
from pathlib import Path
from typing import List, Dict, Any, Optional
from percell.domain.ports import FileSystemPort, LoggingPort


class GroupMetadataService:
    """
    Service for including cell group metadata in analysis results.
    
    This service merges group metadata with analysis results, enabling
    correlation between expression level groups and cell phenotypes.
    """
    
    def __init__(
        self,
        filesystem_port: FileSystemPort,
        logging_port: LoggingPort
    ):
        """
        Initialize the Group Metadata Service.
        
        Args:
            filesystem_port: Port for file system operations
            logging_port: Port for logging operations
        """
        self.filesystem_port = filesystem_port
        self.logging_port = logging_port
        self.logger = self.logging_port.get_logger("GroupMetadataService")
    
    def read_csv_robust(self, file_path: str) -> Optional[Dict[str, Any]]:
        """
        Read CSV file with robust encoding handling.
        
        Args:
            file_path: Path to the CSV file
            
        Returns:
            Dictionary representation of the CSV data, or None if failed
        """
        encodings = ['utf-8', 'utf-8-sig', 'latin-1', 'cp1252', 'iso-8859-1']
        
        for encoding in encodings:
            try:
                # For now, we'll return a placeholder since we don't have pandas in the domain
                # In a real implementation, this would use a CSV reading port
                content = self.filesystem_port.read_file(file_path, encoding=encoding)
                self.logger.debug(f"Successfully read {file_path} with {encoding} encoding")
                
                # Parse CSV content manually (basic implementation)
                lines = content.split('\n')
                if not lines:
                    return None
                
                # Parse header
                header = lines[0].split(',')
                
                # Parse data rows
                data = []
                for line in lines[1:]:
                    if line.strip():
                        values = line.split(',')
                        row = {}
                        for i, value in enumerate(values):
                            if i < len(header):
                                row[header[i].strip()] = value.strip()
                        data.append(row)
                
                return {
                    'columns': header,
                    'data': data,
                    'content': content
                }
                
            except Exception as e:
                self.logger.debug(f"Failed to read {file_path} with {encoding} encoding: {e}")
                continue
        
        self.logger.error(f"Failed to read {file_path} with any supported encoding")
        return None
    
    def find_group_metadata_files(self, grouped_cells_dir: str) -> List[str]:
        """
        Find all cell group metadata CSV files.
        
        Args:
            grouped_cells_dir: Directory containing grouped cell metadata files
            
        Returns:
            List of paths to cell group metadata files
        """
        try:
            metadata_files = []
            
            # Convert to Path object if not already
            grouped_cells_path = Path(grouped_cells_dir)
            
            if not self.filesystem_port.path_exists(grouped_cells_dir):
                self.logger.error(f"Grouped cells directory not found: {grouped_cells_dir}")
                return metadata_files
            
            # Find all *_cell_groups.csv files recursively
            for root, dirs, files in self.filesystem_port.walk_directory(grouped_cells_dir):
                for file in files:
                    if file.endswith('_cell_groups.csv') and not file.startswith('._'):
                        file_path = os.path.join(root, file)
                        metadata_files.append(file_path)
            
            self.logger.info(f"Found {len(metadata_files)} group metadata files")
            return metadata_files
            
        except Exception as e:
            self.logger.error(f"Error finding group metadata files: {e}")
            return []
    
    def find_analysis_file(self, analysis_dir: str, output_dir: Optional[str] = None) -> Optional[str]:
        """
        Find the combined analysis CSV file.
        
        Args:
            analysis_dir: Directory containing analysis results
            output_dir: Base output directory for the entire workflow
            
        Returns:
            Path to the combined analysis file, or None if not found
        """
        try:
            if not self.filesystem_port.path_exists(analysis_dir):
                self.logger.error(f"Analysis directory not found: {analysis_dir}")
                return None
            
            # If output_dir is specified, try to find dish-specific combined analysis file
            if output_dir:
                # Get dish name from output directory
                output_path = Path(output_dir)
                dish_name = output_path.name.replace('_analysis_', '').replace('/', '_')
                
                # Look for dish-specific combined files
                dish_combined = os.path.join(analysis_dir, f"{dish_name}_combined_analysis.csv")
                if self.filesystem_port.path_exists(dish_combined):
                    self.logger.info(f"Found dish-specific combined analysis file: {dish_combined}")
                    return dish_combined
            
            # Look for particle analysis CSVs produced by the analysis step
            particle_files = []
            for root, dirs, files in self.filesystem_port.walk_directory(analysis_dir):
                for file in files:
                    if file.endswith('particle_analysis.csv') and not file.startswith('._'):
                        file_path = os.path.join(root, file)
                        particle_files.append(file_path)
            
            if particle_files:
                # Sort by file size (largest first)
                particle_files.sort(key=lambda f: self.filesystem_port.get_file_size(f), reverse=True)
                self.logger.info(f"Found particle analysis file: {particle_files[0]}")
                return particle_files[0]
            
            # Look for combined_results.csv or similar
            for pattern in ["*combined*.csv", "*combined_analysis.csv", "combined_results.csv"]:
                combined_files = []
                for root, dirs, files in self.filesystem_port.walk_directory(analysis_dir):
                    for file in files:
                        if (file.endswith('.csv') and 
                            not file.startswith('._') and 
                            'cell_area' not in file and
                            'combined' in file.lower()):
                            file_path = os.path.join(root, file)
                            combined_files.append(file_path)
                
                if combined_files:
                    # Sort by file size (largest first)
                    combined_files.sort(key=lambda f: self.filesystem_port.get_file_size(f), reverse=True)
                    self.logger.info(f"Found combined analysis file: {combined_files[0]}")
                    return combined_files[0]
            
            # If not found, look for any CSV file that might be the combined results
            csv_files = []
            for root, dirs, files in self.filesystem_port.walk_directory(analysis_dir):
                for file in files:
                    if file.endswith('.csv') and not file.startswith('._') and 'cell_area' not in file:
                        file_path = os.path.join(root, file)
                        csv_files.append(file_path)
            
            if csv_files:
                # Use the largest CSV file as it's likely the combined results
                csv_files.sort(key=lambda f: self.filesystem_port.get_file_size(f), reverse=True)
                self.logger.info(f"Using largest CSV file as combined analysis: {csv_files[0]}")
                return csv_files[0]
            
            self.logger.error(f"No CSV files found in {analysis_dir}")
            return None
            
        except Exception as e:
            self.logger.error(f"Error finding analysis file: {e}")
            return None
    
    def load_group_metadata(self, metadata_files: List[str]) -> Optional[Dict[str, Any]]:
        """
        Load and combine all group metadata files.
        
        Args:
            metadata_files: List of paths to metadata files
            
        Returns:
            Combined metadata dictionary, or None if failed
        """
        try:
            all_metadata = []
            
            for file_path in metadata_files:
                try:
                    df_data = self.read_csv_robust(file_path)
                    
                    if df_data is None:
                        self.logger.error(f"Failed to read {file_path}")
                        continue
                    
                    # Display sample data for debugging
                    sample_data = df_data['data'][:2] if df_data['data'] else []
                    self.logger.info(f"Sample data from {file_path}: {sample_data}")
                    
                    # Add source directory information to help with matching
                    parent_dir = os.path.dirname(file_path)
                    region_name = os.path.basename(parent_dir)
                    condition_name = os.path.basename(os.path.dirname(parent_dir)) if os.path.basename(parent_dir) != "grouped_cells" else ""
                    
                    # Add metadata columns
                    for row in df_data['data']:
                        row['region'] = region_name
                        if condition_name:
                            row['condition'] = condition_name
                    
                    all_metadata.append(df_data)
                    self.logger.info(f"Loaded {len(df_data['data'])} records from {file_path}")
                    
                except Exception as e:
                    self.logger.error(f"Error loading {file_path}: {e}")
            
            if not all_metadata:
                self.logger.error("No metadata files could be loaded")
                return None
            
            # Combine all metadata
            combined_data = []
            all_columns = set()
            
            for metadata in all_metadata:
                all_columns.update(metadata['columns'])
                combined_data.extend(metadata['data'])
            
            self.logger.info(f"Combined metadata contains {len(combined_data)} records")
            
            return {
                'columns': list(all_columns),
                'data': combined_data,
                'total_records': len(combined_data)
            }
            
        except Exception as e:
            self.logger.error(f"Error loading group metadata: {e}")
            return None
    
    def merge_metadata_with_analysis(
        self,
        group_metadata: Dict[str, Any],
        analysis_file_path: str,
        output_path: str,
        overwrite: bool = True,
        replace: bool = True
    ) -> Dict[str, Any]:
        """
        Merge group metadata with analysis results.
        
        Args:
            group_metadata: Group metadata dictionary
            analysis_file_path: Path to analysis results file
            output_path: Path to save the merged results
            overwrite: Whether to overwrite the original file
            replace: Whether to replace existing group data or keep it
            
        Returns:
            Dictionary with merge results
        """
        try:
            # Load analysis results
            analysis_data = self.read_csv_robust(analysis_file_path)
            if analysis_data is None:
                return {
                    'success': False,
                    'error': f'Failed to read analysis file: {analysis_file_path}'
                }
            
            self.logger.info(f"Loaded analysis file with {len(analysis_data['data'])} records")
            
            # Print column names for debugging
            self.logger.info(f"Analysis file columns: {analysis_data['columns']}")
            self.logger.info(f"Group metadata columns: {group_metadata['columns']}")
            
            # Check for duplicate cell entries in the analysis file
            if 'Slice' in analysis_data['columns']:
                slice_values = [row.get('Slice', '') for row in analysis_data['data']]
                dup_count = len(slice_values) - len(set(slice_values))
                if dup_count > 0:
                    self.logger.warning(f"Found {dup_count} duplicate cell entries in analysis file.")
            
            # Extract cell IDs for matching
            analysis_cell_ids = self._extract_cell_ids_from_analysis(analysis_data)
            metadata_cell_ids = self._extract_cell_ids_from_metadata(group_metadata)
            
            if not analysis_cell_ids or not metadata_cell_ids:
                return {
                    'success': False,
                    'error': 'Could not extract cell IDs from analysis or metadata files'
                }
            
            # Perform the merge
            merged_data = self._perform_merge(analysis_data, group_metadata, analysis_cell_ids, metadata_cell_ids)
            
            if merged_data is None:
                return {
                    'success': False,
                    'error': 'Failed to merge metadata with analysis data'
                }
            
            # Save merged results
            success = self._save_merged_results(merged_data, analysis_file_path, output_path, overwrite)
            
            if success:
                return {
                    'success': True,
                    'message': 'Successfully merged group metadata with analysis results',
                    'total_records': len(merged_data['data']),
                    'matched_records': sum(1 for row in merged_data['data'] if row.get('group_id') is not None)
                }
            else:
                return {
                    'success': False,
                    'error': 'Failed to save merged results'
                }
            
        except Exception as e:
            error_msg = f"Error merging data: {e}"
            self.logger.error(error_msg)
            return {
                'success': False,
                'error': error_msg
            }
    
    def _extract_cell_ids_from_analysis(self, analysis_data: Dict[str, Any]) -> List[str]:
        """
        Extract cell IDs from analysis data.
        
        Args:
            analysis_data: Analysis data dictionary
            
        Returns:
            List of extracted cell IDs
        """
        try:
            # Check if we can extract cell ID from Label, Slice, or other columns
            id_columns = ['Label', 'Slice', 'ROI']
            id_column = next((col for col in id_columns if col in analysis_data['columns']), None)
            
            if not id_column:
                return []
            
            self.logger.info(f"Using {id_column} column for cell identification")
            
            # Extract cell IDs
            cell_ids = []
            for row in analysis_data['data']:
                cell_id = row.get(id_column, '')
                if cell_id:
                    # Extract numeric part for matching
                    extracted_id = self._extract_numeric_id(str(cell_id))
                    cell_ids.append(extracted_id)
                    row['extracted_cell_id'] = extracted_id
            
            return cell_ids
            
        except Exception as e:
            self.logger.error(f"Error extracting cell IDs from analysis: {e}")
            return []
    
    def _extract_cell_ids_from_metadata(self, metadata: Dict[str, Any]) -> List[str]:
        """
        Extract cell IDs from metadata.
        
        Args:
            metadata: Metadata dictionary
            
        Returns:
            List of extracted cell IDs
        """
        try:
            if 'cell_id' not in metadata['columns']:
                return []
            
            cell_ids = []
            for row in metadata['data']:
                cell_id = row.get('cell_id', '')
                if cell_id:
                    # Clean up the cell_id values to improve matching
                    cleaned_id = str(cell_id).replace('CELL', '').replace('.tif', '').strip()
                    extracted_id = self._extract_numeric_id(cleaned_id)
                    cell_ids.append(extracted_id)
                    row['extracted_cell_id'] = extracted_id
            
            return cell_ids
            
        except Exception as e:
            self.logger.error(f"Error extracting cell IDs from metadata: {e}")
            return []
    
    def _extract_numeric_id(self, cell_id: str) -> str:
        """
        Extract numeric ID from cell ID string.
        
        Args:
            cell_id: Cell ID string
            
        Returns:
            Extracted numeric ID
        """
        try:
            # Special case for mask files with format R_1_t00_MASK_CELL1f
            cell_match = re.search(r'CELL(\d+)[a-zA-Z]*$', cell_id)
            if cell_match:
                return cell_match.group(1)  # Just the number part after CELL
            
            # Try to get the last segment after underscore
            if '_' in cell_id:
                last_part = cell_id.split('_')[-1]
                # Remove non-digit characters if it contains digits
                if any(c.isdigit() for c in last_part):
                    return ''.join(c for c in last_part if c.isdigit())
                return last_part
            
            # If nothing else works, just return any digits
            digits = ''.join(c for c in cell_id if c.isdigit())
            if digits:
                return digits
            
            return cell_id
            
        except Exception as e:
            self.logger.error(f"Error extracting numeric ID from '{cell_id}': {e}")
            return cell_id
    
    def _perform_merge(
        self,
        analysis_data: Dict[str, Any],
        metadata: Dict[str, Any],
        analysis_cell_ids: List[str],
        metadata_cell_ids: List[str]
    ) -> Optional[Dict[str, Any]]:
        """
        Perform the actual merge of analysis and metadata data.
        
        Args:
            analysis_data: Analysis data dictionary
            metadata: Metadata dictionary
            analysis_cell_ids: List of cell IDs from analysis
            metadata_cell_ids: List of cell IDs from metadata
            
        Returns:
            Merged data dictionary, or None if failed
        """
        try:
            # Create a mapping from metadata cell IDs to metadata rows
            metadata_map = {}
            for i, cell_id in enumerate(metadata_cell_ids):
                if cell_id not in metadata_map:
                    metadata_map[cell_id] = metadata['data'][i]
            
            # Merge data
            merged_data = []
            matched_count = 0
            
            for i, row in enumerate(analysis_data['data']):
                cell_id = analysis_cell_ids[i] if i < len(analysis_cell_ids) else None
                
                if cell_id and cell_id in metadata_map:
                    # Merge with metadata
                    merged_row = row.copy()
                    metadata_row = metadata_map[cell_id]
                    
                    # Add group columns
                    group_cols = ['group_id', 'group_name', 'group_mean_auc']
                    for col in group_cols:
                        if col in metadata_row:
                            merged_row[col] = metadata_row[col]
                    
                    merged_data.append(merged_row)
                    matched_count += 1
                else:
                    # No metadata match, keep original row
                    merged_data.append(row)
            
            self.logger.info(f"Matched {matched_count} of {len(merged_data)} records with group data")
            
            # Remove temporary columns
            for row in merged_data:
                if 'extracted_cell_id' in row:
                    del row['extracted_cell_id']
            
            return {
                'columns': analysis_data['columns'] + ['group_id', 'group_name', 'group_mean_auc'],
                'data': merged_data,
                'matched_count': matched_count
            }
            
        except Exception as e:
            self.logger.error(f"Error performing merge: {e}")
            return None
    
    def _save_merged_results(
        self,
        merged_data: Dict[str, Any],
        analysis_file_path: str,
        output_path: str,
        overwrite: bool
    ) -> bool:
        """
        Save merged results to file.
        
        Args:
            merged_data: Merged data dictionary
            analysis_file_path: Path to original analysis file
            output_path: Path to save merged results
            overwrite: Whether to overwrite the original file
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Convert data back to CSV format
            csv_content = self._convert_to_csv(merged_data)
            
            # Save to output path
            self.filesystem_port.write_file(output_path, csv_content)
            self.logger.info(f"Saved merged results to {output_path}")
            
            # Overwrite original file if requested
            if overwrite and output_path != analysis_file_path:
                self.filesystem_port.write_file(analysis_file_path, csv_content)
                self.logger.info(f"Updated original analysis file with group data: {analysis_file_path}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error saving merged results: {e}")
            return False
    
    def _convert_to_csv(self, data: Dict[str, Any]) -> str:
        """
        Convert data dictionary to CSV format.
        
        Args:
            data: Data dictionary with columns and data
            
        Returns:
            CSV formatted string
        """
        try:
            if not data['columns'] or not data['data']:
                return ""
            
            # Write header
            csv_lines = [','.join(data['columns'])]
            
            # Write data rows
            for row in data['data']:
                row_values = []
                for col in data['columns']:
                    value = row.get(col, '')
                    # Escape commas and quotes
                    if ',' in str(value) or '"' in str(value):
                        escaped_value = str(value).replace('"', '""')
                        value = f'"{escaped_value}"'
                    row_values.append(str(value))
                csv_lines.append(','.join(row_values))
            
            return '\n'.join(csv_lines)
            
        except Exception as e:
            self.logger.error(f"Error converting to CSV: {e}")
            return ""
    
    def process_group_metadata(
        self,
        grouped_cells_dir: str,
        analysis_dir: str,
        output_dir: Optional[str] = None,
        output_file: Optional[str] = None,
        overwrite: bool = True,
        replace: bool = True,
        channels: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Main method to process group metadata and merge with analysis results.
        
        Args:
            grouped_cells_dir: Directory containing grouped cell metadata
            analysis_dir: Directory containing analysis results
            output_dir: Directory to save updated analysis results
            output_file: Specific output file name
            overwrite: Whether to overwrite existing output files
            replace: Whether to replace existing group columns
            channels: Channels to process
            
        Returns:
            Dictionary with processing results
        """
        try:
            # Find all group metadata files
            metadata_files = self.find_group_metadata_files(grouped_cells_dir)
            
            if not metadata_files:
                return {
                    'success': False,
                    'error': 'No group metadata files found'
                }
            
            # Filter metadata files by channels if specified
            if channels:
                filtered_files = []
                for metadata_file in metadata_files:
                    file_channels = [ch for ch in channels if ch in metadata_file]
                    if file_channels:
                        self.logger.info(f"Including {metadata_file} for channels {file_channels}")
                        filtered_files.append(metadata_file)
                    else:
                        self.logger.info(f"Skipping {metadata_file} - no matching channels")
                metadata_files = filtered_files
            
            if not metadata_files:
                return {
                    'success': False,
                    'error': 'No metadata files match the specified channels'
                }
            
            # Load and combine all metadata
            group_metadata = self.load_group_metadata(metadata_files)
            if group_metadata is None:
                return {
                    'success': False,
                    'error': 'Failed to load group metadata'
                }
            
            # Find the analysis file
            analysis_file = self.find_analysis_file(analysis_dir, output_dir)
            if not analysis_file:
                return {
                    'success': False,
                    'error': 'No analysis file found'
                }
            
            # Determine output path
            if output_file:
                output_path = output_file
            elif output_dir:
                output_path = os.path.join(output_dir, os.path.basename(analysis_file))
            else:
                output_path = analysis_file
            
            # Merge metadata with analysis results
            result = self.merge_metadata_with_analysis(
                group_metadata,
                analysis_file,
                output_path,
                overwrite=overwrite,
                replace=replace
            )
            
            return result
            
        except Exception as e:
            error_msg = f"Error processing group metadata: {e}"
            self.logger.error(error_msg)
            return {
                'success': False,
                'error': error_msg
            }
