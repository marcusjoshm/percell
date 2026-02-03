"""
Application Layer Stage Registration

Registers all available pipeline stages from application.stages package.
"""

from percell.application.stages_api import register_stage


def register_all_stages():
    """Register all available pipeline stages."""
    # Import stage classes from application.stages package
    from percell.application.stages import (
        DataSelectionStage,
        SegmentationStage,
        ProcessSingleCellDataStage,
        ThresholdGroupedCellsStage,
        FullAutoThresholdGroupedCellsStage,
        MeasureROIAreaStage,
        AnalysisStage,
        CleanupStage,
        CompleteWorkflowStage,
    )
    # Import advanced workflow stage (interactive custom sequence)
    try:
        from percell.application.advanced_workflow import (
            AdvancedWorkflowStage  # type: ignore
        )
    except Exception:
        AdvancedWorkflowStage = None  # type: ignore

    # Complete workflow stage (executes all stages in sequence)
    register_stage('complete_workflow', order=0)(CompleteWorkflowStage)

    # Advanced workflow builder stage (custom sequence)
    if AdvancedWorkflowStage is not None:
        register_stage('advanced_workflow', order=1)(AdvancedWorkflowStage)

    # Core processing stages (in execution order)
    register_stage('data_selection', order=2)(DataSelectionStage)
    register_stage('cellpose_segmentation', order=3)(SegmentationStage)
    register_stage('process_cellpose_single_cell', order=4)(
        ProcessSingleCellDataStage
    )
    register_stage('semi_auto_threshold_grouped_cells', order=5)(
        ThresholdGroupedCellsStage
    )
    register_stage('full_auto_threshold_grouped_cells', order=6)(
        FullAutoThresholdGroupedCellsStage
    )
    register_stage('measure_roi_area', order=7)(MeasureROIAreaStage)
    register_stage('analysis', order=8)(AnalysisStage)
    register_stage('cleanup', order=9)(CleanupStage)
