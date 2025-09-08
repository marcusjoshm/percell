#!/usr/bin/env python3
"""
Stage Classes for Microscopy Single-Cell Analysis Pipeline

Contains the concrete implementations of each pipeline stage.
"""

import subprocess
from percell.application.progress_api import run_subprocess_with_spinner
import os
import re
import sys
import shutil
from pathlib import Path
from typing import Dict, Any, List, Set, Optional
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
            
            # Step 6: Copy selected files to output
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
            
            # Make sure the script is executable
            from percell.adapters.local_filesystem_adapter import LocalFileSystemAdapter
            from percell.application.paths_api import get_path
            LocalFileSystemAdapter().ensure_executable(get_path("setup_output_structure_script"))
            
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
                        # Find corresponding directory timepoint
                        # For now, assume t00 maps to timepoint_1, t01 to timepoint_2, etc.
                        # This can be made more sophisticated if needed
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
            
            # Make sure the script is executable
            from percell.adapters.local_filesystem_adapter import LocalFileSystemAdapter
            from percell.application.paths_api import get_path
            LocalFileSystemAdapter().ensure_executable(get_path("prepare_input_structure_script"))
            
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

            # Use domain service to scan and parse filenames globally
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


class SegmentationStage(StageBase):
    """
    Single-cell Segmentation Stage
    
    Handles image binning and interactive segmentation using Cellpose.
    Includes: bin_images_for_segmentation, interactive_segmentation
    """
    
    def __init__(self, config, logger, stage_name="segmentation"):
        super().__init__(config, logger, stage_name)
        
    def validate_inputs(self, **kwargs) -> bool:
        """Validate inputs for segmentation stage."""
        # Check if required scripts exist
        from percell.application.paths_api import path_exists
        required_scripts = [
            ("bin_images_module", "Python module"),
            ("launch_segmentation_tools_script", "Bash script")
        ]
        for script_name, script_type in required_scripts:
            if not path_exists(script_name):
                self.logger.error(f"Required {script_type} not found: {script_name}")
                return False
        
        # Check if data selection has been completed
        data_selection = self.config.get('data_selection')
        if not data_selection:
            self.logger.error("Data selection has not been completed. Please run data selection first.")
            return False
        
        # Check if required data selection parameters are available
        required_params = ['selected_conditions', 'selected_regions', 'selected_timepoints', 'segmentation_channel']
        missing_params = [param for param in required_params if not data_selection.get(param)]
        if missing_params:
            self.logger.error(f"Missing data selection parameters: {missing_params}")
            return False
        
        return True
    
    def run(self, **kwargs) -> bool:
        """Run the segmentation stage."""
        try:
            self.logger.info("Starting Single-cell Segmentation Stage")
            
            # Get data selection parameters from config
            data_selection = self.config.get('data_selection')
            if not data_selection:
                self.logger.error("No data selection information found in config")
                return False
            
            # Get input and output directories
            input_dir = kwargs.get('input_dir')
            output_dir = kwargs.get('output_dir')
            
            if not input_dir or not output_dir:
                self.logger.error("Input and output directories are required")
                return False
            
            # Step 1: Bin images for segmentation
            self.logger.info("Binning images for segmentation...")
            from percell.application.paths_api import get_path, ensure_executable
            bin_script = get_path("bin_images_module")
            bin_args = [
                "--input", f"{output_dir}/raw_data",
                "--output", f"{output_dir}/preprocessed",
                "--verbose"
            ]
            
            # Add data selection parameters
            if data_selection.get('selected_conditions'):
                bin_args.extend(["--conditions"] + data_selection['selected_conditions'])
            if data_selection.get('selected_regions'):
                bin_args.extend(["--regions"] + data_selection['selected_regions'])
            if data_selection.get('selected_timepoints'):
                bin_args.extend(["--timepoints"] + data_selection['selected_timepoints'])
            if data_selection.get('segmentation_channel'):
                bin_args.extend(["--channels", data_selection['segmentation_channel']])
            
            self.logger.info(f"Running bin_images.py with args: {bin_args}")
            result = run_subprocess_with_spinner([sys.executable, str(bin_script)] + bin_args, title="Binning images")
            if result.returncode != 0:
                self.logger.error(f"Failed to bin images: {result.stderr}")
                return False
            self.logger.info("Images binned successfully")
            self.logger.info(f"Bin script output: {result.stdout}")
            
            # Step 2: Launch segmentation (interactive Cellpose GUI only)
            preprocessed_dir = f"{output_dir}/preprocessed"
            cellpose_python = self.config.get('cellpose_path')
            if cellpose_python:
                from percell.adapters.cellpose_subprocess_adapter import CellposeSubprocessAdapter
                from percell.domain.models import SegmentationParameters
                adapter = CellposeSubprocessAdapter(Path(cellpose_python))
                self.logger.info("Launching Cellpose GUI (python -m cellpose) — no directories passed")
                # Launch GUI and wait for user to complete segmentation, then close
                from pathlib import Path as _P
                adapter.run_segmentation([], _P(f"{output_dir}/combined_masks"), SegmentationParameters(0, 0, 0, "nuclei"))
                self.logger.info("Cellpose GUI closed by user")
            else:
                # Fallback to interactive tools script
                self.logger.info("Launching interactive segmentation tools...")
                seg_script_path = get_path("launch_segmentation_tools_script")
                # Make sure the script is executable
                from percell.adapters.local_filesystem_adapter import LocalFileSystemAdapter
                from percell.application.paths_api import get_path
                LocalFileSystemAdapter().ensure_executable(get_path("launch_segmentation_tools_script"))
                self.logger.info("Starting interactive segmentation session...")
                self.logger.info("The script will open Cellpose and ImageJ for manual segmentation.")
                self.logger.info("Please complete your segmentation work and press Enter when done.")
                result = subprocess.run([str(seg_script_path), preprocessed_dir], 
                                      stdin=sys.stdin, stdout=sys.stdout, stderr=sys.stderr)
                if result.returncode != 0:
                    self.logger.error(f"Failed to launch segmentation tools: {result.returncode}")
                    return False
                self.logger.info("Segmentation tools completed successfully")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error in Segmentation Stage: {e}")
            return False


