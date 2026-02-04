"""
Application Layer Pipeline Stages

This package contains individual stage implementations for the microscopy
single-cell analysis pipeline. Each stage is responsible for a specific
part of the analysis workflow.

Stages:
- DataSelectionStage: Handles selection of conditions, regions, timepoints, and channels
- SegmentationStage: Manages cell segmentation using Cellpose or similar tools
- ProcessSingleCellDataStage: Processes individual cell data extraction
- AUCGroupCellsStage: Groups cells by AUC intensity for batch thresholding
- ThresholdGroupedCellsStage: Handles thresholding for grouped cell analysis
- MeasureROIAreaStage: Measures regions of interest areas
- AnalysisStage: Performs final analysis and generates results
- CleanupStage: Cleans up intermediate files and directories
- CompleteWorkflowStage: Orchestrates the complete end-to-end workflow
"""

from __future__ import annotations

from percell.application.stages.data_selection_stage import DataSelectionStage
from percell.application.stages.segmentation_stage import SegmentationStage
from percell.application.stages.process_single_cell_stage import ProcessSingleCellDataStage
from percell.application.stages.auc_group_cells_stage import AUCGroupCellsStage
from percell.application.stages.threshold_grouped_cells_stage import ThresholdGroupedCellsStage
from percell.application.stages.full_auto_threshold_grouped_cells_stage import FullAutoThresholdGroupedCellsStage
from percell.application.stages.measure_roi_area_stage import MeasureROIAreaStage
from percell.application.stages.analysis_stage import AnalysisStage
from percell.application.stages.cleanup_stage import CleanupStage
from percell.application.stages.complete_workflow_stage import CompleteWorkflowStage

__all__ = [
    "DataSelectionStage",
    "SegmentationStage",
    "ProcessSingleCellDataStage",
    "AUCGroupCellsStage",
    "ThresholdGroupedCellsStage",
    "FullAutoThresholdGroupedCellsStage",
    "MeasureROIAreaStage",
    "AnalysisStage",
    "CleanupStage",
    "CompleteWorkflowStage",
]
