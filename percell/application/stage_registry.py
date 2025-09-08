"""
Application Layer Stage Registration

Registers all available pipeline stages implemented in application.stage_classes.
"""

from percell.application.stages_api import register_stage


def register_all_stages():
    """Register all available pipeline stages."""
    # Import stage classes from application layer to avoid circular imports
    from percell.application.stage_classes import (
        DataSelectionStage,
        SegmentationStage,
        ProcessSingleCellDataStage,
        ThresholdGroupedCellsStage,
        MeasureROIAreaStage,
        AnalysisStage,
        CleanupStage,
        CompleteWorkflowStage,
    )

    # Complete workflow stage (executes all stages in sequence)
    register_stage('complete_workflow', order=0)(CompleteWorkflowStage)

    # Core processing stages (in execution order)
    register_stage('data_selection', order=1)(DataSelectionStage)
    register_stage('segmentation', order=2)(SegmentationStage)
    register_stage('process_single_cell', order=3)(ProcessSingleCellDataStage)
    register_stage('threshold_grouped_cells', order=4)(ThresholdGroupedCellsStage)
    register_stage('measure_roi_area', order=5)(MeasureROIAreaStage)
    register_stage('analysis', order=6)(AnalysisStage)
    register_stage('cleanup', order=7)(CleanupStage)


