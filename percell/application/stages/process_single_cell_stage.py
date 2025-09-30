"""
ProcessSingleCellDataStage - Application Layer Stage

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
        # No external script required anymore for tracking
        
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
                from percell.application.image_processing_tasks import track_rois as _track_rois
                ok_track = _track_rois(
                    input_dir=f"{output_dir}/preprocessed",
                    timepoints=timepoints,
                    recursive=True,
                )
                if not ok_track:
                    self.logger.error("Failed to track ROIs")
                    return False
                self.logger.info("ROI tracking completed successfully")
            else:
                self.logger.info("Skipping ROI tracking (single timepoint or no timepoints)")
            
            # Step 2: Resize ROIs (migrated from module to application helper)
            self.logger.info("Resizing ROIs...")
            from percell.application.paths_api import get_path_str
            from percell.application.imagej_tasks import resize_rois as _resize_rois
            ok_resize = _resize_rois(
                input_dir=f"{output_dir}/preprocessed",
                output_dir=f"{output_dir}/ROIs",
                imagej_path=self.config.get('imagej_path'),
                channel=data_selection.get('segmentation_channel', ''),
                macro_path=get_path_str("resize_rois_macro"),
                auto_close=True,
                imagej=kwargs.get('imagej'),
                fs=kwargs.get('fs'),
            )
            if not ok_resize:
                self.logger.error("Failed to resize ROIs")
                return False
            self.logger.info("ROIs resized successfully")
            
            # Step 3: Duplicate ROIs for analysis channels (migrated to application helper)
            self.logger.info("Duplicating ROIs for analysis channels...")
            from percell.application.image_processing_tasks import duplicate_rois_for_channels as _dup_rois
            ok_dup = _dup_rois(
                roi_dir=f"{output_dir}/ROIs",
                channels=data_selection.get('analysis_channels'),
                verbose=True,
            )
            if not ok_dup:
                self.logger.error("Failed to duplicate ROIs for requested channels")
                return False
            self.logger.info("ROIs duplicated successfully")
            
            # Step 4: Extract cells (migrated to application helper)
            self.logger.info("Extracting cells...")
            from percell.application.imagej_tasks import extract_cells as _extract_cells
            ok_extract = _extract_cells(
                roi_dir=f"{output_dir}/ROIs",
                raw_data_dir=f"{output_dir}/raw_data",
                output_dir=f"{output_dir}/cells",
                imagej_path=self.config.get('imagej_path'),
                macro_path=get_path_str("extract_cells_macro"),
                channels=data_selection.get('analysis_channels'),
                auto_close=True,
                imagej=kwargs.get('imagej'),
            )
            if not ok_extract:
                self.logger.error("Failed to extract cells")
                return False
            self.logger.info("Cells extracted successfully")
            
            # Step 5: Group cells (migrated to application helper)
            self.logger.info("Grouping cells...")
            from percell.application.image_processing_tasks import group_cells as _group_cells
            ok_group = _group_cells(
                cells_dir=f"{output_dir}/cells",
                output_dir=f"{output_dir}/grouped_cells",
                bins=int(kwargs.get('bins', 5)),
                force_clusters=True,
                channels=data_selection.get('analysis_channels'),
                imgproc=kwargs.get('imgproc'),
            )
            if not ok_group:
                self.logger.error("Failed to group cells")
                return False
            self.logger.info("Cells grouped successfully")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error in Process Single-cell Data Stage: {e}")
            return False


