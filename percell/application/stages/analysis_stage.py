"""
AnalysisStage - Application Layer Stage

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
        # Check required macro for analysis exists
        from percell.application.paths_api import path_exists
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
            
            # Step 1: Combine masks (migrated to application helper)
            self.logger.info("Combining masks...")
            from percell.application.image_processing_tasks import combine_masks as _combine_masks
            ok_combine = _combine_masks(
                input_dir=f"{output_dir}/grouped_masks",
                output_dir=f"{output_dir}/combined_masks",
                channels=data_selection.get('analysis_channels'),
                imgproc=kwargs.get('imgproc'),
            )
            if not ok_combine:
                self.logger.error("Failed to combine masks (no output written)")
                return False
            self.logger.info("Masks combined successfully")
            
            # Step 2: Create cell masks (migrated to application helper)
            self.logger.info("Creating cell masks...")
            from percell.application.imagej_tasks import create_cell_masks as _create_cell_masks
            from percell.application.paths_api import get_path_str
            ok_create = _create_cell_masks(
                roi_dir=f"{output_dir}/ROIs",
                mask_dir=f"{output_dir}/combined_masks",
                output_dir=f"{output_dir}/masks",
                imagej_path=self.config.get('imagej_path'),
                macro_path=get_path_str("create_cell_masks_macro"),
                channels=data_selection.get('analysis_channels'),
                auto_close=True,
                imagej=kwargs.get('imagej'),
            )
            if not ok_create:
                self.logger.error("Failed to create cell masks")
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
                channels=data_selection.get('analysis_channels'),
                max_files=9999999999999,  # Effectively no limit
                auto_close=True,
                imagej=kwargs.get('imagej'),
            )
            if not ok_analyze:
                self.logger.error("Failed to analyze cell masks")
                return False
            self.logger.info("Cell masks analyzed successfully")
            
            # Step 4: Include group metadata (migrated to application helper)
            self.logger.info("Including group metadata...")
            from percell.application.image_processing_tasks import include_group_metadata as _include
            ok_meta = _include(
                grouped_cells_dir=f"{output_dir}/grouped_cells",
                analysis_dir=f"{output_dir}/analysis",
                output_dir=f"{output_dir}/analysis",
                overwrite=True,
                replace=True,
                channels=data_selection.get('analysis_channels'),
            )
            if not ok_meta:
                self.logger.error("Failed to include group metadata")
                return False
            self.logger.info("Group metadata included successfully")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error in Analysis Stage: {e}")
            return False


