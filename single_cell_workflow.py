#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Microscopy Single-Cell Analysis Workflow Orchestrator

This script orchestrates the entire single-cell analysis workflow by combining multiple
scripts and handling transitions between automated and manual steps. It's designed to 
process microscopy data with specific naming conventions (R_X for regions, tXX for 
time points, chXX for channels) and organize analysis results.
"""

import logging
import json
import subprocess
import sys
import time
import os
import shutil
import re
from pathlib import Path
from datetime import datetime
from typing import List, Optional, Set, Dict, Any
import argparse

# Configure logging
logger = logging.getLogger('SingleCellWorkflow')

class WorkflowOrchestrator:
    """Main class to orchestrate the single-cell analysis workflow."""
    
    def __init__(self, config_path, input_dir, output_dir, skip_steps=None, 
                 datatype: Optional[str] = None, 
                 conditions: Optional[List[str]] = None, 
                 segmentation_channel: Optional[str] = None,
                 analysis_channels: Optional[List[str]] = None,
                 timepoints=None, regions=None, setup_only=False,
                 start_from: Optional[str] = None, bins: int = 5):
        """
        Initialize the workflow orchestrator.
        
        Args:
            config_path (str): Path to the configuration file.
            input_dir (str): Directory containing input data.
            output_dir (str): Directory for output results.
            skip_steps (list): List of step names to skip (optional).
            datatype (str): Specific data type to analyze (optional).
            conditions (list): List of specific conditions to analyze (optional).
            segmentation_channel (str): Channel to use for cell segmentation (optional).
            analysis_channels (list): List of channels to analyze (optional).
            timepoints (list): List of timepoints to analyze (e.g., ["t00", "t03"]).
            regions (list): List of regions to analyze (e.g., ["R_1", "R_2", "R_3"]).
            setup_only (bool): Flag to indicate if only directory setup should be performed.
            start_from (str): Step name to start the workflow from (optional).
            bins (int): Number of bins for grouping cells (default: 5).
        """
        self.config_path = config_path
        self.input_dir = Path(input_dir).resolve()
        self.output_dir = Path(output_dir).resolve()
        self.skip_steps = skip_steps or []
        self.selected_datatype = datatype
        self.selected_conditions = conditions or []
        self.segmentation_channel = segmentation_channel
        self.analysis_channels = analysis_channels or []
        self.timepoints = timepoints or []
        self.regions = regions or []
        self.setup_only = setup_only
        self.start_from = start_from
        self.bins = bins
        
        # --- BEGIN DEBUG LOG ---
        logger.debug(f"__init__: self.selected_conditions = {self.selected_conditions}")
        logger.debug(f"__init__: self.regions = {self.regions}")
        logger.debug(f"__init__: self.segmentation_channel = {self.segmentation_channel}")
        logger.debug(f"__init__: self.analysis_channels = {self.analysis_channels}")
        # --- END DEBUG LOG ---
        
        # Load configuration
        self.config = self._load_config()
        self.imagej_path = self.config.get('imagej_path', 'ImageJ') # Get ImageJ path
        
        # Extract experiment metadata from directory structure
        self.experiment_metadata = self._extract_experiment_metadata()
        
        # Create output directory if it doesn't exist
        os.makedirs(self.output_dir, exist_ok=True)
        
        # Store workflow state
        self.workflow_state = {
            'start_time': datetime.now().isoformat(),
            'steps_completed': [],
            'steps_skipped': [],
            'current_step': None,
            'experiment_metadata': self.experiment_metadata,
            'selected_datatype': self.selected_datatype,
            'selected_conditions': self.selected_conditions,
            'segmentation_channel': self.segmentation_channel,
            'analysis_channels': self.analysis_channels,
            'selected_timepoints': self.timepoints,
            'selected_regions': self.regions,
            'bins': self.bins
        }
        
        # Load or initialize state
        self.state_file = self.output_dir / '.workflow_state.json'
        
    def _extract_experiment_metadata(self):
        """
        Extract experiment metadata from the directory structure.
        This analyzes the microscopy data folders to identify conditions, regions, timepoints, etc.
        
        Returns:
            dict: Dictionary containing experiment metadata
        """
        metadata = {
            'conditions': [],
            'regions': set(),
            'timepoints': set(),
            'channels': set(),
            'region_to_channels': {},  # Map from region name to set of available channels
            'datatype_inferred': 'multi_timepoint'
        }
        
        logger.info(f"Scanning input directory: {self.input_dir}")
        if not self.input_dir.exists():
            logger.error(f"Input directory does not exist: {self.input_dir}")
            return metadata
            
        # List all items in the input directory
        input_items = list(self.input_dir.glob("*"))
        logger.info(f"Found {len(input_items)} items in input directory")
        
        # Count directories to help with debugging
        input_dirs = [item for item in input_items if item.is_dir() and not item.name.startswith('.')]
        logger.info(f"Found {len(input_dirs)} directories in input directory: {[d.name for d in input_dirs]}")
        
        if not input_dirs:
            logger.warning("No subdirectories found in input directory. Expected at least one condition directory.")
            return metadata
        
        # Find all directories in the input directory as potential conditions
        for item in input_dirs:
            condition_name = item.name
            metadata['conditions'].append(condition_name)
            
            # Count TIF files in this condition
            tif_files = list(item.glob("**/*.tif"))
            logger.info(f"Found {len(tif_files)} TIF files in condition '{condition_name}'")
            
            if not tif_files:
                logger.warning(f"No TIF files found in condition directory: {condition_name}")
                continue
                
            # Log some example filenames to help with debugging
            if tif_files:
                examples = [f.name for f in tif_files[:3]]
                logger.info(f"Example filenames: {examples}")
            
            # Process files within each condition to extract regions/timepoints/channels
            for tif_file in tif_files:
                # Extract region and channel from filename
                # Expected format: [RegionName]_Merged_t00_ch00.tif
                filename = tif_file.name
                
                # Extract timepoint
                timepoint_match = re.search(r'(t\d+)', filename)
                if timepoint_match:
                    metadata['timepoints'].add(timepoint_match.group(1))
                
                # Extract channel
                channel_match = re.search(r'(ch\d+)', filename)
                if channel_match:
                    channel = channel_match.group(1)
                    metadata['channels'].add(channel)
                
                # Extract region by looking at what's not a channel or timepoint
                # Remove channel and timepoint parts from filename
                temp_name = re.sub(r'(ch\d+|t\d+)', '', filename)
                # Remove file extension
                temp_name = os.path.splitext(temp_name)[0]
                # Remove any trailing or duplicate underscores from the result and clean it up
                region_name = re.sub(r'_+', '_', temp_name).strip('_')
                if region_name:  # Only add if not empty
                    metadata['regions'].add(region_name)
                    
                    # Add channel to this region's available channels
                    if channel_match:
                        if region_name not in metadata['region_to_channels']:
                            metadata['region_to_channels'][region_name] = set()
                        metadata['region_to_channels'][region_name].add(channel)
        
        # Convert sets to sorted lists for consistent ordering
        metadata['regions'] = sorted(list(metadata['regions']))
        metadata['timepoints'] = sorted(list(metadata['timepoints']))
        metadata['channels'] = sorted(list(metadata['channels']))
        metadata['conditions'] = sorted(metadata['conditions'])
        
        # Convert the region_to_channels sets to sorted lists
        for region in metadata['region_to_channels']:
            metadata['region_to_channels'][region] = sorted(list(metadata['region_to_channels'][region]))
        
        # Infer datatype based on number of timepoints found
        if len(metadata['timepoints']) <= 1:
            metadata['datatype_inferred'] = 'single_timepoint'
        
        # Log the extracted metadata for debugging
        logger.info(f"Extracted metadata:")
        logger.info(f"  Conditions: {metadata['conditions']}")
        logger.info(f"  Regions: {metadata['regions']}")
        logger.info(f"  Timepoints: {metadata['timepoints']}")
        logger.info(f"  Channels: {metadata['channels']}")
        
        return metadata
    
    def setup_base_directories(self):
        """
        Set up just the base directory structure without creating condition-specific subdirectories.
        This creates only the first level of directories needed for the workflow.
        
        Returns:
            bool: True if successful, False otherwise
        """
        logger.info("Setting up base directory structure")
        
        try:
            # Define the main directories to create (relative to output_dir)
            main_dirs = ['analysis', 'cells', 'combined_masks', 'grouped_cells', 
                        'grouped_masks', 'masks', 'raw_data', 'ROIs', 'macros']
            
            # Create the main directories
            for dir_name in main_dirs:
                (self.output_dir / dir_name).mkdir(parents=True, exist_ok=True)
                
            logger.info("Base directory setup complete")
            return True
            
        except Exception as e:
            logger.error(f"Error setting up base directory structure: {e}", exc_info=True)
            return False
    
    def setup_condition_directories(self):
        """
        Set up directories specific to selected conditions after condition selection step.
        
        Returns:
            bool: True if successful, False otherwise
        """
        logger.info("Setting up condition-specific directories")
        
        try:
            # Get selected conditions
            conditions_to_process = self.selected_conditions
            
            if not conditions_to_process:
                logger.warning("No conditions selected, skipping condition directory setup")
                return True
                
            logger.info(f"Creating condition directories for: {conditions_to_process}")
            
            # Create condition-level subdirectories in analysis folders
            base_dirs_with_condition_subdir = ['cells', 'combined_masks', 'grouped_cells', 
                                              'grouped_masks', 'masks', 'ROIs']
            
            for base_dir_name in base_dirs_with_condition_subdir:
                base_path = self.output_dir / base_dir_name
                for condition_name in conditions_to_process:
                    (base_path / condition_name).mkdir(parents=True, exist_ok=True)
            
            # Create raw_data condition directories and copy files
            input_conditions_found = {item.name for item in self.input_dir.glob("*") if item.is_dir() and not item.name.startswith('.')}
            
            for condition_name in conditions_to_process:
                if condition_name in input_conditions_found:
                    source_cond_dir = self.input_dir / condition_name
                    dest_cond_dir = self.output_dir / "raw_data" / condition_name
                    
                    # Just create the directory but don't copy files yet - that happens after all selections
                else:
                    logger.warning(f"Selected condition '{condition_name}' not found in input directory {self.input_dir}, skipping.")
            
            logger.info("Condition directory setup complete")
            return True
            
        except Exception as e:
            logger.error(f"Error setting up condition directories: {e}", exc_info=True)
            return False
    
    def setup_timepoint_directories(self):
        """
        Set up directories specific to selected timepoints after timepoint selection step.
        
        Returns:
            bool: True if successful, False otherwise
        """
        logger.info("Setting up timepoint-specific directories")
        
        try:
            # Get selected conditions and timepoints
            conditions_to_process = self.selected_conditions
            timepoints_to_process = self.timepoints
            
            if not conditions_to_process:
                logger.warning("No conditions selected, skipping timepoint directory setup")
                return True
                
            if not timepoints_to_process:
                logger.warning("No timepoints selected, skipping timepoint directory setup")
                return True
                
            logger.info(f"Creating timepoint directories for timepoints: {timepoints_to_process}")
            
            # Create region-timepoint directories structure (even before region selection)
            # We'll create all region-timepoint combinations since we know timepoints now
            base_dirs_with_time_subdir = ['cells', 'grouped_cells', 'grouped_masks', 'masks']
            
            for base_dir_name in base_dirs_with_time_subdir:
                base_path = self.output_dir / base_dir_name
                for condition_name in conditions_to_process:
                    condition_path = base_path / condition_name
                    # Create placeholder directories with timepoints
                    # Region selection will fill in the correct region names later
                    for timepoint in timepoints_to_process:
                        # Create a placeholder directory for all timepoints
                        # The actual region_timepoint directories will be created after region selection
                        (condition_path / f"timepoint_{timepoint}").mkdir(parents=True, exist_ok=True)
            
            logger.info("Timepoint directory setup complete")
            return True
            
        except Exception as e:
            logger.error(f"Error setting up timepoint directories: {e}", exc_info=True)
            return False
    
    def setup_analysis_directories(self):
        """
        Set up the final directory structure for analysis based on selected conditions, regions, and timepoints.
        This creates the final region_timepoint directories and copies selected files.
        
        Returns:
            bool: True if successful, False otherwise
        """
        logger.info("Setting up final analysis directory structure based on selections")
        
        try:
            # Determine target items based on selections or defaults from metadata
            conditions_to_process = self.selected_conditions or self.experiment_metadata.get('conditions', [])
            regions_to_process = self.regions or self.experiment_metadata.get('regions', [])
            timepoints_to_process = self.timepoints or self.experiment_metadata.get('timepoints', [])
            channels_to_process = self.analysis_channels or self.experiment_metadata.get('channels', [])

            logger.info(f"Creating directories for Conditions: {conditions_to_process}")
            logger.info(f"Creating directories for Regions: {regions_to_process}")
            logger.info(f"Creating directories for Timepoints: {timepoints_to_process}")
            logger.info(f"Selected Channels: {channels_to_process}")
            
            # Clean up any placeholder timepoint directories
            base_dirs_with_time_subdir = ['cells', 'grouped_cells', 'grouped_masks', 'masks']
            for base_dir_name in base_dirs_with_time_subdir:
                base_path = self.output_dir / base_dir_name
                for condition_name in conditions_to_process:
                    condition_path = base_path / condition_name
                    # Remove placeholder timepoint directories
                    for placeholder_dir in condition_path.glob("timepoint_*"):
                        if placeholder_dir.is_dir():
                            try:
                                placeholder_dir.rmdir()  # This will only succeed if empty
                            except:
                                pass  # If not empty, just leave it
            
            # Skip creating region-timepoint subdirectories
            # We're removing this part because the actual directories used by the scripts
            # are created automatically with more specific naming conventions
            # This fixes the issue of having duplicate directories like:
            # - 120min_washout_t00 (created here but never used)
            # - 120min_washout_Merged_ch00_t00_t00 (created by ImageJ and actually used)
            
            # Instead, just ensure the base condition directories exist
            base_dirs_with_region_time_subdir = ['cells', 'grouped_cells', 'grouped_masks', 'masks']
            for base_dir_name in base_dirs_with_region_time_subdir:
                base_path = self.output_dir / base_dir_name
                for condition_name in conditions_to_process:
                    condition_path = base_path / condition_name
                    condition_path.mkdir(parents=True, exist_ok=True)
                    
            logger.info("Base condition directories created - specific region directories will be created by the processing scripts")
            
            # --- Copy selected raw data files ---
            logger.info("Copying selected raw data files...")
            input_conditions_found = {item.name for item in self.input_dir.glob("*") if item.is_dir() and not item.name.startswith('.')}
            
            for condition_name in conditions_to_process:
                if condition_name in input_conditions_found:
                    source_cond_dir = self.input_dir / condition_name
                    dest_cond_dir = self.output_dir / "raw_data" / condition_name
                    
                    # Copy only files matching selected regions, timepoints, channels
                    for item in source_cond_dir.glob("**/*"):
                        if item.is_file() and item.suffix.lower() == '.tif':
                            filename = item.name
                            
                            # Check if file matches our selected criteria
                            region_match = any(region in filename for region in regions_to_process)
                            timepoint_match = any(timepoint in filename for timepoint in timepoints_to_process)
                            
                            # Copy files for both segmentation channel and analysis channels
                            # bin_images_for_segmentation needs segmentation channel files from raw_data
                            # Later analysis steps need analysis channel files from raw_data
                            channels_needed = set(channels_to_process) if channels_to_process else set()
                            if self.segmentation_channel:
                                channels_needed.add(self.segmentation_channel)
                            
                            channel_match = any(channel in filename for channel in channels_needed) if channels_needed else True
                            
                            if region_match and timepoint_match and channel_match:
                                rel_path = item.relative_to(source_cond_dir)
                                target_file = dest_cond_dir / rel_path
                                target_file.parent.mkdir(parents=True, exist_ok=True)
                                shutil.copy2(item, target_file)
                                logger.debug(f"Copied file: {item} to {target_file}")
                else:
                     logger.warning(f"Selected condition '{condition_name}' not found in input directory {self.input_dir}, skipping copy.")
            logger.info("Raw data copying complete.")
            
            logger.info("Directory setup complete")
            return True
            
        except Exception as e:
            logger.error(f"Error setting up directory structure: {e}", exc_info=True) # Add traceback
            return False
    
    def _load_config(self):
        """Load the workflow configuration from JSON file."""
        try:
            with open(self.config_path, 'r') as f:
                config = json.load(f)
            return config
        except Exception as e:
            logger.error(f"Failed to load configuration file: {e}")
            sys.exit(1)
    
    def _save_state(self):
        """Save the current workflow state to a JSON file."""
        state_file = self.output_dir / "workflow_state.json"
        try:
            with open(state_file, 'w') as f:
                json.dump(self.workflow_state, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save workflow state: {e}")
    
    def _restart_from_step(self, step_name):
        """
        Restart the workflow from a specific step.
        
        Args:
            step_name (str): Name of the step to restart from
            
        Returns:
            bool: True if successful, False otherwise
        """
        logger.info(f"Restarting workflow from step: {step_name}")
        
        try:
            # Load workflow steps from config
            steps = self.config.get('steps', [])
            if not steps:
                logger.error("No steps defined in workflow configuration")
                return False
            
            # Find the step to restart from
            start_index = None
            for i, step in enumerate(steps):
                if step['name'] == step_name:
                    start_index = i
                    break
            
            if start_index is None:
                logger.error(f"Step '{step_name}' not found in workflow")
                return False
            
            # Execute steps starting from the specified step
            for i, step in enumerate(steps[start_index:], start_index):
                step_name = step['name']
                
                # Skip if step is in skip list
                if step_name in self.skip_steps:
                    logger.info(f"Skipping step: {step_name}")
                    self.workflow_state['steps_skipped'].append(step_name)
                    continue
                
                logger.info(f"Executing step {i+1}/{len(steps)}: {step_name}")
                self.workflow_state['current_step'] = step_name
                
                # Handle different step types
                if step['type'] == 'bash':
                    success = self.run_bash_script(step['path'], step.get('args', []))
                elif step['type'] == 'python':
                    success, result_data = self.run_python_script(step['path'], step.get('args', []))
                    
                    # Handle special case: need more bins for cell grouping
                    if result_data.get('needs_more_bins', False):
                        logger.info(f"Step {step_name} indicated need for more bins. Going back to group_cells step.")
                        
                        # Find the group_cells step and restart from there
                        group_cells_index = None
                        for j, prev_step in enumerate(steps):
                            if prev_step['name'] == 'group_cells':
                                group_cells_index = j
                                break
                        
                        if group_cells_index is not None:
                            logger.info(f"Restarting workflow from group_cells step (index {group_cells_index})")
                            # Update bins count to add one more bin
                            self.bins += 1
                            logger.info(f"Increased bin count to {self.bins}")
                            
                            # Update workflow state
                            self.workflow_state['bins'] = self.bins
                            self._save_state()
                            
                            # Restart from group_cells step recursively
                            return self._restart_from_step('group_cells')
                        else:
                            logger.error("Could not find group_cells step to restart from")
                            return False
                elif step['type'] == 'manual':
                    success = self.prompt_manual_step(step_name, step.get('instructions', ''))
                else:
                    logger.error(f"Unknown step type: {step['type']}")
                    success = False
                
                if not success:
                    logger.error(f"Step {step_name} failed")
                    return False
                    
                self.workflow_state['steps_completed'].append(step_name)
                self._save_state()
                
            logger.info("Workflow restart completed successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error during workflow restart: {e}", exc_info=True)
            return False
    
    def run_bash_script(self, script_path, args=None):
        """
        Run a bash script with the specified arguments.
        
        Args:
            script_path (str): Path to the bash script.
            args (list): List of arguments to pass to the script.
        
        Returns:
            bool: True if successful, False otherwise.
        """
        cmd = ['/bin/bash', script_path]
        if args:
            # Substitute placeholders in arguments
            substituted_args = []
            for arg in args:
                # Handle list placeholders that need to be expanded into multiple arguments
                if '{conditions}' in arg and self.selected_conditions:
                    # Replace {conditions} placeholder with multiple arguments
                    base_arg = arg.replace('{conditions}', '').strip()
                    if base_arg:  # If there's text before/after the placeholder
                        substituted_args.extend([base_arg + condition for condition in self.selected_conditions])
                    else:  # If the arg is just {conditions}
                        substituted_args.extend(self.selected_conditions)
                    continue
                elif '{regions}' in arg and self.regions:
                    # Replace {regions} placeholder with multiple arguments  
                    base_arg = arg.replace('{regions}', '').strip()
                    if base_arg:
                        substituted_args.extend([base_arg + region for region in self.regions])
                    else:
                        substituted_args.extend(self.regions)
                    continue
                elif '{timepoints}' in arg and self.timepoints:
                    # Replace {timepoints} placeholder with multiple arguments
                    base_arg = arg.replace('{timepoints}', '').strip()
                    if base_arg:
                        substituted_args.extend([base_arg + timepoint for timepoint in self.timepoints])
                    else:
                        substituted_args.extend(self.timepoints)
                    continue
                elif '{analysis_channels}' in arg and self.analysis_channels:
                    # Replace {analysis_channels} placeholder with multiple arguments
                    base_arg = arg.replace('{analysis_channels}', '').strip()
                    if base_arg:
                        substituted_args.extend([base_arg + channel for channel in self.analysis_channels])
                    else:
                        substituted_args.extend(self.analysis_channels)
                    continue
                else:
                    # Handle single-value placeholders normally
                    arg = arg.replace('{input_dir}', str(self.input_dir)) \
                             .replace('{output_dir}', str(self.output_dir)) \
                             .replace('{imagej_path}', self.config.get('imagej_path', 'ImageJ')) \
                             .replace('{segmentation_channel}', self.segmentation_channel or '') \
                             .replace('{bins}', str(self.bins))
                    substituted_args.append(arg)
            cmd.extend(substituted_args)
            
        logger.info(f"Running bash script: {script_path}")
        try:
            # Run without capturing stdout/stderr
            process = subprocess.run(
                cmd,
                check=True,
                text=True,
                encoding='utf-8'
            )
            logger.info(f"Bash script completed successfully: {script_path}")
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"Bash script {script_path} failed with exit code {e.returncode}")
            return False
    
    def run_python_script(self, script_path, args=None):
        """
        Run a Python script with the specified arguments.
        
        Args:
            script_path (str): Path to the Python script.
            args (list): List of arguments to pass to the script.
        
        Returns:
            tuple: (bool, dict) - (success, result_data)
            where result_data may contain additional information like 'needs_more_bins'
        """
        args = args or []
        command = [sys.executable, script_path]
        
        # Substitute placeholders in arguments
        substituted_args = []
        for arg in args:
            # Handle list placeholders that need to be expanded into multiple arguments
            if '{conditions}' in arg and self.selected_conditions:
                # Replace {conditions} placeholder with multiple arguments
                base_arg = arg.replace('{conditions}', '').strip()
                if base_arg:  # If there's text before/after the placeholder
                    substituted_args.extend([base_arg + condition for condition in self.selected_conditions])
                else:  # If the arg is just {conditions}
                    substituted_args.extend(self.selected_conditions)
                continue
            elif '{regions}' in arg and self.regions:
                # Replace {regions} placeholder with multiple arguments  
                base_arg = arg.replace('{regions}', '').strip()
                if base_arg:
                    substituted_args.extend([base_arg + region for region in self.regions])
                else:
                    substituted_args.extend(self.regions)
                continue
            elif '{timepoints}' in arg and self.timepoints:
                # Replace {timepoints} placeholder with multiple arguments
                base_arg = arg.replace('{timepoints}', '').strip()
                if base_arg:
                    substituted_args.extend([base_arg + timepoint for timepoint in self.timepoints])
                else:
                    substituted_args.extend(self.timepoints)
                continue
            elif '{analysis_channels}' in arg and self.analysis_channels:
                # Replace {analysis_channels} placeholder with multiple arguments
                base_arg = arg.replace('{analysis_channels}', '').strip()
                if base_arg:
                    substituted_args.extend([base_arg + channel for channel in self.analysis_channels])
                else:
                    substituted_args.extend(self.analysis_channels)
                continue
            else:
                # Handle single-value placeholders normally
                arg = arg.replace('{input_dir}', str(self.input_dir)) \
                         .replace('{output_dir}', str(self.output_dir)) \
                         .replace('{imagej_path}', self.config.get('imagej_path', 'ImageJ')) \
                         .replace('{segmentation_channel}', self.segmentation_channel or '') \
                         .replace('{bins}', str(self.bins))
                substituted_args.append(arg)
        command.extend(substituted_args)
        
        logger.info(f"Running Python script: {script_path} with args: {substituted_args}") # Log arguments for clarity
        
        try:
            # Run without capturing stdout/stderr
            process = subprocess.run(
                command,
                check=False,  # Don't raise exception so we can handle special exit codes
                text=True,
                encoding='utf-8'
            )
            
            # Check for special exit codes
            if process.returncode == 5:  # Special exit code for "need more bins"
                logger.info(f"Python script {script_path} indicated need for more bins with exit code 5")
                return True, {'needs_more_bins': True}
            
            # Handle normal exit codes
            if process.returncode == 0:
                logger.info(f"Python script completed successfully: {script_path}")
                return True, {}
            else:
                logger.error(f"Python script {script_path} failed with exit code {process.returncode}")
                return False, {}
        except Exception as e:
            logger.error(f"Error executing Python script {script_path}: {e}")
            return False, {}
    
    def run_imagej_macro(self, macro_path, args=None):
        """
        Run an ImageJ macro with the specified arguments.
        
        Args:
            macro_path (str): Path to the ImageJ macro.
            args (str): Arguments to pass to the macro.
        
        Returns:
            bool: True if successful, False otherwise.
        """
        # Get ImageJ path from config
        imagej_path = self.config.get('imagej_path', 'ImageJ')
        
        # Construct absolute path to macro
        abs_macro_path = Path(macro_path)
        if not abs_macro_path.is_absolute():
            abs_macro_path = Path.cwd() / macro_path
        
        # Build command
        cmd = [imagej_path, '--headless', '--console', '--run', str(abs_macro_path)]
        if args:
            cmd.append(f'"{args}"')
        
        # Log the exact command
        logger.info(f"Running ImageJ command: {' '.join(cmd)}")
        
        try:
            # Run without capturing stdout/stderr
            process = subprocess.run(
                cmd,
                check=True,
                text=True,
                encoding='utf-8'
            )
            logger.info(f"ImageJ macro completed successfully: {macro_path}")
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"ImageJ macro {macro_path} failed with exit code {e.returncode}")
            return False
    
    def launch_gui_application(self, app_path, instructions):
        """
        Launch a GUI application and prompt the user for manual interaction.
        
        Args:
            app_path (str): Path to the GUI application.
            instructions (str): Instructions for the user.
        
        Returns:
            bool: True when the user confirms completion.
        """
        logger.info(f"Launching GUI application: {app_path}")
        
        # Start the GUI application in a new process
        try:
            process = subprocess.Popen([app_path])
            
            # Display instructions to the user
            print("\n" + "="*80)
            print(f"MANUAL STEP REQUIRED: {app_path}")
            print("="*80)
            print(instructions)
            print("\nPress Enter when you have completed this step...")
            input()
            
            # Try to terminate the process (if it's still running)
            try:
                process.terminate()
                time.sleep(1)
                if process.poll() is None:  # If process hasn't terminated
                    process.kill()
            except:
                pass
                
            return True
            
        except Exception as e:
            logger.error(f"Error launching GUI application: {e}")
            return False
    
    def prompt_manual_step(self, step_name, instructions):
        """
        Prompt the user to perform a manual step.
        
        Args:
            step_name (str): Name of the manual step.
            instructions (str): Instructions for the user.
        
        Returns:
            bool: True when the user confirms completion.
        """
        logger.info(f"Manual step required: {step_name}")
        
        # Replace placeholders in instructions
        instructions = instructions.replace('{input_dir}', str(self.input_dir)) \
                               .replace('{output_dir}', str(self.output_dir)) \
                               .replace('{imagej_path}', self.config.get('imagej_path', 'ImageJ'))
        
        # Replace timepoints and regions lists
        instructions = instructions.replace('{conditions_list}', ', '.join(self.experiment_metadata['conditions']))
        instructions = instructions.replace('{channels_list}', ', '.join(self.experiment_metadata['channels']))
        instructions = instructions.replace('{timepoints_list}', ', '.join(self.experiment_metadata.get('timepoints', [])))
        instructions = instructions.replace('{regions_list}', ', '.join(self.experiment_metadata.get('regions', [])))
        
        print("\n" + "="*80)
        print(f"MANUAL STEP REQUIRED: {step_name}")
        print("="*80)
        print(instructions)
        
        # Handle special manual steps that require input
        if step_name == "select_datatype" and not self.selected_datatype:
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
                logger.warning(f"Invalid datatype selection '{user_input}'. Using detected default: {inferred_datatype}")
                self.selected_datatype = inferred_datatype
                
            logger.info(f"Selected datatype: {self.selected_datatype}")
            self.workflow_state['selected_datatype'] = self.selected_datatype
        
        elif step_name == "select_condition" and not self.selected_conditions:
            available_items = self.experiment_metadata['conditions']
            item_type = "conditions"
            self.selected_conditions = self._handle_list_selection(available_items, item_type, self.selected_conditions)
            self.workflow_state['selected_conditions'] = self.selected_conditions
            
        elif step_name == "select_timepoints" and not self.timepoints:
            available_items = self.experiment_metadata['timepoints']
            item_type = "timepoints"
            self.timepoints = self._handle_list_selection(available_items, item_type, self.timepoints)
            self.workflow_state['selected_timepoints'] = self.timepoints
            
        elif step_name == "select_regions" and not self.regions:
            # Only show regions that exist in the selected conditions
            if not self.selected_conditions:
                logger.warning("No conditions selected. Please select conditions first.")
                return False
                
            # Filter regions based on the selected conditions
            # Get all tif files for selected conditions
            available_regions_by_condition = {}
            for condition in self.selected_conditions:
                condition_dir = self.input_dir / condition
                if condition_dir.exists():
                    # Find all TIF files in this condition
                    tif_files = list(condition_dir.glob("**/*.tif"))
                    # Extract regions from filenames
                    regions_in_condition = set()
                    for tif_file in tif_files:
                        filename = tif_file.name
                        # Extract region by looking at what's not a channel or timepoint
                        # Remove channel and timepoint parts from filename
                        temp_name = re.sub(r'(ch\d+|t\d+)', '', filename)
                        # Remove file extension
                        temp_name = os.path.splitext(temp_name)[0]
                        # Remove any trailing or duplicate underscores from the result and clean it up
                        region_name = re.sub(r'_+', '_', temp_name).strip('_')
                        if region_name:  # Only add if not empty
                            regions_in_condition.add(region_name)
                    available_regions_by_condition[condition] = sorted(list(regions_in_condition))
                else:
                    logger.warning(f"Selected condition '{condition}' directory not found")
                    available_regions_by_condition[condition] = []
            
            # Log the regions available in each condition
            for condition, regions in available_regions_by_condition.items():
                logger.info(f"Regions available in condition '{condition}': {regions}")
            
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
                logger.error("Selected conditions have different available regions:")
                for condition, regions in available_regions_by_condition.items():
                    logger.error(f"  '{condition}': {regions}")
                logger.error("The workflow cannot proceed with inconsistent regions across conditions.")
                print("\nERROR: Selected conditions have different available regions.")
                print("Please select conditions with the same regions or modify your data structure.")
                print("Press Enter to exit...")
                input()
                sys.exit(1)
                
            # All conditions have the same regions, so we can use the first one's regions list
            available_items = available_regions_by_condition.get(self.selected_conditions[0], [])
            logger.info(f"Available regions for selected conditions: {available_items}")
            
            if not available_items:
                logger.error("No regions found for the selected conditions")
                print("\nERROR: No regions found for the selected conditions.")
                print("Press Enter to exit...")
                input()
                sys.exit(1)
                
            item_type = "regions"
            self.regions = self._handle_list_selection(available_items, item_type, self.regions)
            self.workflow_state['selected_regions'] = self.regions
            
        elif step_name == "select_segmentation_channel" and not self.segmentation_channel:
            available_items = self.experiment_metadata['channels']
            item_type = "segmentation channel"
            selected_channels = self._handle_list_selection(available_items, item_type, [])
            if selected_channels:
                self.segmentation_channel = selected_channels[0]  # Take first selection only
                self.workflow_state['segmentation_channel'] = self.segmentation_channel
            
        elif step_name == "select_analysis_channels" and not self.analysis_channels:
            available_items = self.experiment_metadata['channels']
            item_type = "analysis channel"
            self.analysis_channels = self._handle_list_selection(available_items, item_type, self.analysis_channels)
            self.workflow_state['analysis_channels'] = self.analysis_channels
            
        else:
            print("\nPress Enter when you have completed this step...")
            input()
        
        return True
    
    def _handle_list_selection(self, available_items: List[str], item_type: str, target_list: List[str]):
        """
        Handle selection of items from a list with interactive CLI.
        
        Args:
            available_items (List[str]): List of available items to choose from
            item_type (str): Type of items being selected (e.g., 'condition', 'channel')
            target_list (List[str]): List to store selected items
            
        Returns:
            List[str]: List of selected items
        """
        if not available_items:
            logger.warning(f"No {item_type}s available for selection")
            return []
            
        print(f"\nAvailable {item_type}s:")
        for i, item in enumerate(available_items, 1):
            print(f"{i}. {item}")
            
        print(f"\nInput options for {item_type}s:")
        print(f"- Enter {item_type}s as space-separated text (e.g., '{available_items[0]} {available_items[-1] if len(available_items) > 1 else available_items[0]}')")
        print(f"- Enter numbers from the list (e.g., '1 {len(available_items)}')")
        print(f"- Type 'all' to select all {item_type}s")
        
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
    
    def run_workflow(self):
        """
        Run the complete workflow.
        
        Returns:
            bool: True if workflow completed successfully, False otherwise
        """
        logger.info("Starting workflow execution")
        
        try:
            # Set up base directory structure first
            if not self.setup_base_directories():
                logger.error("Failed to set up base directories")
                return False
            
            # Load workflow steps from config
            steps = self.config.get('steps', [])
            if not steps:
                logger.error("No steps defined in workflow configuration")
                return False
            
            # Define which steps are manual selection steps that should always be executed first
            manual_selection_steps = [
                'select_datatype',
                'select_condition', 
                'select_timepoints',
                'select_regions',
                'select_segmentation_channel',
                'select_analysis_channels'
            ]
            
            # If start_from is specified, first execute all manual selection steps
            if self.start_from:
                logger.info(f"Executing manual selection steps before starting from '{self.start_from}'")
                
                for step in steps:
                    step_name = step['name']
                    
                    # Execute manual selection steps
                    if step_name in manual_selection_steps:
                        # Skip if step is in skip list
                        if step_name in self.skip_steps:
                            logger.info(f"Skipping manual selection step: {step_name}")
                            self.workflow_state['steps_skipped'].append(step_name)
                            continue
                        
                        logger.info(f"Executing manual selection step: {step_name}")
                        self.workflow_state['current_step'] = step_name
                        
                        # Handle manual step
                        if step['type'] == 'manual':
                            success = self.prompt_manual_step(step_name, step.get('instructions', ''))
                            
                            # Set up directories after specific manual steps
                            if success and step_name == 'select_condition' and self.selected_conditions:
                                if not self.setup_condition_directories():
                                    logger.error("Failed to set up condition directories")
                                    return False
                            elif success and step_name == 'select_timepoints' and self.timepoints:
                                if not self.setup_timepoint_directories():
                                    logger.error("Failed to set up timepoint directories")
                                    return False
                            elif success and step_name == 'select_analysis_channels' and self.analysis_channels:
                                # Set up final analysis directory structure after all selections are made
                                if not self.setup_analysis_directories():
                                    logger.error("Failed to set up analysis directories")
                                    return False
                        else:
                            success = False
                            logger.error(f"Manual selection step {step_name} has unexpected type: {step['type']}")
                        
                        if not success:
                            logger.error(f"Manual selection step {step_name} failed")
                            return False
                            
                        self.workflow_state['steps_completed'].append(step_name)
                        self._save_state()
                
                # Find start step index for processing steps
                start_index = 0
                for i, step in enumerate(steps):
                    if step['name'] == self.start_from:
                        start_index = i
                        break
                else:
                    logger.error(f"Start step '{self.start_from}' not found in workflow")
                    return False
                
                logger.info(f"Starting processing steps from step: {self.start_from}")
                
            else:
                # Normal execution from the beginning
                start_index = 0
            
            # Execute processing steps
            for i, step in enumerate(steps[start_index:], start_index):
                step_name = step['name']
                
                # Skip manual selection steps if we already executed them above
                if self.start_from and step_name in manual_selection_steps:
                    continue
                
                # Skip if step is in skip list
                if step_name in self.skip_steps:
                    logger.info(f"Skipping step: {step_name}")
                    self.workflow_state['steps_skipped'].append(step_name)
                    continue
                
                logger.info(f"Executing step {i+1}/{len(steps)}: {step_name}")
                self.workflow_state['current_step'] = step_name
                
                # Handle different step types
                if step['type'] == 'bash':
                    success = self.run_bash_script(step['path'], step.get('args', []))
                elif step['type'] == 'python':
                    success, result_data = self.run_python_script(step['path'], step.get('args', []))
                    
                    # Handle special case: need more bins for cell grouping
                    if result_data.get('needs_more_bins', False):
                        logger.info(f"Step {step_name} indicated need for more bins. Going back to group_cells step.")
                        
                        # Find the group_cells step and restart from there
                        group_cells_index = None
                        for j, prev_step in enumerate(steps):
                            if prev_step['name'] == 'group_cells':
                                group_cells_index = j
                                break
                        
                        if group_cells_index is not None:
                            logger.info(f"Restarting workflow from group_cells step (index {group_cells_index})")
                            # Update bins count to add one more bin
                            self.bins += 1
                            logger.info(f"Increased bin count to {self.bins}")
                            
                            # Update workflow state
                            self.workflow_state['bins'] = self.bins
                            self._save_state()
                            
                            # Restart from group_cells step
                            # We'll break out of the current loop and restart from group_cells
                            logger.info("Restarting from group_cells step with increased bin count")
                            return self._restart_from_step('group_cells')
                        else:
                            logger.error("Could not find group_cells step to restart from")
                            return False
                elif step['type'] == 'manual':
                    success = self.prompt_manual_step(step_name, step.get('instructions', ''))
                    
                    # Set up directories after specific manual steps
                    if success and step_name == 'select_condition' and self.selected_conditions:
                        if not self.setup_condition_directories():
                            logger.error("Failed to set up condition directories")
                            return False
                    elif success and step_name == 'select_timepoints' and self.timepoints:
                        if not self.setup_timepoint_directories():
                            logger.error("Failed to set up timepoint directories")
                            return False
                    elif success and step_name == 'select_analysis_channels' and self.analysis_channels:
                        # Set up final analysis directory structure after all selections are made
                        if not self.setup_analysis_directories():
                            logger.error("Failed to set up analysis directories")
                            return False
                else:
                    logger.error(f"Unknown step type: {step['type']}")
                    success = False
                
                if not success:
                    logger.error(f"Step {step_name} failed")
                    return False
                    
                self.workflow_state['steps_completed'].append(step_name)
                self._save_state()
                
            logger.info("Workflow completed successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error during workflow execution: {e}", exc_info=True)
            return False


def main():
    """Main entry point for the script."""
    parser = argparse.ArgumentParser(description='Microscopy Single-Cell Analysis Workflow Orchestrator')
    
    parser.add_argument('--config', '-c', default='config/config.json',
                        help='Path to workflow configuration file (JSON)')
    parser.add_argument('--input', '-i', required=True,
                        help='Input directory containing microscopy data to analyze')
    parser.add_argument('--output', '-o', required=True,
                        help='Output directory for results')
    parser.add_argument('--skip', '-s', nargs='+', default=[],
                        help='Steps to skip (by name)')
    parser.add_argument('--datatype', type=str, choices=['single_timepoint', 'multi_timepoint'],
                        help='Specify the data type (overrides manual selection)')
    parser.add_argument('--conditions', nargs='+', default=[],
                        help='Specific conditions to analyze (e.g., Dish_1 Dish_2)')
    parser.add_argument('--segmentation-channel', type=str,
                        help='Channel to use for cell segmentation (e.g., ch00)')
    parser.add_argument('--analysis-channels', nargs='+', default=[],
                        help='Channels to analyze (e.g., ch01 ch02 ch03)')
    parser.add_argument('--timepoints', '-t', nargs='+', default=[],
                        help='Specific timepoints to analyze (e.g., t00 t03)')
    parser.add_argument('--regions', '-r', nargs='+', default=[],
                        help='Specific regions to analyze (e.g., R_1 R_2 R_3)')
    parser.add_argument('--bins', type=int, default=5,
                        help='Number of bins for grouping cells (default: 5)')
    parser.add_argument('--setup-only', action='store_true',
                        help='Only set up directory structure, do not run the workflow')
    parser.add_argument('--start-from', type=str,
                        help='Start the workflow from this step (by name)')
    parser.add_argument('--verbose', action='store_true',
                        help='Enable verbose logging')
    parser.add_argument('--debug', action='store_true',
                        help='Enable debug logging (even more detailed)')
    
    args = parser.parse_args()
    
    # Configure logging based on verbosity level
    log_level = logging.INFO
    if args.verbose:
        log_level = logging.INFO  # We were already at INFO level for verbose
    if args.debug:
        log_level = logging.DEBUG
    
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Create and run the workflow orchestrator
    orchestrator = WorkflowOrchestrator(
        config_path=args.config,
        input_dir=args.input,
        output_dir=args.output,
        skip_steps=args.skip,
        datatype=args.datatype,
        conditions=args.conditions,
        segmentation_channel=args.segmentation_channel,
        analysis_channels=args.analysis_channels,
        timepoints=args.timepoints,
        regions=args.regions,
        setup_only=args.setup_only,
        start_from=args.start_from,
        bins=args.bins
    )
    
    # If only setting up directories, create just the base directories
    if args.setup_only:
        if orchestrator.setup_base_directories():
            logger.info("Base directory setup complete, stopping as --setup-only was specified")
            return 0
        else:
            logger.error("Failed to set up base directories")
            return 1
    
    # Run the workflow (which now handles directory creation in the proper sequence)
    if orchestrator.run_workflow():
        logger.info("Workflow completed successfully")
        return 0
    else:
        logger.error("Workflow failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())