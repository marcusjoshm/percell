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
    # Import advanced workflow stage (interactive custom sequence)
    try:
        from percell.application.advanced_workflow import AdvancedWorkflowStage  # type: ignore
    except Exception:
        AdvancedWorkflowStage = None  # type: ignore

    # Complete workflow stage (executes all stages in sequence)
    register_stage('complete_workflow', order=0)(CompleteWorkflowStage)

    # Advanced workflow builder stage (custom sequence)
    if AdvancedWorkflowStage is not None:
        register_stage('advanced_workflow', order=1)(AdvancedWorkflowStage)

    # Core processing stages (in execution order)
    register_stage('data_selection', order=2)(DataSelectionStage)
    register_stage('segmentation', order=3)(SegmentationStage)
    register_stage('process_single_cell', order=4)(ProcessSingleCellDataStage)
    register_stage('threshold_grouped_cells', order=5)(ThresholdGroupedCellsStage)
    register_stage('measure_roi_area', order=6)(MeasureROIAreaStage)
    register_stage('analysis', order=7)(AnalysisStage)
    register_stage('cleanup', order=8)(CleanupStage)


