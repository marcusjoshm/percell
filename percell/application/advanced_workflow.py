"""
Advanced Workflow Builder Stage (Application Layer)

Provides an interactive interface to build and execute
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
    space-separated sequence, then executes the corresponding stages.
    """

    def __init__(self, config, logger, stage_name: str = "advanced_workflow"):
        super().__init__(config, logger, stage_name)

        # Get workflow configuration for dynamic tool names
        from percell.domain.services import create_workflow_configuration_service
        workflow_config = create_workflow_configuration_service(config)

        # Ordered, user-visible steps (key, label) using configured tools
        self.available_steps: List[Tuple[str, str]] = [
            ("data_selection", "Data selection"),
            (workflow_config.get_segmentation_stage_name(),
             workflow_config.get_segmentation_display_name()),
            ("track_rois", "Track ROIs"),
            ("filter_edge_rois", "Filter Edge ROIs"),
            ("resize_rois", "Resize ROIs"),
            ("duplicate_rois", "Duplicate ROIs for multi-channel analysis"),
            ("extract_cells", "Extract Cells"),
            (workflow_config.get_grouping_stage_name(),
             workflow_config.get_grouping_display_name()),
            (workflow_config.get_thresholding_stage_name(),
             workflow_config.get_thresholding_display_name()),
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
        # Get workflow configuration for dynamic mappings
        from percell.domain.services import create_workflow_configuration_service
        workflow_config = create_workflow_configuration_service(self.config)

        # Dispatch table mapping step keys to handler methods
        step_handlers = {
            "data_selection": self._step_data_selection,
            workflow_config.get_segmentation_stage_name(): self._step_segmentation,
            workflow_config.get_grouping_stage_name(): self._step_group_cells,
            workflow_config.get_thresholding_stage_name(): self._step_threshold_cells,
            "measure_roi_area": self._step_measure_roi_area,
            "analyze_masks": self._step_analyze_masks,
            "cleanup": self._step_cleanup,
            "track_rois": self._step_track_rois,
            "filter_edge_rois": self._step_filter_edge_rois,
            "resize_rois": self._step_resize_rois,
            "duplicate_rois": self._step_duplicate_rois,
            "extract_cells": self._step_extract_cells,
        }

        handler = step_handlers.get(step_key)
        if handler is None:
            self.logger.error(f"Unknown step: {step_key}")
            return False

        return handler(registry, **kwargs)

    def _execute_stage(self, registry, stage_key: str, stage_name: str, **kwargs) -> bool:
        """Helper to execute a registered stage."""
        stage_class = registry.get_stage_class(stage_key)
        if not stage_class:
            self.logger.error(f"{stage_name} not registered")
            return False
        return stage_class(self.config, self.pipeline_logger, stage_key).execute(**kwargs)

    def _step_data_selection(self, registry, **kwargs) -> bool:
        return self._execute_stage(registry, 'data_selection', 'DataSelectionStage', **kwargs)

    def _step_segmentation(self, registry, **kwargs) -> bool:
        # Get configured segmentation stage
        from percell.domain.services import create_workflow_configuration_service
        workflow_config = create_workflow_configuration_service(self.config)
        stage_name = workflow_config.get_segmentation_stage_name()
        return self._execute_stage(registry, stage_name, 'SegmentationStage', **kwargs)

    def _step_threshold_cells(self, registry, **kwargs) -> bool:
        # Get configured thresholding stage
        from percell.domain.services import create_workflow_configuration_service
        workflow_config = create_workflow_configuration_service(self.config)
        stage_name = workflow_config.get_thresholding_stage_name()
        return self._execute_stage(
            registry, stage_name, 'ThresholdGroupedCellsStage', **kwargs
        )

    def _step_measure_roi_area(self, registry, **kwargs) -> bool:
        return self._execute_stage(registry, 'measure_roi_area', 'MeasureROIAreaStage', **kwargs)

    def _step_analyze_masks(self, registry, **kwargs) -> bool:
        return self._execute_stage(registry, 'analysis', 'AnalysisStage', **kwargs)

    def _step_cleanup(self, registry, **kwargs) -> bool:
        return self._execute_stage(registry, 'cleanup', 'CleanupStage', **kwargs)

    def _step_track_rois(self, registry, **kwargs) -> bool:
        data_selection = self.config.get('data_selection') or {}
        timepoints = data_selection.get('selected_timepoints', [])
        if not timepoints or len(timepoints) <= 1:
            self.logger.info("Skipping ROI tracking (single timepoint or none selected)")
            return True
        from percell.application.image_processing_tasks import track_rois as _track
        output_dir = kwargs.get('output_dir')
        return _track(
            input_dir=f"{output_dir}/preprocessed", timepoints=timepoints, recursive=True
        )

    def _step_filter_edge_rois(self, registry, **kwargs) -> bool:
        from percell.application.paths_api import get_path_str
        data_selection = self.config.get('data_selection') or {}
        output_dir = kwargs.get('output_dir')
        edge_margin = self._prompt_for_edge_margin()
        from percell.application.imagej_tasks import filter_edge_rois as _filter_edge_rois
        ok = _filter_edge_rois(
            input_dir=f"{output_dir}/preprocessed",
            output_dir=f"{output_dir}/preprocessed_filtered",
            imagej_path=self.config.get('imagej_path'),
            channel=data_selection.get('segmentation_channel', ''),
            macro_path=get_path_str("filter_edge_rois_macro"),
            edge_margin=edge_margin,
            auto_close=True,
        )
        if not ok:
            self.logger.error("filter_edge_rois failed")
        return ok

    def _step_resize_rois(self, registry, **kwargs) -> bool:
        from percell.application.paths_api import get_path_str
        data_selection = self.config.get('data_selection') or {}
        output_dir = kwargs.get('output_dir')
        # Use filtered ROIs if available, otherwise use preprocessed
        filtered_dir = Path(output_dir) / "preprocessed_filtered"
        if filtered_dir.exists() and any(filtered_dir.rglob("*_rois.zip")):
            input_dir = str(filtered_dir)
            self.logger.info("Using filtered ROIs from preprocessed_filtered/")
        else:
            input_dir = f"{output_dir}/preprocessed"
            self.logger.info("Using ROIs from preprocessed/ (no filtered ROIs found)")
        from percell.application.imagej_tasks import resize_rois as _resize_rois
        ok = _resize_rois(
            input_dir=input_dir,
            output_dir=f"{output_dir}/ROIs",
            imagej_path=self.config.get('imagej_path'),
            channel=data_selection.get('segmentation_channel', ''),
            macro_path=get_path_str("resize_rois_macro"),
            auto_close=True,
        )
        if not ok:
            self.logger.error("resize_rois failed")
        return ok

    def _step_duplicate_rois(self, registry, **kwargs) -> bool:
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

    def _step_extract_cells(self, registry, **kwargs) -> bool:
        from percell.application.paths_api import get_path_str
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

    def _step_group_cells(self, registry, **kwargs) -> bool:
        data_selection = self.config.get('data_selection') or {}
        output_dir = kwargs.get('output_dir')
        channels = data_selection.get('analysis_channels', [])

        if not self._ensure_extracted_cells_exist(registry, **kwargs):
            return False

        # Check which grouping tool is configured
        from percell.domain.services import create_workflow_configuration_service
        workflow_config = create_workflow_configuration_service(self.config)
        grouping_tool = workflow_config.get_grouping_tool()

        if grouping_tool == 'auc_auto_groups':
            # Auto-grouping with GMM clustering by AUC (total intensity)
            max_clusters = self._prompt_for_max_clusters(
                default_max=10, metric_name="AUC (total intensity)"
            )
            from percell.application.image_processing_tasks import (
                group_cells_auto as _group_cells_auto
            )
            ok = _group_cells_auto(
                cells_dir=f"{output_dir}/cells",
                output_dir=f"{output_dir}/grouped_cells",
                max_clusters=max_clusters,
                channels=channels,
            )
            if not ok:
                self.logger.error("group_cells_auto failed")
            return ok
        elif grouping_tool == 'mean_auto_groups':
            # Auto-grouping with GMM clustering by mean intensity
            max_clusters = self._prompt_for_max_clusters(
                default_max=10, metric_name="mean intensity"
            )
            from percell.application.image_processing_tasks import (
                group_cells_mean_auto as _group_cells_mean_auto
            )
            ok = _group_cells_mean_auto(
                cells_dir=f"{output_dir}/cells",
                output_dir=f"{output_dir}/grouped_cells",
                max_clusters=max_clusters,
                channels=channels,
            )
            if not ok:
                self.logger.error("group_cells_mean_auto failed")
            return ok
        elif grouping_tool == 'max_auto_groups':
            # Auto-grouping with GMM clustering by max intensity
            max_clusters = self._prompt_for_max_clusters(
                default_max=10, metric_name="max intensity (peak)"
            )
            from percell.application.image_processing_tasks import (
                group_cells_max_auto as _group_cells_max_auto
            )
            ok = _group_cells_max_auto(
                cells_dir=f"{output_dir}/cells",
                output_dir=f"{output_dir}/grouped_cells",
                max_clusters=max_clusters,
                channels=channels,
            )
            if not ok:
                self.logger.error("group_cells_max_auto failed")
            return ok
        elif grouping_tool == 'sg_auto_groups':
            # Auto-grouping with GMM clustering by SG contrast ratio
            max_clusters = self._prompt_for_max_clusters(
                default_max=10, metric_name="SG contrast (95th/50th pctl)"
            )
            from percell.application.image_processing_tasks import (
                group_cells_sg_auto as _group_cells_sg_auto
            )
            ok = _group_cells_sg_auto(
                cells_dir=f"{output_dir}/cells",
                output_dir=f"{output_dir}/grouped_cells",
                max_clusters=max_clusters,
                channels=channels,
            )
            if not ok:
                self.logger.error("group_cells_sg_auto failed")
            return ok
        else:
            # Fixed bins grouping (auc_5_groups or default)
            current_default = kwargs.get('bins', self.default_bins)
            bins = self._prompt_for_bins(current_default)
            self.default_bins = bins

            from percell.application.image_processing_tasks import (
                group_cells as _group_cells
            )
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

    def _ensure_extracted_cells_exist(self, registry, **kwargs) -> bool:
        """Check for extracted cells; optionally run extract_cells if missing."""
        output_dir = kwargs.get('output_dir')
        cells_dir = Path(output_dir) / "cells"
        has_cells = cells_dir.exists() and any(cells_dir.rglob("*.tif"))
        if has_cells:
            return True

        self.logger.warning("No extracted cells found. Grouping requires extracted cells.")
        try:
            choice = input("Run 'Extract Cells' now? [Y/n]: ").strip().lower()
        except EOFError:
            choice = 'n'

        if choice not in ("", "y", "yes"):
            self.logger.error(
                "Cannot group without extracted cells. Aborting Group Cells step."
            )
            return False

        ok = self._step_extract_cells(registry, **kwargs)
        if not ok:
            self.logger.error("Extract Cells failed; cannot proceed to Group Cells")
            return False
        return True

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
            print(" Group Cells Configuration (Fixed Bins) ".center(80, '-'))
            print("-"*80)
            user_input = input(
                f"\n>>> Enter number of groups (bins) [default {default_bins}]: "
            ).strip()
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

    def _prompt_for_max_clusters(
        self, default_max: int = 10, metric_name: str = "intensity"
    ) -> int:
        """Prompt user for max clusters for GMM auto-grouping."""
        try:
            print("\n" + "-"*80)
            title = f" Auto-Grouping by {metric_name} (GMM) "
            print(title.center(80, '-'))
            print("-"*80)
            print(" GMM clustering will automatically determine the optimal "
                  "number of groups.")
            print(" You can set a maximum limit for the number of groups.")
            user_input = input(
                f"\n>>> Enter maximum number of groups [default {default_max}]: "
            ).strip()
            if not user_input:
                return default_max
            value = int(user_input)
            if value < 2:
                self.logger.warning(
                    "Max clusters must be at least 2. Using default."
                )
                return default_max
            return value
        except Exception:
            self.logger.warning("Invalid input for max clusters. Using default.")
            return default_max

    def _prompt_for_edge_margin(self, default_margin: int = 10) -> int:
        """Prompt user for edge margin in pixels; return validated int, default if blank."""
        try:
            print("\n" + "-"*80)
            print(" Filter Edge ROIs Configuration ".center(80, '-'))
            print("-"*80)
            print(" ROIs within this margin of the image edge will be excluded.")
            print(" Set to 0 to only exclude ROIs that directly touch the edge.")
            user_input = input(f"\n>>> Enter edge margin in pixels [default {default_margin}]: ").strip()
            if not user_input:
                return default_margin
            value = int(user_input)
            if value < 0:
                self.logger.warning("Edge margin cannot be negative. Using default.")
                return default_margin
            return value
        except Exception:
            self.logger.warning("Invalid input for edge margin. Using default.")
            return default_margin