class ProcessSingleCellDataStage(StageBase):
    """
    Process Single-cell Data Stage
    
    Handles ROI tracking, resizing, duplication, cell extraction, and cell grouping.
    Includes: roi_tracking, resize_rois, duplicate_rois_for_analysis_channels, extract_cells, group_cells
    """
    
    def __init__(self, config, logger, stage_name="process_single_cell"):
        super().__init__(config, logger, stage_name)
        
    def validate_inputs(self, **kwargs) -> bool:
        """Validate inputs for process single-cell data stage."""
        # Check if required scripts exist
        from percell.application.paths_api import path_exists
        required_scripts = [
            "track_rois_module",
            "duplicate_rois_for_channels_module",
            "extract_cells_module",
            "group_cells_module"
        ]
        for script_name in required_scripts:
            if not path_exists(script_name):
                self.logger.error(f"Required script not found: {script_name}")
                return False
        
        # Check if data selection has been completed
        data_selection = self.config.get('data_selection')
        if not data_selection:
            self.logger.error("Data selection has not been completed. Please run data selection first.")
            return False
        
        # Check if required data selection parameters are available
        required_params = ['selected_conditions', 'selected_regions', 'selected_timepoints', 'segmentation_channel', 'analysis_channels']
        missing_params = [param for param in required_params if not data_selection.get(param)]
        if missing_params:
            self.logger.error(f"Missing data selection parameters: {missing_params}")
            return False
        
        return True
    
    def run(self, **kwargs) -> bool:
        """Run the process single-cell data stage."""
        try:
            self.logger.info("Starting Process Single-cell Data Stage")
            
            # Get data selection parameters from config
            data_selection = self.config.get('data_selection')
            if not data_selection:
                self.logger.error("No data selection information found in config")
                return False
            
            # Get input and output directories
            input_dir = kwargs.get('input_dir')
            output_dir = kwargs.get('output_dir')
            
            if not input_dir or not output_dir:
                self.logger.error("Input and output directories are required")
                return False
            
            # Step 1: ROI tracking (if multiple timepoints)
            timepoints = data_selection.get('selected_timepoints', [])
            if timepoints and len(timepoints) > 1:
                self.logger.info("Tracking ROIs across timepoints...")
                from percell.application.paths_api import get_path
                track_script = get_path("track_rois_module")
                track_args = [
                    "--input", f"{output_dir}/preprocessed",
                    "--timepoints"
                ] + timepoints + ["--recursive"]
                
                result = run_subprocess_with_spinner([sys.executable, str(track_script)] + track_args, title="Tracking ROIs")
                if result.returncode != 0:
                    self.logger.error(f"Failed to track ROIs: {result.stderr}")
                    return False
                self.logger.info("ROI tracking completed successfully")
            else:
                self.logger.info("Skipping ROI tracking (single timepoint or no timepoints)")
            
            # Step 2: Resize ROIs (migrated from module to application helper)
            self.logger.info("Resizing ROIs...")
            from percell.application.paths_api import get_path, get_path_str
            from percell.application.imagej_tasks import resize_rois as _resize_rois
            ok_resize = _resize_rois(
                input_dir=f"{output_dir}/preprocessed",
                output_dir=f"{output_dir}/ROIs",
                imagej_path=self.config.get('imagej_path'),
                channel=data_selection.get('segmentation_channel', ''),
                macro_path=get_path_str("resize_rois_macro"),
                auto_close=True,
            )
            if not ok_resize:
                self.logger.error("Failed to resize ROIs")
                return False
            self.logger.info("ROIs resized successfully")
            
            # Step 3: Duplicate ROIs for analysis channels
            self.logger.info("Duplicating ROIs for analysis channels...")
            duplicate_script = get_path("duplicate_rois_for_channels_module")
            duplicate_args = [
                "--roi-dir", f"{output_dir}/ROIs",
                "--channels"
            ] + data_selection.get('analysis_channels', []) + ["--verbose"]
            
            result = run_subprocess_with_spinner([sys.executable, str(duplicate_script)] + duplicate_args, title="Duplicating ROIs")
            if result.returncode != 0:
                self.logger.error(f"Failed to duplicate ROIs: {result.stderr}")
                return False
            self.logger.info("ROIs duplicated successfully")
            
            # Step 4: Extract cells
            self.logger.info("Extracting cells...")
            extract_script = get_path("extract_cells_module")
            extract_args = [
                "--roi-dir", f"{output_dir}/ROIs",
                "--raw-data-dir", f"{output_dir}/raw_data",
                "--output-dir", f"{output_dir}/cells",
                "--imagej", self.config.get('imagej_path'),
                "--macro", get_path_str("extract_cells_macro"),
                "--auto-close",
                "--channels"
            ] + data_selection.get('analysis_channels', [])
            
            result = run_subprocess_with_spinner([sys.executable, str(extract_script)] + extract_args, title="Extracting cells")
            if result.returncode != 0:
                self.logger.error(f"Failed to extract cells: {result.stderr}")
                return False
            self.logger.info("Cells extracted successfully")
            
            # Step 5: Group cells
            self.logger.info("Grouping cells...")
            group_script = get_path("group_cells_module")
            group_args = [
                "--cells-dir", f"{output_dir}/cells",
                "--output-dir", f"{output_dir}/grouped_cells",
                "--bins", str(kwargs.get('bins', 5)),
                "--force-clusters",
                "--channels"
            ] + data_selection.get('analysis_channels', [])
            
            result = run_subprocess_with_spinner([sys.executable, str(group_script)] + group_args, title="Grouping cells")
            if result.returncode != 0:
                self.logger.error(f"Failed to group cells: {result.stderr}")
                return False
            self.logger.info("Cells grouped successfully")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error in Process Single-cell Data Stage: {e}")
            return False


