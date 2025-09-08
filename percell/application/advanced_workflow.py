"""
Advanced Workflow Builder Stage (Application Layer)

Migrated from percell/modules/advanced_workflow.py to align with the
new architecture. Provides an interactive interface to build and execute
custom workflows by leveraging existing stages and application tasks.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import List, Tuple

from percell.application.progress_api import run_subprocess_with_spinner
from percell.application.stages_api import StageBase


class AdvancedWorkflowStage(StageBase):
    """
    Advanced Workflow Builder

    Shows a numbered list of higher-level steps, lets the user enter a
    space-separated sequence, then executes the corresponding stages/modules.
    """

    def __init__(self, config, logger, stage_name: str = "advanced_workflow"):
        super().__init__(config, logger, stage_name)

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

    def validate_inputs(self, **kwargs) -> bool:
        # Output is generally required
        output_dir = kwargs.get('output_dir')
        if not output_dir:
            self.logger.error("Output directory is required")
            return False
        return True

    def run(self, **kwargs) -> bool:
        from percell.application.stages_api import get_stage_registry
        registry = get_stage_registry()

        try:
            # 1) Show menu
            print("\n" + "="*80)
            print(" Advanced Workflow Builder ".center(80, '='))
            print("="*80)
            print(" ")
            print("0. Back to main menu")
            for idx, (step_key, step_label) in enumerate(self.available_steps, start=1):
                print(f"{idx}. {step_label}")

            print("\n" + "-"*80)
            print(" Enter a space-separated sequence of numbers to define your custom workflow ")
            print(" Example: 1 2 3 4 5 6 7 8 9 10 11 ")
            print(" Type 0 or Q to return to the main menu ")
            print("-"*80)

            # 2) Read user input
            selection_raw = input("\n>>> Custom workflow (space-separated numbers, or 0/Q to exit): ").strip().lower()
            if not selection_raw or selection_raw in {"0", "q", "quit", "exit"}:
                self.logger.info("Exiting Advanced Workflow to main menu")
                return True

            # 3) Parse and validate
            try:
                indices = [int(x) for x in selection_raw.split()]
            except ValueError:
                self.logger.error("Invalid input: please enter numbers only")
                return False

            if any(i < 1 or i > len(self.available_steps) for i in indices):
                self.logger.error("Invalid step number in selection")
                return False

            selected_steps = [self.available_steps[i-1][0] for i in indices]

            # 4) Execute
            for step_key in selected_steps:
                self.logger.info(f"Executing step: {step_key}")
                success = self._execute_step(step_key, registry, **kwargs)
                if not success:
                    self.logger.error(f"Step failed: {step_key}")
                    return False

            self.logger.info("Advanced workflow completed successfully")
            return True

        except Exception as e:
            self.logger.error(f"Error in Advanced Workflow Builder: {e}")
            return False

    def _execute_step(self, step_key: str, registry, **kwargs) -> bool:
        """Execute a single higher-level step by delegating to a stage or module."""

        # Stage-based steps
        if step_key == "data_selection":
            stage_class = registry.get_stage_class('data_selection')
            if not stage_class:
                self.logger.error("DataSelectionStage not registered")
                return False
            return stage_class(self.config, self.pipeline_logger, 'data_selection').execute(**kwargs)

        if step_key == "segmentation":
            stage_class = registry.get_stage_class('segmentation')
            if not stage_class:
                self.logger.error("SegmentationStage not registered")
                return False
            return stage_class(self.config, self.pipeline_logger, 'segmentation').execute(**kwargs)

        if step_key == "threshold_cells":
            stage_class = registry.get_stage_class('threshold_grouped_cells')
            if not stage_class:
                self.logger.error("ThresholdGroupedCellsStage not registered")
                return False
            return stage_class(self.config, self.pipeline_logger, 'threshold_grouped_cells').execute(**kwargs)

        if step_key == "measure_roi_area":
            stage_class = registry.get_stage_class('measure_roi_area')
            if not stage_class:
                self.logger.error("MeasureROIAreaStage not registered")
                return False
            return stage_class(self.config, self.pipeline_logger, 'measure_roi_area').execute(**kwargs)

        if step_key == "analyze_masks":
            stage_class = registry.get_stage_class('analysis')
            if not stage_class:
                self.logger.error("AnalysisStage not registered")
                return False
            return stage_class(self.config, self.pipeline_logger, 'analysis').execute(**kwargs)

        if step_key == "cleanup":
            stage_class = registry.get_stage_class('cleanup')
            if not stage_class:
                self.logger.error("CleanupStage not registered")
                return False
            return stage_class(self.config, self.pipeline_logger, 'cleanup').execute(**kwargs)

        # Application-task steps
        from percell.application.paths_api import get_path, get_path_str

        if step_key == "track_rois":
            data_selection = self.config.get('data_selection') or {}
            timepoints = data_selection.get('selected_timepoints', [])
            if not timepoints or len(timepoints) <= 1:
                self.logger.info("Skipping ROI tracking (single timepoint or none selected)")
                return True
            from percell.application.image_processing_tasks import track_rois as _track
            output_dir = kwargs.get('output_dir')
            return _track(input_dir=f"{output_dir}/preprocessed", timepoints=timepoints, recursive=True)

        if step_key == "resize_rois":
            data_selection = self.config.get('data_selection') or {}
            output_dir = kwargs.get('output_dir')
            from percell.application.imagej_tasks import resize_rois as _resize_rois
            ok = _resize_rois(
                input_dir=f"{output_dir}/preprocessed",
                output_dir=f"{output_dir}/ROIs",
                imagej_path=self.config.get('imagej_path'),
                channel=data_selection.get('segmentation_channel', ''),
                macro_path=get_path_str("resize_rois_macro"),
                auto_close=True,
            )
            if not ok:
                self.logger.error("resize_rois failed")
            return ok

        if step_key == "duplicate_rois":
            data_selection = self.config.get('data_selection') or {}
            output_dir = kwargs.get('output_dir')
            from percell.application.image_processing_tasks import duplicate_rois_for_channels as _dup
            ok = _dup(
                roi_dir=f"{output_dir}/ROIs",
                channels=data_selection.get('analysis_channels', []),
                verbose=True,
            )
            if not ok:
                self.logger.error("duplicate_rois failed")
            return ok

        if step_key == "extract_cells":
            data_selection = self.config.get('data_selection') or {}
            output_dir = kwargs.get('output_dir')
            channels = data_selection.get('analysis_channels', [])
            from percell.application.imagej_tasks import extract_cells as _extract_cells
            ok = _extract_cells(
                roi_dir=f"{output_dir}/ROIs",
                raw_data_dir=f"{output_dir}/raw_data",
                output_dir=f"{output_dir}/cells",
                imagej_path=self.config.get('imagej_path'),
                macro_path=get_path_str("extract_cells_macro"),
                channels=channels,
                auto_close=True,
            )
            if not ok:
                self.logger.error("extract_cells failed")
            return ok

        if step_key == "group_cells":
            data_selection = self.config.get('data_selection') or {}
            output_dir = kwargs.get('output_dir')
            channels = data_selection.get('analysis_channels', [])
            # Allow the user to override and set the default bins for this Advanced session
            current_default = kwargs.get('bins', self.default_bins)
            bins = self._prompt_for_bins(current_default)
            # Persist chosen bins as new default for subsequent Group Cells steps in this Advanced session
            self.default_bins = bins
            # Ensure prerequisite: extracted cells exist
            cells_dir = Path(output_dir) / "cells"
            has_cells = cells_dir.exists() and any(cells_dir.rglob("*.tif"))
            if not has_cells:
                self.logger.warning("No extracted cells found. Grouping requires extracted cells.")
                try:
                    choice = input("Run 'Extract Cells' now? [Y/n]: ").strip().lower()
                except EOFError:
                    choice = 'n'
                if choice in ("", "y", "yes"):
                    # Attempt to run extract_cells step automatically
                    ok = self._execute_step("extract_cells", registry, **kwargs)
                    if not ok:
                        self.logger.error("Extract Cells failed; cannot proceed to Group Cells")
                        return False
                else:
                    self.logger.error("Cannot group without extracted cells. Aborting Group Cells step.")
                    return False
            from percell.application.image_processing_tasks import group_cells as _group_cells
            ok = _group_cells(
                cells_dir=f"{output_dir}/cells",
                output_dir=f"{output_dir}/grouped_cells",
                bins=int(bins),
                force_clusters=True,
                channels=channels,
            )
            if not ok:
                self.logger.error("group_cells failed")
            return ok

        self.logger.error(f"Unknown step: {step_key}")
        return False

    def _run_py_module(self, script_path: Path, args: List[str]) -> bool:
        try:
            # Show a spinner while running each module, using a very compact title for 80x24 terminal
            script_name = Path(script_path).stem  # Remove .py extension
            # Truncate to 15 chars max to minimize spacing
            title = script_name[:15] if len(script_name) > 15 else script_name
            result = run_subprocess_with_spinner([sys.executable, str(script_path)] + args, title=title)
            if result.returncode != 0:
                self.logger.error(result.stderr)
                return False
            self.logger.info(result.stdout)
            return True
        except Exception as e:
            self.logger.error(f"Error running module {script_path}: {e}")
            return False

    def _prompt_for_bins(self, default_bins: int) -> int:
        """Prompt user for number of groups (bins); return validated int, default if blank."""
        try:
            print("\n" + "-"*80)
            print(" Group Cells Configuration ".center(80, '-'))
            print("-"*80)
            user_input = input(f"\n>>> Enter number of groups (bins) [default {default_bins}]: ").strip()
            if not user_input:
                return default_bins
            value = int(user_input)
            if value <= 0:
                self.logger.warning("Bins must be a positive integer. Using default.")
                return default_bins
            return value
        except Exception:
            self.logger.warning("Invalid input for bins. Using default.")
            return default_bins


