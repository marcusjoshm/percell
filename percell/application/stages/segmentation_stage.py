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

    Handles image binning and segmentation using Cellpose.
    Supports both interactive GUI mode and headless automated mode.
    Includes: bin_images_for_segmentation, segmentation (GUI or headless)
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
                self.logger.error(
                    "No data selection information found in config"
                )
                return False

            # Get input and output directories
            input_dir = kwargs.get('input_dir')
            output_dir = kwargs.get('output_dir')

            if not input_dir or not output_dir:
                self.logger.error(
                    "Input and output directories are required"
                )
                return False

            # Check if headless mode is enabled
            headless_mode = self.config.get('segmentation.headless', False)
            self.logger.info(
                f"Segmentation mode: {'headless' if headless_mode else 'GUI'}"
            )

            # Step 1: Bin images for segmentation
            self.logger.info("Binning images for segmentation...")
            from percell.application.image_processing_tasks import (
                bin_images as _bin_images
            )
            processed = _bin_images(
                input_dir=f"{output_dir}/raw_data",
                output_dir=f"{output_dir}/preprocessed",
                bin_factor=4,
                conditions=data_selection.get('selected_conditions'),
                regions=data_selection.get('selected_regions'),
                timepoints=data_selection.get('selected_timepoints'),
                channels=(
                    [data_selection.get('segmentation_channel')]
                    if data_selection.get('segmentation_channel')
                    else None
                ),
                imgproc=kwargs.get('imgproc'),
            )
            if processed <= 0:
                self.logger.error(
                    "No images binned; check selection filters"
                )
                return False
            self.logger.info(f"Images binned: {processed} files")

            # Step 2: Run segmentation (GUI or headless)
            preprocessed_dir = f"{output_dir}/preprocessed"

            # Remove output_dir from kwargs to avoid duplication
            other_kwargs = {k: v for k, v in kwargs.items()
                          if k not in ['input_dir', 'output_dir']}

            if headless_mode:
                return self._run_headless_segmentation(
                    preprocessed_dir=preprocessed_dir,
                    output_dir=output_dir,
                    **other_kwargs
                )
            else:
                return self._run_gui_segmentation(
                    preprocessed_dir=preprocessed_dir,
                    output_dir=output_dir,
                    **other_kwargs
                )

        except Exception as e:
            self.logger.error(f"Error in Segmentation Stage: {e}")
            return False

    def _run_headless_segmentation(
        self,
        preprocessed_dir: str,
        output_dir: str,
        **kwargs
    ) -> bool:
        """Run automated headless segmentation."""
        self.logger.info("Running headless Cellpose segmentation...")

        # Get segmentation parameters from config
        model_type = self.config.get('segmentation.model_type', 'cyto2')
        diameter = self.config.get('segmentation.diameter', 30.0)
        flow_threshold = self.config.get(
            'segmentation.flow_threshold', 0.4
        )
        cellprob_threshold = self.config.get(
            'segmentation.cellprob_threshold', 0.0
        )
        min_area = self.config.get('segmentation.min_area', 10)
        use_gpu = self.config.get('segmentation.use_gpu', False)

        self.logger.info(f"Model: {model_type}, Diameter: {diameter}")
        self.logger.info(
            f"Thresholds: flow={flow_threshold}, "
            f"cellprob={cellprob_threshold}"
        )

        # Get or create headless adapter
        from percell.adapters.headless_cellpose_adapter import (
            HeadlessCellposeAdapter
        )
        from percell.domain.models import SegmentationParameters
        from percell.application.paths_api import get_path_config

        project_root = get_path_config().get_project_root()
        cellpose_python = self.config.get('cellpose_path')

        if Path(cellpose_python).is_absolute():
            cellpose_path = Path(cellpose_python)
        else:
            cellpose_path = project_root / cellpose_python

        adapter = HeadlessCellposeAdapter(cellpose_path)

        # Check dependencies
        if not adapter.check_dependencies():
            self.logger.error(
                "Headless segmentation dependencies not installed. "
                "Install with: pip install cellpose roifile "
                "scikit-image tifffile"
            )
            return False

        # Find images to segment
        preproc_path = Path(preprocessed_dir)
        images = list(preproc_path.glob("**/*.tif"))
        images.extend(list(preproc_path.glob("**/*.tiff")))

        if not images:
            self.logger.error(f"No images found in {preprocessed_dir}")
            return False

        self.logger.info(f"Found {len(images)} images to segment")

        # Run segmentation
        params = SegmentationParameters(
            cell_diameter=diameter,
            flow_threshold=flow_threshold,
            probability_threshold=cellprob_threshold,
            model_type=model_type,
        )

        # Save ROIs in preprocessed directory (same location as binned images)
        # The resize_rois step will pick them up and move to ROIs directory
        roi_files = adapter.run_segmentation(
            images=images,
            output_dir=Path(preprocessed_dir),
            params=params,
            gpu=use_gpu,
            min_area=min_area,
            save_masks=True,
        )

        if not roi_files:
            self.logger.error("No ROI files generated")
            return False

        self.logger.info(
            f"Headless segmentation complete: {len(roi_files)} ROI files"
        )
        return True

    def _run_gui_segmentation(
        self,
        preprocessed_dir: str,
        output_dir: str,
        **kwargs
    ) -> bool:
        """Run interactive GUI-based segmentation."""
        self.logger.info("Launching interactive segmentation...")

        cellpose_adapter = kwargs.get('cellpose')
        cellpose_python = self.config.get('cellpose_path')

        if cellpose_adapter is not None or cellpose_python:
            from percell.domain.models import SegmentationParameters
            adapter = cellpose_adapter

            if adapter is None:
                from percell.adapters.cellpose_subprocess_adapter import (
                    CellposeSubprocessAdapter
                )
                from percell.application.paths_api import get_path_config

                project_root = get_path_config().get_project_root()
                if Path(cellpose_python).is_absolute():
                    cellpose_path = Path(cellpose_python)
                else:
                    cellpose_path = project_root / cellpose_python

                self.logger.info(f"Cellpose path: {cellpose_path}")
                adapter = CellposeSubprocessAdapter(cellpose_path)

            self.logger.info("Launching Cellpose GUI...")
            # Launch GUI and wait for user to complete segmentation
            from pathlib import Path as _P
            adapter.run_segmentation(
                [],
                _P(f"{output_dir}/combined_masks"),
                SegmentationParameters(0, 0, 0, "nuclei")
            )
            self.logger.info("Cellpose GUI closed by user")
        else:
            # Fallback to interactive tools script
            self.logger.info("Launching segmentation tools script...")
            from percell.application.paths_api import get_path
            seg_script_path = get_path("launch_segmentation_tools_script")

            # Make script executable
            fs_port = getattr(self, '_fs', None)
            try:
                if fs_port is not None:
                    fs_port.ensure_executable(
                        get_path("launch_segmentation_tools_script")
                    )
                else:
                    from percell.adapters.local_filesystem_adapter import (
                        LocalFileSystemAdapter
                    )
                    LocalFileSystemAdapter().ensure_executable(
                        get_path("launch_segmentation_tools_script")
                    )
            except Exception:
                pass

            self.logger.info("Starting interactive segmentation...")
            self.logger.info(
                "Complete segmentation and press Enter when done."
            )
            result = subprocess.run(
                [str(seg_script_path), preprocessed_dir],
                stdin=sys.stdin,
                stdout=sys.stdout,
                stderr=sys.stderr
            )
            if result.returncode != 0:
                self.logger.error(
                    f"Segmentation tools failed: {result.returncode}"
                )
                return False

            self.logger.info("Segmentation tools completed")

        return True


