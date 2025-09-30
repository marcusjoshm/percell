"""
ThresholdGroupedCellsStage - Application Layer Stage

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
        # Check required macro path exists
        from percell.application.paths_api import path_exists
        if not path_exists("threshold_grouped_cells_macro"):
            self.logger.error("Required macro not found: threshold_grouped_cells_macro")
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
            from percell.application.imagej_tasks import threshold_grouped_cells as _threshold
            from percell.application.paths_api import get_path_str
            ok_thresh = _threshold(
                input_dir=f"{output_dir}/grouped_cells",
                output_dir=f"{output_dir}/grouped_masks",
                imagej_path=self.config.get('imagej_path'),
                macro_path=get_path_str("threshold_grouped_cells_macro"),
                channels=data_selection.get('analysis_channels'),
                auto_close=True,
            )
            if not ok_thresh:
                self.logger.error("Failed to threshold grouped cells")
                return False
            self.logger.info("Grouped cells thresholded successfully")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error in Threshold Grouped Cells Stage: {e}")
            return False


