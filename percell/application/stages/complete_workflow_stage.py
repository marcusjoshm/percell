"""
CompleteWorkflowStage - Application Layer Stage

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