class ThresholdGroupedCellsStage(StageBase):
    """
    Threshold Grouped Cells Stage
    
    Handles thresholding of grouped cells.
    Includes: threshold_grouped_cells
    """
    
    def __init__(self, config, logger, stage_name="threshold_grouped_cells"):
        super().__init__(config, logger, stage_name)
        
    def validate_inputs(self, **kwargs) -> bool:
        """Validate inputs for threshold grouped cells stage."""
        # Check if required scripts exist
        from percell.application.paths_api import path_exists
        required_scripts = ["otsu_threshold_grouped_cells_module"]
        for script_name in required_scripts:
            if not path_exists(script_name):
                self.logger.error(f"Required script not found: {script_name}")
                return False
        
        # Check if data selection has been completed
        data_selection = self.config.get('data_selection')
        if not data_selection:
            self.logger.error("Data selection has not been completed. Please run data selection first.")
            return False
        
        # Check if required data selection parameters are available
        required_params = ['analysis_channels']
        missing_params = [param for param in required_params if not data_selection.get(param)]
        if missing_params:
            self.logger.error(f"Missing data selection parameters: {missing_params}")
            return False
        
        return True
    
    def run(self, **kwargs) -> bool:
        """Run the threshold grouped cells stage."""
        try:
            self.logger.info("Starting Threshold Grouped Cells Stage")
            
            # Get data selection parameters from config
            data_selection = self.config.get('data_selection')
            if not data_selection:
                self.logger.error("No data selection information found in config")
                return False
            
            # Get output directory
            output_dir = kwargs.get('output_dir')
            if not output_dir:
                self.logger.error("Output directory is required")
                return False
            
            # Threshold grouped cells
            self.logger.info("Thresholding grouped cells...")
            from percell.application.paths_api import get_path, get_path_str
            threshold_script = get_path("otsu_threshold_grouped_cells_module")
            threshold_args = [
                "--input-dir", f"{output_dir}/grouped_cells",
                "--output-dir", f"{output_dir}/grouped_masks",
                "--imagej", self.config.get('imagej_path'),
                "--macro", get_path_str("threshold_grouped_cells_macro"),
                "--channels"
            ]
            # Add analysis channels as separate arguments (matching original workflow)
            for channel in data_selection.get('analysis_channels', []):
                threshold_args.append(channel)
            
            # Run without spinner for thresholding step
            result = subprocess.run([sys.executable, str(threshold_script)] + threshold_args, capture_output=True, text=True)
            if result.returncode != 0:
                self.logger.error(f"Failed to threshold grouped cells: {result.stderr}")
                return False
            self.logger.info("Grouped cells thresholded successfully")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error in Threshold Grouped Cells Stage: {e}")
            return False


