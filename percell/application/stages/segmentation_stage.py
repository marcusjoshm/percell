"""
SegmentationStage - Application Layer Stage

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
            
            # Step 1: Bin images for segmentation (migrated to application helper)
            self.logger.info("Binning images for segmentation...")
            from percell.application.image_processing_tasks import bin_images as _bin_images
            processed = _bin_images(
                input_dir=f"{output_dir}/raw_data",
                output_dir=f"{output_dir}/preprocessed",
                bin_factor=4,
                conditions=data_selection.get('selected_conditions'),
                regions=data_selection.get('selected_regions'),
                timepoints=data_selection.get('selected_timepoints'),
                channels=[data_selection.get('segmentation_channel')] if data_selection.get('segmentation_channel') else None,
                imgproc=kwargs.get('imgproc'),
            )
            if processed <= 0:
                self.logger.error("No images binned; check selection filters and input data")
                return False
            self.logger.info(f"Images binned successfully: {processed} files")
            
            # Step 2: Launch segmentation (interactive Cellpose GUI only)
            preprocessed_dir = f"{output_dir}/preprocessed"
            cellpose_adapter = kwargs.get('cellpose')
            cellpose_python = self.config.get('cellpose_path')
            if cellpose_adapter is not None or cellpose_python:
                from percell.domain.models import SegmentationParameters
                adapter = cellpose_adapter
                if adapter is None:
                    from percell.adapters.cellpose_subprocess_adapter import CellposeSubprocessAdapter  # type: ignore
                    # Resolve cellpose path relative to project root if it's a relative path
                    from percell.application.paths_api import get_path_config
                    project_root = get_path_config().get_project_root()
                    if Path(cellpose_python).is_absolute():
                        cellpose_path = Path(cellpose_python)
                    else:
                        cellpose_path = project_root / cellpose_python
                    self.logger.info(f"Resolved cellpose path: {cellpose_path}")
                    self.logger.info(f"Cellpose path exists: {cellpose_path.exists()}")
                    adapter = CellposeSubprocessAdapter(cellpose_path)
                self.logger.info("Launching Cellpose GUI (python -m cellpose) — no directories passed")
                # Launch GUI and wait for user to complete segmentation, then close
                from pathlib import Path as _P
                adapter.run_segmentation([], _P(f"{output_dir}/combined_masks"), SegmentationParameters(0, 0, 0, "nuclei"))
                self.logger.info("Cellpose GUI closed by user")
            else:
                # Fallback to interactive tools script
                self.logger.info("Launching interactive segmentation tools...")
                from percell.application.paths_api import get_path
                seg_script_path = get_path("launch_segmentation_tools_script")
                # Make sure the script is executable (prefer injected filesystem port)
                fs_port = getattr(self, '_fs', None)
                try:
                    if fs_port is not None:
                        from percell.application.paths_api import get_path
                        fs_port.ensure_executable(get_path("launch_segmentation_tools_script"))
                    else:
                        from percell.adapters.local_filesystem_adapter import LocalFileSystemAdapter
                        from percell.application.paths_api import get_path
                        LocalFileSystemAdapter().ensure_executable(get_path("launch_segmentation_tools_script"))
                except Exception:
                    pass
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


