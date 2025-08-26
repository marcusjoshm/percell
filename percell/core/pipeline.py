"""
Main Pipeline Orchestrator for Microscopy Single-Cell Analysis

Coordinates the execution of all pipeline stages based on user arguments.
"""

import os
import time
from pathlib import Path
from typing import Dict, List, Optional, Any
import argparse

from .config import Config
from .logger import PipelineLogger
from .stages import get_stage_registry, StageExecutor


class Pipeline:
    """
    Main pipeline orchestrator for microscopy single-cell analysis.
    
    Manages the overall workflow, directory setup, and stage execution.
    """
    
    def __init__(self, config: Config, logger: PipelineLogger, args: argparse.Namespace):
        """
        Initialize the pipeline.
        
        Args:
            config: Pipeline configuration
            logger: Pipeline logger
            args: Command line arguments
        """
        self.config = config
        self.logger = logger
        self.args = args
        
        # Setup directories
        self.setup_directories()
        
        # Register all available stages
        # register_all_stages() # This line is removed as per the edit hint
        
        # Create stage executor
        self.registry = get_stage_registry()
        self.executor = StageExecutor(config, logger, self.registry)
        
        # Determine which stages to run
        self.stages_to_run = self._determine_stages()
        
    def setup_directories(self) -> None:
        """Set up required output directories for the selected stages."""
        # Always create logs directory
        logs_dir = Path(self.args.output) / 'logs'
        logs_dir.mkdir(parents=True, exist_ok=True)
        self.logger.debug(f"Created directory: {logs_dir}")

        # Determine which directories are needed based on selected stages
        needed_dirs = {
            'preprocessed': Path(self.args.output) / 'preprocessed',
            'logs': logs_dir
        }
        
        # Create directories
        for name, path in needed_dirs.items():
            if name != 'logs':  # logs already created
                path.mkdir(parents=True, exist_ok=True)
                self.logger.debug(f"Created directory: {path}")
        
        self.directories = needed_dirs
    
    def _determine_stages(self) -> List[str]:
        """
        Determine which stages to run based on command line arguments.
        
        Returns:
            List of stage names to execute
        """
        stages = []
        
        # Handle complete workflow - if selected, run only the complete workflow stage
        if self.args.complete_workflow:
            stages.append('complete_workflow')
            return stages
        
        # Handle advanced workflow builder - single stage that orchestrates custom steps
        if getattr(self.args, 'advanced_workflow', False):
            stages.append('advanced_workflow')
            return stages
        
        # Add individual stages based on flags
        if self.args.data_selection:
            stages.append('data_selection')
            
        if self.args.segmentation:
            stages.append('segmentation')
            
        if self.args.process_single_cell:
            stages.append('process_single_cell')
            
        if self.args.threshold_grouped_cells:
            stages.append('threshold_grouped_cells')
            
        if self.args.measure_roi_area:
            stages.append('measure_roi_area')
            
        if self.args.analysis:
            stages.append('analysis')
            
        if self.args.cleanup:
            stages.append('cleanup')
        
        # Filter out skipped stages
        if self.args.skip_steps:
            stages = [s for s in stages if s not in self.args.skip_steps]
        
        # Start from specific stage if requested
        if self.args.start_from:
            try:
                start_index = stages.index(self.args.start_from)
                stages = stages[start_index:]
            except ValueError:
                self.logger.warning(f"Start stage '{self.args.start_from}' not found in pipeline")
        
        return stages
    
    def get_pipeline_arguments(self) -> Dict[str, Any]:
        """
        Get arguments for pipeline execution.
        
        Returns:
            Dictionary of pipeline arguments
        """
        return {
            'input_dir': self.args.input,
            'output_dir': self.args.output,
            'datatype': self.args.datatype,
            'conditions': self.args.conditions,
            'timepoints': self.args.timepoints,
            'regions': self.args.regions,
            'segmentation_channel': self.args.segmentation_channel,
            'analysis_channels': self.args.analysis_channels,
            'bins': self.args.bins,
            'directories': self.directories
        }
    
    def run(self) -> bool:
        """
        Run the pipeline.
        
        Returns:
            True if successful, False otherwise
        """
        try:
            self.logger.info("Starting microscopy single-cell analysis pipeline")
            self.logger.info(f"Stages to run: {', '.join(self.stages_to_run)}")
            
            # Get pipeline arguments
            pipeline_args = self.get_pipeline_arguments()
            
            # Execute stages
            success = self.executor.execute_stages(self.stages_to_run, **pipeline_args)
            
            if success:
                self.logger.info("Pipeline completed successfully")
                
                # Save execution summary
                self.logger.save_execution_summary()
                
                # Print execution summary
                summary = self.executor.get_execution_summary()
                self.logger.info(f"Execution summary:")
                self.logger.info(f"  Total stages: {summary['total_stages']}")
                self.logger.info(f"  Successful: {summary['successful_stages']}")
                self.logger.info(f"  Failed: {summary['failed_stages']}")
                self.logger.info(f"  Success rate: {summary['success_rate']:.1%}")
                self.logger.info(f"  Total duration: {summary['total_duration']:.2f}s")
                
            else:
                self.logger.error("Pipeline failed")
            
            return success
            
        except Exception as e:
            self.logger.error(f"Pipeline execution error: {e}")
            return False
    
    def get_available_stages(self) -> List[str]:
        """
        Get list of available stages.
        
        Returns:
            List of available stage names
        """
        return self.registry.get_available_stages()
    
    def get_stage_order(self) -> List[str]:
        """
        Get stages in execution order.
        
        Returns:
            List of stage names in order
        """
        return self.registry.get_stage_order()


def create_pipeline(config: Config, logger: PipelineLogger, args: argparse.Namespace) -> Pipeline:
    """
    Create a pipeline instance.
    
    Args:
        config: Pipeline configuration
        logger: Pipeline logger
        args: Command line arguments
        
    Returns:
        Pipeline instance
    """
    return Pipeline(config, logger, args) 