class MeasureROIAreaStage(StageBase):
    """
    Measure ROI Area Stage
    
    Opens ROI lists and corresponding raw data files, then measures ROI areas.
    Results are saved as CSV files in the analysis/cell_area folder.
    """
    
    def __init__(self, config, logger, stage_name="measure_roi_area"):
        super().__init__(config, logger, stage_name)
        
    def validate_inputs(self, **kwargs) -> bool:
        """Validate inputs for measure ROI area stage."""
        # Check if required macro exists
        from percell.application.paths_api import path_exists
        if not path_exists("measure_roi_area_macro"):
            self.logger.error("Required macro not found: measure_roi_area_macro")
            return False
        
        # Check if ImageJ path is configured
        imagej_path = self.config.get('imagej_path')
        if not imagej_path or not Path(imagej_path).exists():
            self.logger.error("ImageJ path not configured or does not exist")
            return False
        
        # Check if input and output directories are provided
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
        """Run the measure ROI area stage."""
        try:
            self.logger.info("Starting Measure ROI Area Stage")
            
            # Get input and output directories
            input_dir = kwargs.get('input_dir')
            output_dir = kwargs.get('output_dir')
            
            if not input_dir or not output_dir:
                self.logger.error("Input and output directories are required")
                return False
            
            # Run via application helper (migrated from module)
            from percell.application.imagej_tasks import measure_roi_areas as _measure_roi_areas
            from percell.application.paths_api import get_path_str

            imagej_path = self.config.get('imagej_path')

            self.logger.info(f"Measuring ROI areas using ImageJ: {imagej_path}")
            self.logger.info(f"Input directory: {input_dir}")
            self.logger.info(f"Output directory: {output_dir}")

            success = _measure_roi_areas(
                input_dir=str(input_dir),
                output_dir=str(output_dir),
                imagej_path=str(imagej_path),
                macro_path=get_path_str("measure_roi_area_macro"),
                auto_close=True,
            )
            
            if success:
                self.logger.info("ROI area measurement completed successfully")
                
                # Check if any CSV files were created in the analysis directory
                analysis_dir = Path(output_dir) / "analysis"
                csv_files = list(analysis_dir.glob("*cell_area*.csv"))
                if csv_files:
                    self.logger.info(f"Created {len(csv_files)} ROI area measurement files")
                    for csv_file in csv_files[:5]:  # Show first 5 files
                        self.logger.info(f"  - {csv_file.name}")
                    if len(csv_files) > 5:
                        self.logger.info(f"  ... and {len(csv_files) - 5} more files")
                else:
                    self.logger.warning("No ROI area measurement files were created")
                    
                return True
            else:
                self.logger.error("Failed to measure ROI areas")
                return False
            
        except Exception as e:
            self.logger.error(f"Error in Measure ROI Area Stage: {e}")
            return False


