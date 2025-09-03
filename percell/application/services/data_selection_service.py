"""
Data Selection Application Service.

This service implements the use case for data selection, including:
- Setting up output directory structure
- Preparing input directory structure
- Extracting experiment metadata
- Interactive data selection
- Copying selected files
"""

import os
import re
from pathlib import Path
from typing import Dict, List, Optional, Any, Set, Tuple

from percell.domain.ports import (
    FileSystemPort, 
    LoggingPort,
    SubprocessPort
)
from percell.domain.exceptions import (
    FileSystemError, 
    SubprocessError
)


class DataSelectionService:
    """
    Application service for data selection.
    
    This service coordinates the domain operations needed to:
    1. Set up output directory structure
    2. Prepare input directory structure
    3. Extract experiment metadata
    4. Run interactive data selection
    5. Copy selected files to output directory
    """
    
    def __init__(
        self,
        filesystem_port: FileSystemPort,
        logging_port: LoggingPort,
        subprocess_port: SubprocessPort
    ):
        self.filesystem_port = filesystem_port
        self.logging_port = logging_port
        self.subprocess_port = subprocess_port
        self.logger = logging_port.get_logger("DataSelectionService")
    
    def execute_data_selection(
        self,
        input_dir: str,
        output_dir: str,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Execute the complete data selection process.
        
        Args:
            input_dir: Input directory containing raw data
            output_dir: Output directory for analysis
            **kwargs: Additional parameters (conditions, regions, timepoints, channels, etc.)
            
        Returns:
            Dict containing data selection results and metadata
        """
        try:
            self.logger.info("Starting data selection process...")
            self.logger.info(f"Input directory: {input_dir}")
            self.logger.info(f"Output directory: {output_dir}")
            
            # Step 1: Set up output directory structure
            self.logger.info("Setting up output directory structure...")
            if not self._setup_output_structure(output_dir):
                return {"success": False, "error": "Failed to setup output directory structure"}
            
            # Step 2: Prepare input directory structure
            self.logger.info("Preparing input directory structure...")
            if not self._prepare_input_structure(input_dir):
                return {"success": False, "error": "Failed to prepare input directory structure"}
            
            # Step 3: Extract experiment metadata
            self.logger.info("Extracting experiment metadata...")
            metadata = self._extract_experiment_metadata(input_dir)
            if not metadata:
                return {"success": False, "error": "Failed to extract experiment metadata"}
            
            # Step 4: Run interactive data selection
            self.logger.info("Starting interactive data selection...")
            selections = self._run_interactive_selection(metadata, **kwargs)
            if not selections:
                return {"success": False, "error": "Data selection was cancelled or failed"}
            
            # Step 5: Copy selected files
            self.logger.info("Copying selected files to output directory...")
            if not self._copy_selected_files(input_dir, output_dir, selections):
                return {"success": False, "error": "Failed to copy selected files"}
            
            # Combine metadata and selections
            result = {
                "success": True,
                "message": "Data selection completed successfully",
                "metadata": metadata,
                "selections": selections,
                "input_dir": input_dir,
                "output_dir": output_dir
            }
            
            self.logger.info("Data selection process completed successfully")
            return result
            
        except Exception as e:
            self.logger.error(f"Error in execute_data_selection: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def _setup_output_structure(self, output_dir: str) -> bool:
        """Set up the output directory structure."""
        try:
            # Create main output directories
            main_dirs = [
                'ROIs', 'analysis', 'cells', 'combined_masks', 'grouped_cells',
                'grouped_masks', 'logs', 'masks', 'preprocessed', 'raw_data'
            ]
            
            for dir_name in main_dirs:
                dir_path = Path(output_dir) / dir_name
                dir_path.mkdir(parents=True, exist_ok=True)
                self.logger.debug(f"Created directory: {dir_path}")
            
            # Create logs subdirectory
            logs_dir = Path(output_dir) / 'logs'
            logs_dir.mkdir(parents=True, exist_ok=True)
            
            self.logger.info("Output directory structure setup complete")
            return True
            
        except Exception as e:
            self.logger.error(f"Error setting up output directory structure: {e}")
            return False
    
    def _prepare_input_structure(self, input_dir: str) -> bool:
        """Prepare the input directory structure."""
        try:
            # Run the setup_input_structure.sh script
            script_path = "percell/bash/prepare_input_structure.sh"
            cmd = ["bash", script_path, input_dir]
            
            result = self.subprocess_port.run_with_progress(
                cmd,
                title="Prepare Input Structure"
            )
            
            if result == 0:
                self.logger.info("Input directory structure prepared successfully")
                return True
            else:
                self.logger.error("Failed to prepare input directory structure")
                return False
                
        except Exception as e:
            self.logger.error(f"Error preparing input directory structure: {e}")
            return False
    
    def _extract_experiment_metadata(self, input_dir: str) -> Optional[Dict[str, Any]]:
        """Extract experiment metadata from the input directory."""
        try:
            input_path = Path(input_dir)
            if not input_path.exists():
                self.logger.error(f"Input directory does not exist: {input_dir}")
                return None
            
            # Scan for conditions (top-level directories)
            conditions = []
            regions = set()
            timepoints = set()
            channels = set()
            directory_timepoints = []
            
            for item in input_path.iterdir():
                if item.is_dir() and not item.name.startswith('.'):
                    conditions.append(item.name)
                    
                    # Scan condition directory for timepoints and files
                    for subitem in item.iterdir():
                        if subitem.is_dir():
                            directory_timepoints.append(subitem.name)
                            
                            # Look for TIF files to extract metadata
                            for tif_file in subitem.glob("*.tif"):
                                filename = tif_file.name
                                region, timepoint, channel = self._extract_metadata_from_filename(filename)
                                if region:
                                    regions.add(region)
                                if timepoint:
                                    timepoints.add(timepoint)
                                if channel:
                                    channels.add(channel)
            
            # Convert sets to sorted lists
            regions = sorted(list(regions))
            timepoints = sorted(list(timepoints))
            channels = sorted(list(channels))
            directory_timepoints = sorted(list(set(directory_timepoints)))
            
            # Infer datatype
            datatype_inferred = 'multi_timepoint' if len(timepoints) > 1 else 'single_timepoint'
            
            metadata = {
                'conditions': conditions,
                'regions': regions,
                'timepoints': timepoints,
                'channels': channels,
                'directory_timepoints': directory_timepoints,
                'datatype_inferred': datatype_inferred
            }
            
            self.logger.info(f"Extracted metadata: {metadata}")
            return metadata
            
        except Exception as e:
            self.logger.error(f"Error extracting experiment metadata: {e}")
            return None
    
    def _extract_metadata_from_filename(self, filename: str) -> Tuple[Optional[str], Optional[str], Optional[str]]:
        """Extract region, timepoint, and channel from filename."""
        try:
            # Extract region (everything before channel and timepoint)
            region_match = re.search(r'(.+?)_(ch\d+)_(t\d+)', filename)
            if region_match:
                region = region_match.group(1)
                channel = region_match.group(2)
                timepoint = region_match.group(3)
                return region, timepoint, channel
            
            # Fallback extraction
            parts = filename.split('_')
            channel = None
            timepoint = None
            region = None
            
            for i, part in enumerate(parts):
                if part.startswith('ch'):
                    channel = part
                    if i > 0:
                        region = '_'.join(parts[:i])
                elif part.startswith('t'):
                    timepoint = part
            
            return region, timepoint, channel
            
        except Exception as e:
            self.logger.debug(f"Error extracting metadata from {filename}: {e}")
            return None, None, None
    
    def _run_interactive_selection(self, metadata: Dict[str, Any], **kwargs) -> Optional[Dict[str, Any]]:
        """Run interactive data selection."""
        try:
            # Use provided selections if available, otherwise use extracted metadata as defaults
            datatype = kwargs.get('datatype') or metadata.get('datatype_inferred', 'single_timepoint')
            conditions = kwargs.get('conditions') or metadata.get('conditions', [])
            regions = kwargs.get('regions') or metadata.get('regions', [])
            timepoints = kwargs.get('timepoints') or metadata.get('timepoints', [])
            channels = kwargs.get('channels') or metadata.get('channels', [])
            
            # Ensure we have valid values (not None)
            if conditions is None:
                conditions = metadata.get('conditions', [])
            if regions is None:
                regions = metadata.get('regions', [])
            if timepoints is None:
                timepoints = metadata.get('timepoints', [])
            if channels is None:
                channels = metadata.get('channels', [])
            
            # For now, use the provided or default values
            # In a full implementation, this would prompt the user interactively
            selections = {
                'datatype': datatype,
                'conditions': conditions,
                'regions': regions,
                'timepoints': timepoints,
                'channels': channels,
                'segmentation_channel': channels[0] if channels else 'ch01',
                'analysis_channels': channels
            }
            
            self.logger.info(f"Data selections: {selections}")
            return selections
            
        except Exception as e:
            self.logger.error(f"Error in interactive selection: {e}")
            return None
    
    def _copy_selected_files(self, input_dir: str, output_dir: str, selections: Dict[str, Any]) -> bool:
        """Copy selected files to the output directory."""
        try:
            input_path = Path(input_dir)
            output_path = Path(output_dir)
            raw_data_dir = output_path / 'raw_data'
            
            conditions = selections.get('conditions', [])
            timepoints = selections.get('timepoints', [])
            
            total_files_copied = 0
            
            for condition in conditions:
                condition_input_dir = input_path / condition
                condition_output_dir = raw_data_dir / condition
                
                if not condition_input_dir.exists():
                    continue
                
                # Create condition output directory
                condition_output_dir.mkdir(parents=True, exist_ok=True)
                
                # Copy timepoint directories
                for timepoint in timepoints:
                    # Map timepoint to directory timepoint
                    timepoint_dir = None
                    for item in condition_input_dir.iterdir():
                        if item.is_dir() and timepoint in item.name:
                            timepoint_dir = item
                            break
                    
                    # If no direct match, try to map t00 -> timepoint_1, t01 -> timepoint_2, etc. (1-based)
                    if timepoint_dir is None:
                        timepoint_number = timepoint.replace('t', '')
                        try:
                            # Convert to int and shift to 1-based indexing used by directory naming
                            timepoint_number_int = int(timepoint_number) + 1
                            expected_dir_name = f"timepoint_{timepoint_number_int}"
                            expected_dir_path = condition_input_dir / expected_dir_name
                            if expected_dir_path.exists() and expected_dir_path.is_dir():
                                timepoint_dir = expected_dir_path
                                self.logger.info(f"Mapped timepoint {timepoint} to directory {expected_dir_name}")
                        except ValueError:
                            pass
                    
                    if timepoint_dir:
                        timepoint_output_dir = condition_output_dir / timepoint_dir.name
                        timepoint_output_dir.mkdir(parents=True, exist_ok=True)
                        
                        self.logger.info(f"Processing timepoint directory: {timepoint_dir}")
                        self.logger.info(f"Output directory: {timepoint_output_dir}")
                        
                        # Copy TIFF files (support .tif/.tiff, case-insensitive)
                        tif_patterns = ["*.tif", "*.tiff", "*.TIF", "*.TIFF"]
                        tif_files = []
                        for pat in tif_patterns:
                            tif_files.extend(timepoint_dir.glob(pat))
                        # De-duplicate
                        tif_files = list({p for p in tif_files})
                        self.logger.info(f"Found {len(tif_files)} TIFF files in {timepoint_dir}")
                        
                        for tif_file in tif_files:
                            output_file = timepoint_output_dir / tif_file.name
                            self.logger.info(f"Copying {tif_file} to {output_file}")
                            
                            if not output_file.exists():
                                # Use filesystem port to copy file
                                try:
                                    content = self.filesystem_port.read_file(tif_file, binary=True)
                                    self.filesystem_port.write_file(output_file, content, binary=True)
                                    total_files_copied += 1
                                    self.logger.info(f"Successfully copied {tif_file}")
                                except Exception as e:
                                    self.logger.warning(f"Could not copy {tif_file}: {e}")
                                    continue
                            else:
                                self.logger.info(f"File already exists: {output_file}")
                                total_files_copied += 1
                    else:
                        self.logger.warning(f"Could not find timepoint directory for {timepoint} in {condition_input_dir}")
            
            self.logger.info(f"File copy completed. Total files copied: {total_files_copied}")
            # Allow 0 files to be copied (might be valid in some cases)
            return True
            
        except Exception as e:
            self.logger.error(f"Error copying selected files: {e}")
            return False
