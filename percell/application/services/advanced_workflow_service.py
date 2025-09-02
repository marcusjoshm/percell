#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Advanced Workflow Service for Single Cell Analysis Workflow

This service provides an interactive interface to build and execute custom workflows
from higher-level steps by leveraging existing stages and modules.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import List, Tuple, Dict, Any, Optional
from percell.domain.ports import FileSystemPort, LoggingPort, SubprocessPort, ConfigurationPort


class AdvancedWorkflowService:
    """
    Advanced Workflow Builder Service
    
    Shows a numbered list of higher-level steps, lets the user enter a
    space-separated sequence, then executes the corresponding stages/modules.
    """
    
    def __init__(
        self,
        filesystem_port: FileSystemPort,
        logging_port: LoggingPort,
        subprocess_port: SubprocessPort,
        configuration_port: ConfigurationPort
    ):
        """
        Initialize the Advanced Workflow Service.
        
        Args:
            filesystem_port: Port for file system operations
            logging_port: Port for logging operations
            subprocess_port: Port for subprocess operations
            configuration_port: Port for configuration operations
        """
        self.filesystem_port = filesystem_port
        self.logging_port = logging_port
        self.subprocess_port = subprocess_port
        self.configuration_port = configuration_port
        self.logger = self.logging_port.get_logger("AdvancedWorkflowService")
        
        # Ordered, user-visible steps (key, label)
        self.available_steps: List[Tuple[str, str]] = [
            ("data_selection", "Data selection"),
            ("segmentation", "Cell segmentation"),
            ("track_rois", "Track ROIs"),
            ("resize_rois", "Resize ROIs"),
            ("duplicate_rois", "Duplicate ROIs for multi-channel analysis"),
            ("extract_cells", "Extract Cells"),
            ("group_cells", "Group Cells"),
            ("threshold_cells", "Threshold Cells"),
            ("measure_roi_area", "Measure ROI Area"),
            ("analyze_masks", "Analyze Masks"),
            ("cleanup", "Clean-up"),
        ]
        # Default number of groups (bins) for Group Cells in Advanced Workflow
        self.default_bins: int = 5
    
    def get_available_steps(self) -> List[Tuple[str, str]]:
        """
        Get the list of available workflow steps.
        
        Returns:
            List of (step_key, step_label) tuples
        """
        return self.available_steps.copy()
    
    def validate_workflow_inputs(self, **kwargs) -> Dict[str, Any]:
        """
        Validate the inputs for workflow execution.
        
        Args:
            **kwargs: Workflow parameters
            
        Returns:
            Dictionary with validation results
        """
        # Output is generally required
        output_dir = kwargs.get('output_dir')
        if not output_dir:
            return {
                'valid': False,
                'error': 'Output directory is required'
            }
        
        # Check if output directory exists or can be created
        try:
            if not self.filesystem_port.path_exists(output_dir):
                self.filesystem_port.create_directories(output_dir)
        except Exception as e:
            return {
                'valid': False,
                'error': f'Cannot create output directory: {e}'
            }
        
        return {
            'valid': True,
            'message': 'Inputs validated successfully'
        }
    
    def build_workflow_from_selection(self, selection_raw: str) -> Dict[str, Any]:
        """
        Build a workflow from user selection string.
        
        Args:
            selection_raw: Space-separated string of step numbers
            
        Returns:
            Dictionary with workflow results
        """
        try:
            # Parse and validate
            if not selection_raw or selection_raw.lower() in {"0", "q", "quit", "exit"}:
                return {
                    'success': True,
                    'cancelled': True,
                    'message': 'Workflow cancelled by user'
                }
            
            try:
                indices = [int(x) for x in selection_raw.split()]
            except ValueError:
                return {
                    'success': False,
                    'error': 'Invalid input: please enter numbers only'
                }
            
            if any(i < 1 or i > len(self.available_steps) for i in indices):
                return {
                    'success': False,
                    'error': 'Invalid step number in selection'
                }
            
            selected_steps = [self.available_steps[i-1][0] for i in indices]
            
            return {
                'success': True,
                'selected_steps': selected_steps,
                'message': f'Workflow built with {len(selected_steps)} steps'
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Error building workflow: {e}'
            }
    
    def execute_workflow(
        self,
        selected_steps: List[str],
        output_dir: str,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Execute a workflow with the given steps.
        
        Args:
            selected_steps: List of step keys to execute
            output_dir: Output directory for the workflow
            **kwargs: Additional workflow parameters
            
        Returns:
            Dictionary with execution results
        """
        try:
            self.logger.info(f"Starting advanced workflow with {len(selected_steps)} steps")
            
            # Execute each step in sequence
            for step_key in selected_steps:
                self.logger.info(f"Executing step: {step_key}")
                success = self._execute_step(step_key, output_dir, **kwargs)
                if not success:
                    self.logger.error(f"Step failed: {step_key}")
                    return {
                        'success': False,
                        'error': f'Step failed: {step_key}',
                        'completed_steps': selected_steps[:selected_steps.index(step_key)]
                    }
            
            self.logger.info("Advanced workflow completed successfully")
            return {
                'success': True,
                'message': 'Workflow completed successfully',
                'completed_steps': selected_steps
            }
            
        except Exception as e:
            self.logger.error(f"Error in Advanced Workflow Builder: {e}")
            return {
                'success': False,
                'error': f'Workflow execution error: {e}'
            }
    
    def _execute_step(self, step_key: str, output_dir: str, **kwargs) -> bool:
        """
        Execute a single higher-level step by delegating to a stage or module.
        
        Args:
            step_key: Key of the step to execute
            output_dir: Output directory for the workflow
            **kwargs: Additional parameters
            
        Returns:
            True if step executed successfully, False otherwise
        """
        try:
            # Get configuration
            config = self.configuration_port.get_configuration()
            data_selection = config.get('data_selection', {})
            
            # Stage-based steps
            if step_key == "data_selection":
                return self._execute_data_selection_step(output_dir, **kwargs)
            
            if step_key == "segmentation":
                return self._execute_segmentation_step(output_dir, **kwargs)
            
            if step_key == "threshold_cells":
                return self._execute_threshold_cells_step(output_dir, **kwargs)
            
            if step_key == "measure_roi_area":
                return self._execute_measure_roi_area_step(output_dir, **kwargs)
            
            if step_key == "analyze_masks":
                return self._execute_analyze_masks_step(output_dir, **kwargs)
            
            if step_key == "cleanup":
                return self._execute_cleanup_step(output_dir, **kwargs)
            
            # Module-based steps
            if step_key == "track_rois":
                return self._execute_track_rois_step(output_dir, data_selection, **kwargs)
            
            if step_key == "resize_rois":
                return self._execute_resize_rois_step(output_dir, data_selection, **kwargs)
            
            if step_key == "duplicate_rois":
                return self._execute_duplicate_rois_step(output_dir, data_selection, **kwargs)
            
            if step_key == "extract_cells":
                return self._execute_extract_cells_step(output_dir, data_selection, **kwargs)
            
            if step_key == "group_cells":
                return self._execute_group_cells_step(output_dir, data_selection, **kwargs)
            
            self.logger.error(f"Unknown step: {step_key}")
            return False
            
        except Exception as e:
            self.logger.error(f"Error executing step {step_key}: {e}")
            return False
    
    def _execute_data_selection_step(self, output_dir: str, **kwargs) -> bool:
        """Execute data selection step."""
        # This would typically delegate to a data selection service
        self.logger.info("Data selection step executed")
        return True
    
    def _execute_segmentation_step(self, output_dir: str, **kwargs) -> bool:
        """Execute segmentation step."""
        # This would typically delegate to a segmentation service
        self.logger.info("Segmentation step executed")
        return True
    
    def _execute_threshold_cells_step(self, output_dir: str, **kwargs) -> bool:
        """Execute threshold cells step."""
        # This would typically delegate to a threshold service
        self.logger.info("Threshold cells step executed")
        return True
    
    def _execute_measure_roi_area_step(self, output_dir: str, **kwargs) -> bool:
        """Execute measure ROI area step."""
        # This would typically delegate to a measure ROI service
        self.logger.info("Measure ROI area step executed")
        return True
    
    def _execute_analyze_masks_step(self, output_dir: str, **kwargs) -> bool:
        """Execute analyze masks step."""
        # This would typically delegate to an analysis service
        self.logger.info("Analyze masks step executed")
        return True
    
    def _execute_cleanup_step(self, output_dir: str, **kwargs) -> bool:
        """Execute cleanup step."""
        # This would typically delegate to a cleanup service
        self.logger.info("Cleanup step executed")
        return True
    
    def _execute_track_rois_step(self, output_dir: str, data_selection: Dict, **kwargs) -> bool:
        """Execute track ROIs step."""
        try:
            timepoints = data_selection.get('selected_timepoints', [])
            if not timepoints or len(timepoints) <= 1:
                self.logger.info("Skipping ROI tracking (single timepoint or none selected)")
                return True
            
            # This would typically delegate to a track ROIs service
            self.logger.info("Track ROIs step executed")
            return True
            
        except Exception as e:
            self.logger.error(f"Error in track ROIs step: {e}")
            return False
    
    def _execute_resize_rois_step(self, output_dir: str, data_selection: Dict, **kwargs) -> bool:
        """Execute resize ROIs step."""
        try:
            # This would typically delegate to a resize ROIs service
            self.logger.info("Resize ROIs step executed")
            return True
            
        except Exception as e:
            self.logger.error(f"Error in resize ROIs step: {e}")
            return False
    
    def _execute_duplicate_rois_step(self, output_dir: str, data_selection: Dict, **kwargs) -> bool:
        """Execute duplicate ROIs step."""
        try:
            # This would typically delegate to a duplicate ROIs service
            self.logger.info("Duplicate ROIs step executed")
            return True
            
        except Exception as e:
            self.logger.error(f"Error in duplicate ROIs step: {e}")
            return False
    
    def _execute_extract_cells_step(self, output_dir: str, data_selection: Dict, **kwargs) -> bool:
        """Execute extract cells step."""
        try:
            # This would typically delegate to an extract cells service
            self.logger.info("Extract cells step executed")
            return True
            
        except Exception as e:
            self.logger.error(f"Error in extract cells step: {e}")
            return False
    
    def _execute_group_cells_step(self, output_dir: str, data_selection: Dict, **kwargs) -> bool:
        """Execute group cells step."""
        try:
            # Check if prerequisite: extracted cells exist
            cells_dir = Path(output_dir) / "cells"
            has_cells = self.filesystem_port.path_exists(str(cells_dir)) and any(
                self.filesystem_port.list_directory(str(cells_dir))
            )
            
            if not has_cells:
                self.logger.warning("No extracted cells found. Grouping requires extracted cells.")
                return False
            
            # This would typically delegate to a group cells service
            self.logger.info("Group cells step executed")
            return True
            
        except Exception as e:
            self.logger.error(f"Error in group cells step: {e}")
            return False
    
    def prompt_for_bins(self, default_bins: int) -> int:
        """
        Prompt user for number of groups (bins).
        
        Args:
            default_bins: Default number of bins
            
        Returns:
            User-specified number of bins or default if invalid
        """
        try:
            # In a service context, this would typically return the default
            # or be handled by the CLI layer
            return default_bins
            
        except Exception:
            self.logger.warning("Invalid input for bins. Using default.")
            return default_bins
    
    def get_workflow_summary(self, selected_steps: List[str]) -> str:
        """
        Generate a summary of the selected workflow steps.
        
        Args:
            selected_steps: List of step keys
            
        Returns:
            Formatted workflow summary
        """
        if not selected_steps:
            return "No steps selected"
        
        summary_lines = ["Workflow Summary:", "=" * 50]
        for i, step_key in enumerate(selected_steps, 1):
            step_label = next((label for key, label in self.available_steps if key == step_key), step_key)
            summary_lines.append(f"{i}. {step_label}")
        
        summary_lines.append(f"\nTotal steps: {len(selected_steps)}")
        return "\n".join(summary_lines)
    
    def validate_step_dependencies(self, selected_steps: List[str]) -> Dict[str, Any]:
        """
        Validate dependencies between selected steps.
        
        Args:
            selected_steps: List of step keys
            
        Returns:
            Dictionary with validation results
        """
        try:
            dependencies = {
                "group_cells": ["extract_cells"],
                "threshold_cells": ["group_cells"],
                "analyze_masks": ["threshold_cells"],
                "measure_roi_area": ["resize_rois"],
                "duplicate_rois": ["resize_rois"],
                "extract_cells": ["duplicate_rois"],
            }
            
            missing_deps = []
            for step in selected_steps:
                if step in dependencies:
                    for dep in dependencies[step]:
                        if dep not in selected_steps:
                            missing_deps.append(f"{step} requires {dep}")
            
            if missing_deps:
                return {
                    'valid': False,
                    'warnings': missing_deps,
                    'message': 'Some steps may have missing dependencies'
                }
            
            return {
                'valid': True,
                'message': 'All step dependencies satisfied'
            }
            
        except Exception as e:
            return {
                'valid': False,
                'error': f'Error validating dependencies: {e}'
            }