class AnalysisStage(StageBase):
    """
    Analysis Stage
    
    Handles mask combination, cell mask creation, analysis, and metadata inclusion.
    Includes: combine_masks, create_cell_masks, analyze_cell_masks, include_group_metadata
    """
    
    def __init__(self, config, logger, stage_name="analysis"):
        super().__init__(config, logger, stage_name)
        
    def validate_inputs(self, **kwargs) -> bool:
        """Validate inputs for analysis stage."""
        # Check if required scripts exist
        from percell.application.paths_api import path_exists
        required_scripts = [
            "combine_masks_module",
            "create_cell_masks_module", 
            "include_group_metadata_module"
        ]
        for script_name in required_scripts:
            if not path_exists(script_name):
                self.logger.error(f"Required script not found: {script_name}")
                return False
        # Check required macro for analysis exists
        if not path_exists("analyze_cell_masks_macro"):
            self.logger.error("Required macro not found: analyze_cell_masks_macro")
            return False
        
        # Check if data selection has been completed
        data_selection = self.config.get('data_selection')
        self.logger.debug(f"Data selection from config: {data_selection}")
        if not data_selection:
            self.logger.error("Data selection has not been completed. Please run data selection first.")
            return False
        
        # Check if required data selection parameters are available
        required_params = ['analysis_channels']
        missing_params = [param for param in required_params if not data_selection.get(param)]
        if missing_params:
            self.logger.error(f"Missing data selection parameters: {missing_params}")
            return False
        
        return True
    
    def run(self, **kwargs) -> bool:
        """Run the analysis stage."""
        try:
            self.logger.info("Starting Analysis Stage")
            
            # Get data selection parameters from config
            data_selection = self.config.get('data_selection')
            if not data_selection:
                self.logger.error("No data selection information found in config")
                return False
            
            # Get output directory
            output_dir = kwargs.get('output_dir')
            if not output_dir:
                self.logger.error("Output directory is required")
                return False
            
            # Step 1: Combine masks
            self.logger.info("Combining masks...")
            from percell.application.paths_api import get_path
            combine_script = get_path("combine_masks_module")
            combine_args = [
                "--input-dir", f"{output_dir}/grouped_masks",
                "--output-dir", f"{output_dir}/combined_masks",
                "--channels"
            ]
            # Add analysis channels as separate arguments (matching original workflow)
            for channel in data_selection.get('analysis_channels', []):
                combine_args.append(channel)
            
            result = run_subprocess_with_spinner([sys.executable, str(combine_script)] + combine_args, title="Combining masks")
            if result.returncode != 0:
                self.logger.error(f"Failed to combine masks: {result.stderr}")
                return False
            self.logger.info("Masks combined successfully")
            
            # Step 2: Create cell masks
            self.logger.info("Creating cell masks...")
            from percell.application.paths_api import get_path, get_path_str
            create_masks_script = get_path("create_cell_masks_module")
            create_masks_args = [
                "--roi-dir", f"{output_dir}/ROIs",
                "--mask-dir", f"{output_dir}/combined_masks",
                "--output-dir", f"{output_dir}/masks",
                "--imagej", self.config.get('imagej_path'),
                "--macro", get_path_str("create_cell_masks_macro"),
                "--auto-close",
                "--channels"
            ]
            # Add analysis channels as separate arguments (matching original workflow)
            for channel in data_selection.get('analysis_channels', []):
                create_masks_args.append(channel)
            
            result = run_subprocess_with_spinner([sys.executable, str(create_masks_script)] + create_masks_args, title="Creating cell masks")
            if result.returncode != 0:
                self.logger.error(f"Failed to create cell masks: {result.stderr}")
                return False
            self.logger.info("Cell masks created successfully")
            
            # Step 3: Analyze cell masks (migrated to application helper)
            self.logger.info("Analyzing cell masks...")
            from percell.application.imagej_tasks import analyze_masks as _analyze_masks
            ok_analyze = _analyze_masks(
                input_dir=f"{output_dir}/masks",
                output_dir=f"{output_dir}/analysis",
                imagej_path=self.config.get('imagej_path'),
                macro_path=get_path_str("analyze_cell_masks_macro"),
                regions=data_selection.get('selected_regions'),
                timepoints=data_selection.get('selected_timepoints'),
                max_files=50,
                auto_close=True,
            )
            if not ok_analyze:
                self.logger.error("Failed to analyze cell masks")
                return False
            self.logger.info("Cell masks analyzed successfully")
            
            # Step 4: Include group metadata
            self.logger.info("Including group metadata...")
            metadata_script = get_path("include_group_metadata_module")
            metadata_args = [
                "--grouped-cells-dir", f"{output_dir}/grouped_cells",
                "--analysis-dir", f"{output_dir}/analysis",
                "--output-dir", f"{output_dir}/analysis",
                "--overwrite",
                "--replace",
                "--verbose",
                "--channels"
            ]
            # Add analysis channels as separate arguments (matching original workflow)
            for channel in data_selection.get('analysis_channels', []):
                metadata_args.append(channel)
            
            result = run_subprocess_with_spinner([sys.executable, str(metadata_script)] + metadata_args, title="Including group metadata")
            if result.returncode != 0:
                self.logger.error(f"Failed to include group metadata: {result.stderr}")
                return False
            self.logger.info("Group metadata included successfully")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error in Analysis Stage: {e}")
            return False


