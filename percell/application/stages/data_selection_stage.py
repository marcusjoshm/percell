"""
DataSelectionStage - Application Layer Stage

Auto-generated from stage_classes.py split.
"""

from __future__ import annotations

import subprocess
import os
import re
import sys
import shutil
from pathlib import Path
from typing import Dict, Any, List, Set, Optional

from percell.application.progress_api import run_subprocess_with_spinner
from percell.domain import WorkflowOrchestrationService
from percell.domain.models import WorkflowStep, WorkflowState, WorkflowConfig
from percell.domain import DataSelectionService, FileNamingService
from percell.application.stages_api import StageBase


class DataSelectionStage(StageBase):
    """
    Data Selection Stage
    
    Handles the selection of conditions, regions, timepoints, and channels for analysis.
    Includes: prepare_input_structure, select_datatype, select_condition, select_timepoints, 
             select_regions, select_segmentation_channel, select_analysis_channels
    """
    
    def __init__(self, config, logger, stage_name="data_selection"):
        super().__init__(config, logger, stage_name)
        self.experiment_metadata = {}
        self.selected_datatype = None
        self.selected_conditions = []
        self.selected_timepoints = []
        self.selected_regions = []
        self.segmentation_channel = None
        self.analysis_channels = []
        # Domain services for parsing/scanning
        self._selection_service = DataSelectionService()
        self._naming_service = FileNamingService()
        
    def validate_inputs(self, **kwargs) -> bool:
        """Validate inputs for data selection stage."""
        input_dir = kwargs.get('input_dir')
        output_dir = kwargs.get('output_dir')
        if not input_dir or not Path(input_dir).exists():
            self.logger.error(f"Input directory does not exist: {input_dir}")
            return False
        if not output_dir:
            self.logger.error("Output directory is required")
            return False
        return True
    
    def run(self, **kwargs) -> bool:
        """Run the data selection stage."""
        try:
            self.logger.info("Starting Data Selection Stage")
            
            # Store input and output directories for later use
            self.input_dir = Path(kwargs['input_dir'])
            self.output_dir = Path(kwargs['output_dir'])
            # Injected filesystem port (optional)
            self._fs = kwargs.get('fs')
            
            # Step 1: Setup output directory structure
            self.logger.info("Setting up output directory structure...")
            if not self._setup_output_structure():
                return False
            
            # Step 2: Prepare input structure
            self.logger.info("Preparing input structure...")
            if not self._prepare_input_structure(str(self.input_dir)):
                return False
            
            # Step 3: Extract experiment metadata
            self.logger.info("Extracting experiment metadata...")
            if not self._extract_experiment_metadata(str(self.input_dir)):
                return False
            
            # Step 4: Interactive data selection
            self.logger.info("Starting interactive data selection...")
            if not self._run_interactive_selection():
                return False
            
            # Step 5: Save selections to config
            self.logger.info("Saving data selections...")
            self._save_selections_to_config()

            # Step 6: Create selected condition directories
            self.logger.info("Creating directories for selected conditions...")
            if not self._create_selected_condition_directories():
                return False

            # Step 7: Copy selected files to output
            self.logger.info("Copying selected files to output directory...")
            if not self._copy_selected_files():
                return False
            
            self.logger.info("Data Selection Stage completed successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Error in Data Selection Stage: {e}")
            return False
    
    def _setup_output_structure(self) -> bool:
        """Set up the output directory structure using the setup_output_structure.sh script."""
        try:
            self.logger.info("Starting output directory structure setup...")
            
            # Use the setup_output_structure.sh script
            from percell.application.paths_api import get_path, ensure_executable
            script_path = get_path("setup_output_structure_script")
            
            # Make sure the script is executable (prefer injected filesystem port)
            fs_port = getattr(self, '_fs', None)
            try:
                if fs_port is not None:
                    from percell.application.paths_api import get_path
                    fs_port.ensure_executable(get_path("setup_output_structure_script"))
                else:
                    from percell.adapters.local_filesystem_adapter import LocalFileSystemAdapter
                    from percell.application.paths_api import get_path
                    LocalFileSystemAdapter().ensure_executable(get_path("setup_output_structure_script"))
            except Exception:
                pass
            
            self.logger.info(f"Running setup_output_structure.sh with input: {self.input_dir}, output: {self.output_dir}")
            
            # Run the script to create directory structure (no file copying yet)
            result = subprocess.run([str(script_path), str(self.input_dir), str(self.output_dir)], 
                                  capture_output=True, text=True)
            
            if result.returncode != 0:
                self.logger.error(f"setup_output_structure.sh failed: {result.stderr}")
                return False
            
            self.logger.info("Output directory structure setup complete")
            self.logger.info(f"Script output: {result.stdout}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error setting up output structure: {e}")
            return False

    def _create_selected_condition_directories(self) -> bool:
        """Create raw_data subdirectories only for selected conditions."""
        try:
            self.logger.info("Creating directories for selected conditions...")

            selected_conditions = self.selected_conditions
            if not selected_conditions:
                self.logger.warning("No conditions selected, skipping directory creation")
                return True

            # Get directory timepoints for creating subdirectory structure
            directory_timepoints = self.experiment_metadata.get('directory_timepoints', [])

            for condition in selected_conditions:
                condition_input_dir = self.input_dir / condition
                condition_output_dir = self.output_dir / "raw_data" / condition

                self.logger.info(f"Creating directory structure for condition: {condition}")

                if not condition_input_dir.exists():
                    self.logger.warning(f"Condition directory not found in input: {condition_input_dir}")
                    continue

                # Create condition directory in raw_data
                condition_output_dir.mkdir(parents=True, exist_ok=True)
                self.logger.info(f"Created: {condition_output_dir}")

                # Create subdirectories for timepoints if they exist in the input
                for timepoint_dir in condition_input_dir.iterdir():
                    if timepoint_dir.is_dir():
                        timepoint_name = timepoint_dir.name
                        timepoint_output_dir = condition_output_dir / timepoint_name
                        timepoint_output_dir.mkdir(parents=True, exist_ok=True)
                        self.logger.info(f"Created: {timepoint_output_dir}")

            self.logger.info("Directory creation for selected conditions completed")
            return True

        except Exception as e:
            self.logger.error(f"Error creating selected condition directories: {e}")
            return False

    def _copy_selected_files(self) -> bool:
        """Copy only the selected files to the output directory after data selection."""
        try:
            self.logger.info("Copying selected files to output directory...")
            
            # Use the instance variables that were set during interactive selection
            selected_conditions = self.selected_conditions
            selected_timepoints = self.selected_timepoints
            selected_regions = self.selected_regions
            
            self.logger.info(f"Selected conditions: {selected_conditions}")
            self.logger.info(f"Selected timepoints: {selected_timepoints}")
            self.logger.info(f"Selected regions: {selected_regions}")
            
            if not selected_conditions:
                self.logger.warning("No conditions selected, skipping file copy")
                return True
            
            # Get directory timepoints for mapping
            directory_timepoints = self.experiment_metadata.get('directory_timepoints', [])
            self.logger.info(f"Available directory timepoints: {directory_timepoints}")
            
            total_copied = 0
            
            for condition in selected_conditions:
                condition_input_dir = self.input_dir / condition
                condition_output_dir = self.output_dir / "raw_data" / condition
                
                self.logger.info(f"Processing condition: {condition}")
                self.logger.info(f"Input directory: {condition_input_dir}")
                self.logger.info(f"Output directory: {condition_output_dir}")
                
                if not condition_input_dir.exists():
                    self.logger.warning(f"Condition directory not found: {condition_input_dir}")
                    continue
                
                # Create condition directory in output
                condition_output_dir.mkdir(parents=True, exist_ok=True)
                
                # Check what's in the condition directory
                condition_items = list(condition_input_dir.iterdir())
                self.logger.info(f"Items in condition directory: {[item.name for item in condition_items]}")
                
                # Copy files based on selections
                if selected_timepoints and directory_timepoints:
                    # Copy specific timepoints - map filename timepoints to directory timepoints
                    for timepoint in selected_timepoints:
                        timepoint_number = timepoint.replace('t', '')
                        directory_timepoint = f"timepoint_{int(timepoint_number) + 1}"
                        
                        if directory_timepoint in directory_timepoints:
                            timepoint_input_dir = condition_input_dir / directory_timepoint
                            timepoint_output_dir = condition_output_dir / directory_timepoint
                            
                            self.logger.info(f"Mapping {timepoint} to directory {directory_timepoint}")
                            self.logger.info(f"Timepoint input directory: {timepoint_input_dir}")
                            
                            if timepoint_input_dir.exists():
                                timepoint_output_dir.mkdir(parents=True, exist_ok=True)
                                
                                # Copy TIF files from this timepoint
                                tif_files = list(timepoint_input_dir.glob("*.tif"))
                                self.logger.info(f"Found {len(tif_files)} TIF files in {directory_timepoint}")
                                
                                copied_in_timepoint = 0
                                for tif_file in tif_files:
                                    # Check if this file matches selected regions (if specified)
                                    if selected_regions:
                                        filename = tif_file.stem
                                        if not any(region in filename for region in selected_regions):
                                            self.logger.debug(f"Skipping file {filename} - doesn't match selected regions")
                                            continue
                                    
                                    # Copy the file
                                    output_file = timepoint_output_dir / tif_file.name
                                    fs_port = getattr(self, '_fs', None)
                                    if fs_port is not None:
                                        fs_port.copy(tif_file, output_file, overwrite=True)
                                    else:
                                        from percell.adapters.local_filesystem_adapter import LocalFileSystemAdapter
                                        LocalFileSystemAdapter().copy(tif_file, output_file, overwrite=True)
                                    total_copied += 1
                                    copied_in_timepoint += 1
                                    self.logger.debug(f"Copied: {tif_file.name}")
                                    
                                self.logger.info(f"Copied {copied_in_timepoint} files from {condition}/{directory_timepoint}")
                            else:
                                self.logger.warning(f"Timepoint directory not found: {timepoint_input_dir}")
                        else:
                            self.logger.warning(f"No directory timepoint found for {timepoint}")
                else:
                    # Copy all TIF files from condition directory
                    tif_files = list(condition_input_dir.glob("*.tif"))
                    self.logger.info(f"Found {len(tif_files)} TIF files directly in condition directory")
                    
                    copied_in_condition = 0
                    for tif_file in tif_files:
                        # Check if this file matches selected regions (if specified)
                        if selected_regions:
                            filename = tif_file.stem
                            if not any(region in filename for region in selected_regions):
                                self.logger.debug(f"Skipping file {filename} - doesn't match selected regions")
                                continue
                        
                        # Copy the file
                        output_file = condition_output_dir / tif_file.name
                        fs_port = getattr(self, '_fs', None)
                        if fs_port is not None:
                            fs_port.copy(tif_file, output_file, overwrite=True)
                        else:
                            from percell.adapters.local_filesystem_adapter import LocalFileSystemAdapter
                            LocalFileSystemAdapter().copy(tif_file, output_file, overwrite=True)
                        total_copied += 1
                        copied_in_condition += 1
                        self.logger.debug(f"Copied: {tif_file.name}")
                    
                    self.logger.info(f"Copied {copied_in_condition} files from {condition}")
            
            self.logger.info(f"File copy completed. Total files copied: {total_copied}")
            
            # Check if any files were actually copied
            if total_copied == 0:
                self.logger.error("No files were copied. This indicates a problem with file selection or copying.")
                self.logger.error("Please check that:")
                self.logger.error("1. The selected conditions, timepoints, and regions exist in the input directory")
                self.logger.error("2. The files match the expected naming patterns")
                self.logger.error("3. The file extensions are correct (.tif)")
                return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error copying selected files: {e}")
            return False
    
    def _prepare_input_structure(self, input_dir: str) -> bool:
        """Prepare input directory structure using the prepare_input_structure.sh script."""
        try:
            input_path = Path(input_dir)
            self.logger.info(f"Starting input directory structure preparation: {input_path}")
            
            # Use the prepare_input_structure.sh script
            from percell.application.paths_api import get_path, ensure_executable
            script_path = get_path("prepare_input_structure_script")
            
            # Make sure the script is executable (prefer injected filesystem port)
            fs_port = getattr(self, '_fs', None)
            try:
                if fs_port is not None:
                    from percell.application.paths_api import get_path
                    fs_port.ensure_executable(get_path("prepare_input_structure_script"))
                else:
                    from percell.adapters.local_filesystem_adapter import LocalFileSystemAdapter
                    from percell.application.paths_api import get_path
                    LocalFileSystemAdapter().ensure_executable(get_path("prepare_input_structure_script"))
            except Exception:
                pass
            
            self.logger.info(f"Running prepare_input_structure.sh with input: {input_path}")
            
            # Run the script
            result = subprocess.run([str(script_path), str(input_path)], 
                                  capture_output=True, text=True)
            
            if result.returncode != 0:
                self.logger.error(f"prepare_input_structure.sh failed: {result.stderr}")
                return False
            
            self.logger.info("Input directory structure prepared successfully")
            self.logger.info(f"Script output: {result.stdout}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error preparing input structure: {e}")
            return False
    
    def _process_timepoint_directory(self, timepoint_dir: Path):
        """Process files in a timepoint directory."""
        self.logger.info(f"Processing files in: {timepoint_dir}")
        region_counter = 1
        
        for tif_file in timepoint_dir.glob("*.tif"):
            if tif_file.is_file():
                filename = tif_file.name
                
                # Check if missing timepoint pattern
                if not self._has_timepoint_pattern(filename):
                    self.logger.warning(f"File missing timepoint pattern: {filename}")
                    new_filename = filename.replace('.tif', '_t00.tif')
                    self.logger.info(f"Adding timepoint pattern: {new_filename}")
                    new_path = timepoint_dir / new_filename
                    tif_file.rename(new_path)
                    tif_file = new_path
                    filename = new_filename
                
                # Check if missing channel pattern
                if not self._has_channel_pattern(filename):
                    self.logger.warning(f"File missing channel pattern: {filename}")
                    new_filename = filename.replace('.tif', '_ch00.tif')
                    self.logger.info(f"Adding channel pattern: {new_filename}")
                    new_path = timepoint_dir / new_filename
                    tif_file.rename(new_path)
                
                # Each file is considered its own region
                self.logger.info(f"File will be treated as Region {region_counter}: {filename}")
                region_counter += 1
    
    def _has_timepoint_pattern(self, filename: str) -> bool:
        """Check if a filename contains a timepoint pattern (tXX)."""
        return bool(re.search(r't[0-9]+', filename))
    
    def _has_channel_pattern(self, filename: str) -> bool:
        """Check if a filename contains a channel pattern (chXX)."""
        return bool(re.search(r'ch[0-9]+', filename))
    
    def _extract_experiment_metadata(self, input_dir: str) -> bool:
        """Extract experiment metadata from the directory structure."""
        try:
            input_path = Path(input_dir)
            metadata = {
                'conditions': [],
                'regions': set(),
                'timepoints': set(),
                'channels': set(),
                'region_to_channels': {},
                'datatype_inferred': 'multi_timepoint',
                'directory_timepoints': set()
            }
            
            self.logger.info(f"Scanning input directory: {input_path}")
            if not input_path.exists():
                self.logger.error(f"Input directory does not exist: {input_path}")
                return False
                
            # Discover conditions from top-level directories
            input_items = list(input_path.glob("*"))
            input_dirs = [item for item in input_items if item.is_dir() and not item.name.startswith('.')]
            if not input_dirs:
                self.logger.warning("No subdirectories found in input directory. Expected at least one condition directory.")
                return False
            metadata['conditions'].extend([d.name for d in input_dirs])

            # Track directory-based timepoints for copy step
            for d in input_dirs:
                for sub in d.iterdir():
                    if sub.is_dir():
                        name = sub.name
                        if name.startswith('timepoint_') or re.match(r't[0-9]+', name):
                            metadata['directory_timepoints'].add(name)

            # Use adapter-provided file list when available to avoid domain IO
            try:
                if getattr(self, '_fs', None) is not None:
                    files = self._fs.list_files(input_path, ["*.tif", "*.tiff"])  # type: ignore[attr-defined]
                else:
                    files = self._selection_service.scan_available_data(input_path)
            except Exception:
                files = self._selection_service.scan_available_data(input_path)
            self.logger.info(f"Found {len(files)} microscopy files under input directory")
            _conditions, timepoints, regions = self._selection_service.parse_conditions_timepoints_regions(files)
            for tp in timepoints:
                metadata['timepoints'].add(tp)
            for rg in regions:
                metadata['regions'].add(rg)

            # Extract channels via domain file naming service
            for f in files[:100]:
                try:
                    meta = self._naming_service.parse_microscopy_filename(f.name)
                    if meta.channel:
                        metadata['channels'].add(meta.channel)
                except Exception:
                    continue
            
            # Convert sets to sorted lists
            metadata['regions'] = sorted(list(metadata['regions']))
            metadata['timepoints'] = sorted(list(metadata['timepoints']))
            metadata['channels'] = sorted(list(metadata['channels']))
            metadata['directory_timepoints'] = sorted(list(metadata['directory_timepoints']))
            
            # Infer datatype based on timepoints
            if len(metadata['timepoints']) <= 1:
                metadata['datatype_inferred'] = 'single_timepoint'
            else:
                metadata['datatype_inferred'] = 'multi_timepoint'
            
            self.experiment_metadata = metadata
            self.logger.info(f"Extracted metadata: {metadata}")
            self.logger.info(f"Directory timepoints (for file copying): {metadata['directory_timepoints']}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error extracting experiment metadata: {e}")
            return False
    
    def _run_interactive_selection(self) -> bool:
        """Run interactive selection prompts."""
        try:
            # Step 1: Select datatype
            if not self._select_datatype():
                return False
            
            # Step 2: Select conditions
            if not self._select_conditions():
                return False
            
            # Step 3: Select timepoints
            if not self._select_timepoints():
                return False
            
            # Step 4: Select regions
            if not self._select_regions():
                return False
            
            # Step 5: Select segmentation channel
            if not self._select_segmentation_channel():
                return False
            
            # Step 6: Select analysis channels
            if not self._select_analysis_channels():
                return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error in interactive selection: {e}")
            return False
    
    def _select_datatype(self) -> bool:
        """Interactive datatype selection."""
        print("\n" + "="*80)
        print("MANUAL STEP REQUIRED: select_datatype")
        print("="*80)
        print("Select the type of data: single_timepoint or multi_timepoint. You can specify the datatype when running the script with the --datatype option.")
        
        available_datatypes = ["single_timepoint", "multi_timepoint"]
        inferred_datatype = self.experiment_metadata.get('datatype_inferred', 'multi_timepoint')
        print(f"\nDetected datatype based on found timepoints: {inferred_datatype}")
        print("Select data type:")
        for i, dt in enumerate(available_datatypes, 1):
            print(f"{i}. {dt}")
        
        user_input = input("Enter selection (number or name, press Enter for detected default): ").strip().lower()
        
        if not user_input:
            self.selected_datatype = inferred_datatype
        elif user_input.isdigit() and 1 <= int(user_input) <= len(available_datatypes):
            self.selected_datatype = available_datatypes[int(user_input) - 1]
        elif user_input in available_datatypes:
            self.selected_datatype = user_input
        else:
            self.logger.warning(f"Invalid datatype selection '{user_input}'. Using detected default: {inferred_datatype}")
            self.selected_datatype = inferred_datatype
            
        self.logger.info(f"Selected datatype: {self.selected_datatype}")
        return True
    
    def _select_conditions(self) -> bool:
        """Interactive condition selection."""
        print("\n" + "="*80)
        print("MANUAL STEP REQUIRED: select_condition")
        print("="*80)
        conditions_list = ', '.join(self.experiment_metadata['conditions'])
        print(f"Review available conditions: {conditions_list}. Select the conditions to analyze. You can specify conditions when running the script with the --conditions option.")
        
        available_items = self.experiment_metadata['conditions']
        self.selected_conditions = self._handle_list_selection(available_items, "conditions", self.selected_conditions)
        
        return True
    
    def _select_timepoints(self) -> bool:
        """Interactive timepoint selection."""
        print("\n" + "="*80)
        print("MANUAL STEP REQUIRED: select_timepoints")
        print("="*80)
        timepoints_list = ', '.join(self.experiment_metadata.get('timepoints', []))
        print(f"Review available timepoints in the raw data and decide which timepoints to use for analysis. Current experiment has timepoints: {timepoints_list}. Press Enter when you have made your selection. You can specify timepoints when running the script with --timepoints option.")
        
        available_items = self.experiment_metadata['timepoints']
        self.selected_timepoints = self._handle_list_selection(available_items, "timepoints", self.selected_timepoints)
        
        return True
    
    def _select_regions(self) -> bool:
        """Interactive region selection."""
        print("\n" + "="*80)
        print("MANUAL STEP REQUIRED: select_regions")
        print("="*80)
        regions_list = ', '.join(self.experiment_metadata.get('regions', []))
        print(f"Review available regions in the raw data and decide which regions to use for analysis. Current experiment has regions: {regions_list}. Press Enter when you have made your selection. You can specify regions when running the script with --regions option.")
        
        # Only show regions that exist in the selected conditions
        if not self.selected_conditions:
            self.logger.warning("No conditions selected. Please select conditions first.")
            return False
        
        # Filter regions based on the selected conditions using domain service
        available_regions_by_condition = {}
        for condition in self.selected_conditions:
            input_dir = getattr(self, 'input_dir', None)
            if not input_dir:
                available_items = self.experiment_metadata.get('regions', [])
                self.selected_regions = self._handle_list_selection(available_items, "regions", self.selected_regions)
                return True
            condition_dir = Path(input_dir) / condition
            if condition_dir.exists():
                files = list(condition_dir.glob("**/*.tif"))
                _conds, _t, regions = self._selection_service.parse_conditions_timepoints_regions(files)
                available_regions_by_condition[condition] = sorted(list(regions))
            else:
                self.logger.warning(f"Selected condition '{condition}' directory not found")
                available_regions_by_condition[condition] = []
        
        # Log the regions available in each condition
        for condition, regions in available_regions_by_condition.items():
            self.logger.info(f"Regions available in condition '{condition}': {regions}")
        
        # Check if all conditions have the same regions
        first_condition = self.selected_conditions[0]
        first_regions = set(available_regions_by_condition.get(first_condition, []))
        same_regions_across_conditions = True
        
        for condition in self.selected_conditions[1:]:
            other_regions = set(available_regions_by_condition.get(condition, []))
            if first_regions != other_regions:
                same_regions_across_conditions = False
                break
        
        if not same_regions_across_conditions:
            self.logger.error("Selected conditions have different available regions:")
            for condition, regions in available_regions_by_condition.items():
                self.logger.error(f"  '{condition}': {regions}")
            self.logger.error("The workflow cannot proceed with inconsistent regions across conditions.")
            print("\nERROR: Selected conditions have different available regions.")
            print("Please select conditions with the same regions or modify your data structure.")
            print("Press Enter to exit...")
            input()
            return False
            
        # All conditions have the same regions, so we can use the first one's regions list
        available_items = available_regions_by_condition.get(self.selected_conditions[0], [])
        self.logger.info(f"Available regions for selected conditions: {available_items}")
        
        if not available_items:
            self.logger.error("No regions found for the selected conditions")
            print("\nERROR: No regions found for the selected conditions.")
            print("Press Enter to exit...")
            input()
            return False
            
        self.selected_regions = self._handle_list_selection(available_items, "regions", self.selected_regions)
        return True
    
    def _select_segmentation_channel(self) -> bool:
        """Interactive segmentation channel selection."""
        print("\n" + "="*80)
        print("MANUAL STEP REQUIRED: select_segmentation_channel")
        print("="*80)
        channels_list = ', '.join(self.experiment_metadata['channels'])
        print(f"Select the channel to use for cell segmentation. This channel will be used for binning images and interactive segmentation. Available channels: {channels_list}")
        
        available_items = self.experiment_metadata['channels']
        selected_channels = self._handle_list_selection(available_items, "segmentation channel", [])
        if selected_channels:
            self.segmentation_channel = selected_channels[0]  # Take first selection only
        return True
    
    def _select_analysis_channels(self) -> bool:
        """Interactive analysis channel selection."""
        print("\n" + "="*80)
        print("MANUAL STEP REQUIRED: select_analysis_channels")
        print("="*80)
        channels_list = ', '.join(self.experiment_metadata['channels'])
        print(f"Select the channels to analyze. These channels will be used for all downstream analysis steps. Available channels: {channels_list}")
        
        available_items = self.experiment_metadata['channels']
        self.analysis_channels = self._handle_list_selection(available_items, "analysis channel", self.analysis_channels)
        return True
    
    def _handle_list_selection(self, available_items: List[str], item_type: str, target_list: List[str]) -> List[str]:
        """Handle selection of items from a list with interactive CLI."""
        if not available_items:
            self.logger.warning(f"No {item_type}s available for selection")
            return []
            
        print(f"\nAvailable {item_type}ss:")
        for i, item in enumerate(available_items, 1):
            print(f"{i}. {item}")
            
        print(f"\nInput options for {item_type}ss:")
        print(f"- Enter {item_type}ss as space-separated text (e.g., '{available_items[0]} {available_items[-1] if len(available_items) > 1 else available_items[0]}')")
        print(f"- Enter numbers from the list (e.g., '1 {len(available_items)}')")
        print(f"- Type 'all' to select all {item_type}ss")
        
        while True:
            selection = input(f"\nEnter your selection: ").strip()
            
            if selection.lower() == 'all':
                return available_items
                
            # Try to parse as numbers first
            try:
                indices = [int(x) for x in selection.split()]
                if all(1 <= i <= len(available_items) for i in indices):
                    return [available_items[i-1] for i in indices]
            except ValueError:
                pass
                
            # If not numbers, treat as direct item names
            selected_items = [item.strip() for item in selection.split()]
            if all(item in available_items for item in selected_items):
                return selected_items
                
            print(f"Invalid selection. Please try again.")
    
    def _save_selections_to_config(self):
        """Save the selected parameters to the configuration."""
        try:
            # Update the config with selected parameters using the Config.set method
            self.config.set('data_selection.selected_datatype', self.selected_datatype)
            self.config.set('data_selection.selected_conditions', self.selected_conditions)
            self.config.set('data_selection.selected_timepoints', self.selected_timepoints)
            self.config.set('data_selection.selected_regions', self.selected_regions)
            self.config.set('data_selection.segmentation_channel', self.segmentation_channel)
            self.config.set('data_selection.analysis_channels', self.analysis_channels)
            self.config.set('data_selection.experiment_metadata', self.experiment_metadata)
            
            # Save the updated config
            self.config.save()
            
            self.logger.info("Data selections saved to configuration")
            
        except Exception as e:
            self.logger.error(f"Error saving selections to config: {e}")


