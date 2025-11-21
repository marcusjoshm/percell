"""
MeasureROIAreaStage - Application Layer Stage

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
from percell.domain.utils.filesystem_filters import is_system_hidden_file


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
                imagej=kwargs.get('imagej'),
            )
            
            if success:
                self.logger.info("ROI area measurement completed successfully")
                
                # Check if any CSV files were created in the analysis directory
                analysis_dir = Path(output_dir) / "analysis"
                # Filter out system metadata files
                csv_files = [cf for cf in analysis_dir.glob("*cell_area*.csv") if not is_system_hidden_file(cf)]
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