class CleanupStage(StageBase):
    """
    Cleanup Stage
    
    Empties cells, masks, and related directories to free up disk space.
    Preserves directory structure while removing contents.
    """
    
    def __init__(self, config, logger, stage_name="cleanup"):
        super().__init__(config, logger, stage_name)
        self.cleanup_directories = [
            'cells',
            'masks'
        ]
        
    def validate_inputs(self, **kwargs) -> bool:
        """Validate inputs for cleanup stage."""
        output_dir = kwargs.get('output_dir')
        if not output_dir:
            self.logger.error("Output directory is required for cleanup")
            return False
        if not Path(output_dir).exists():
            self.logger.error(f"Output directory does not exist: {output_dir}")
            return False
        return True
    
    def run(self, **kwargs) -> bool:
        """Run the cleanup stage."""
        try:
            self.logger.info("Starting Cleanup Stage")
            
            output_dir = Path(kwargs['output_dir'])
            
            # Import cleanup functionality
            try:
                from .cleanup_directories import cleanup_directories, scan_cleanup_directories
            except ImportError as e:
                self.logger.error(f"Could not import cleanup_directories module: {e}")
                return False
            
            # Scan directories to see what can be cleaned up
            self.logger.info("Scanning directories for cleanup...")
            directories_info = scan_cleanup_directories(
                str(output_dir),
                include_cells=True,
                include_masks=True,
                include_combined_masks=False,
                include_grouped_cells=False,
                include_grouped_masks=False
            )
            
            # Check if any directories have content
            total_size = sum(info['size_bytes'] for info in directories_info.values() if info['exists'])
            
            if total_size == 0:
                self.logger.info("No directories found with content to clean up.")
                return True
            
            # Show what will be cleaned up
            self.logger.info("=" * 80)
            self.logger.info("Directories available for cleanup:")
            self.logger.info("-" * 80)
            
            for dir_name, info in directories_info.items():
                if info['exists']:
                    self.logger.info(f"  • {dir_name:<20} {info['size_formatted']:>15}")
            
            self.logger.info("-" * 80)
            self.logger.info(f"  Total space to free: {sum(info['size_bytes'] for info in directories_info.values() if info['exists']):>15} bytes")
            self.logger.info("=" * 80)
            
            # Perform cleanup
            self.logger.info("Performing cleanup...")
            deleted_count, freed_bytes = cleanup_directories(
                str(output_dir),
                delete_cells=True,
                delete_masks=True,
                delete_combined_masks=False,
                delete_grouped_cells=False,
                delete_grouped_masks=False,
                dry_run=False,
                force=True  # Force cleanup in pipeline mode
            )
            
            self.logger.info(f"Cleanup completed successfully!")
            self.logger.info(f"  • Directories emptied: {deleted_count}")
            self.logger.info(f"  • Total space freed: {freed_bytes} bytes")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error in Cleanup Stage: {e}")
            return False


