"""
Stage Registration Module for Microscopy Single-Cell Analysis

Registers all available pipeline stages and their implementations.
"""

from ..core.stages import register_stage


def register_all_stages():
    """Register all available pipeline stages."""
    
    # Import stage classes here to avoid circular imports
    from .stage_classes import (
        DataSelectionStage,
        SegmentationStage,
        ProcessSingleCellDataStage,
        ThresholdGroupedCellsStage,
        MeasureROIAreaStage,
        AnalysisStage
    )
    
    # Core processing stages (in execution order)
    register_stage('data_selection', order=1)(DataSelectionStage)
    register_stage('segmentation', order=2)(SegmentationStage)
    register_stage('process_single_cell', order=3)(ProcessSingleCellDataStage)
    register_stage('threshold_grouped_cells', order=4)(ThresholdGroupedCellsStage)
    register_stage('measure_roi_area', order=5)(MeasureROIAreaStage)
    register_stage('analysis', order=6)(AnalysisStage) 