class CompleteWorkflowStage(StageBase):
    """
    Complete Workflow Stage
    
    Executes all pipeline stages in sequence: data selection, segmentation,
    process single-cell data, threshold grouped cells, measure ROI areas, analysis.
    """
    
    def __init__(self, config, logger, stage_name="complete_workflow"):
        super().__init__(config, logger, stage_name)
        self.stages = [
            ('data_selection', 'Data Selection'),
            ('segmentation', 'Single-cell Segmentation'),
            ('process_single_cell', 'Process Single-cell Data'),
            ('threshold_grouped_cells', 'Threshold Grouped Cells'),
            ('measure_roi_area', 'Measure ROI Areas'),
            ('analysis', 'Analysis')
        ]
        self._orchestration = WorkflowOrchestrationService()
    
    def validate_inputs(self, **kwargs) -> bool:
        """Validate inputs for complete workflow."""
        # Validate that all required directories exist
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
        """Run the complete workflow sequentially."""
        try:
            self.logger.info("Starting Complete Workflow")
            
            # Get the global stage registry
            from percell.application.stages_api import get_stage_registry
            registry = get_stage_registry()
            
            # Build workflow steps subset in canonical order based on available stages
            stage_to_step = {
                'data_selection': WorkflowStep.DATA_SELECTION,
                'segmentation': WorkflowStep.SEGMENTATION,
                'process_single_cell': WorkflowStep.PROCESSING,
                'threshold_grouped_cells': WorkflowStep.THRESHOLDING,
                'analysis': WorkflowStep.ANALYSIS,
            }
            requested_steps: List[WorkflowStep] = [
                stage_to_step[name] for name, _ in self.stages if name in stage_to_step
            ]
            # Normalize and validate steps
            normalized = self._orchestration.handle_custom_workflows(requested_steps)
            self._orchestration.validate_workflow_steps(normalized)
            wf_config = WorkflowConfig(steps=normalized)
            self._orchestration.coordinate_step_execution(normalized, wf_config)
            
            # Track workflow state
            state = WorkflowState.PENDING
            state = self._orchestration.manage_workflow_state(state, "start")
            
            for stage_name, stage_display_name in self.stages:
                self.logger.info(f"Starting {stage_display_name}...")
                
                # Create stage-specific arguments
                stage_args = self._create_stage_args(stage_name, kwargs)
                
                # Execute the stage
                stage_class = registry.get_stage_class(stage_name)
                if not stage_class:
                    self.logger.error(f"Stage not found: {stage_name}")
                    return False
                
                stage = stage_class(self.config, self.pipeline_logger, stage_name)
                success = stage.execute(**stage_args)
                
                if not success:
                    self.logger.error(f"{stage_display_name} failed!")
                    state = self._orchestration.manage_workflow_state(state, "error")
                    return False
                
                self.logger.info(f"{stage_display_name} completed successfully!")
            
            # Completed all stages
            state = self._orchestration.manage_workflow_state(state, "complete")
            self.logger.info(f"Workflow completed with state: {state.name}")
            self.logger.info("Complete Workflow finished successfully!")
            return True
            
        except Exception as e:
            self.logger.error(f"Error in Complete Workflow: {e}")
            return False
    
    def _create_stage_args(self, stage_name: str, base_args: dict) -> dict:
        """Create stage-specific arguments."""
        stage_args = base_args.copy()
        
        # Clear all stage flags and set only the current one
        stage_flags = ['data_selection', 'segmentation', 'process_single_cell',
                      'threshold_grouped_cells', 'measure_roi_area', 'analysis']
        
        for flag in stage_flags:
            stage_args[flag] = (flag == stage_name)
        
        return stage_args 