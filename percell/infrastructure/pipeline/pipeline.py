"""
Main Pipeline Orchestrator for Microscopy Single-Cell Analysis

Coordinates the execution of all pipeline stages based on user arguments.
"""

import os
import time
from pathlib import Path
from typing import Dict, List, Optional, Any
import argparse

from percell.infrastructure.configuration.config import Config
from percell.infrastructure.logging.logger import PipelineLogger
from percell.infrastructure.stages.stages import get_stage_registry, StageExecutor
try:
    from percell.services.event_bus import PipelineEventBus
except Exception:  # pragma: no cover - optional during transition
    PipelineEventBus = None  # type: ignore
try:
    from percell.services.plugin_manager import PluginManager
    from percell.plugins.registry import register_all_plugins
    from percell.domain.plugin import AnalysisContext
except Exception:
    PluginManager = None  # type: ignore
    register_all_plugins = None  # type: ignore
    AnalysisContext = None  # type: ignore
try:
    from percell.services.factory import ServiceFactory
except Exception:
    ServiceFactory = None  # type: ignore


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
        
        # Optional event bus for decoupled notifications
        self.event_bus = PipelineEventBus() if PipelineEventBus is not None else None

        # Create stage executor
        self.registry = get_stage_registry()
        self.executor = StageExecutor(config, logger, self.registry, event_bus=self.event_bus)

        # Optional plugin manager for future plugin-based execution
        self.plugin_manager = PluginManager() if PluginManager is not None else None
        if self.plugin_manager and register_all_plugins:
            try:
                register_all_plugins(self.plugin_manager)
                self.logger.debug(f"Registered plugins: {self.plugin_manager.get_available_plugins()}")
            except Exception:
                pass

        # Optional service factory for shared services; bind to logger for discovery
        self.service_factory = ServiceFactory(self.config) if ServiceFactory is not None else None
        if self.service_factory is not None:
            try:
                setattr(self.logger, 'service_factory', self.service_factory)
            except Exception:
                pass

        # Try to get hexagonal workflow service for modern execution
        self.hexagonal_workflow_service = None
        try:
            from percell.main.composition_root import get_composition_root
            composition_root = get_composition_root()
            self.hexagonal_workflow_service = composition_root.get_service('hexagonal_workflow_service')
            if self.hexagonal_workflow_service:
                self.logger.info("Hexagonal workflow service available - using modern execution path")
            else:
                self.logger.info("Hexagonal workflow service not available - using legacy execution path")
        except Exception as e:
            self.logger.debug(f"Could not initialize hexagonal workflow service: {e}")
            self.logger.info("Using legacy execution path")

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
            
            # Try hexagonal execution first if available
            if self.hexagonal_workflow_service and self._can_use_hexagonal_execution():
                self.logger.info("Using hexagonal workflow service for execution")
                success = self._execute_with_hexagonal_service(pipeline_args)
            else:
                self.logger.info("Using legacy stage executor for execution")
                # Execute stages with legacy system
                success = self.executor.execute_stages(self.stages_to_run, **pipeline_args)
            
            if success:
                self.logger.info("Pipeline completed successfully")
                
                # Save execution summary
                self.logger.save_execution_summary()
                
                # Print execution summary
                if hasattr(self.executor, 'get_execution_summary'):
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

    def _can_use_hexagonal_execution(self) -> bool:
        """
        Check if we can use hexagonal execution for the selected stages.
        
        Returns:
            True if hexagonal execution is possible, False otherwise
        """
        # Check if all selected stages can be handled by hexagonal service
        hexagonal_stages = {
            'data_selection', 'segmentation', 'process_single_cell', 
            'threshold_grouped_cells', 'measure_roi_area', 'analysis', 'cleanup'
        }
        
        # Special handling for complete_workflow - expand it into component stages
        if 'complete_workflow' in self.stages_to_run:
            # For complete workflow, we can use hexagonal execution
            return True
        
        for stage in self.stages_to_run:
            if stage not in hexagonal_stages:
                self.logger.debug(f"Stage '{stage}' not supported by hexagonal service, using legacy execution")
                return False
        
        return True

    def _execute_with_hexagonal_service(self, pipeline_args: Dict[str, Any]) -> bool:
        """
        Execute the pipeline using the hexagonal workflow service.
        
        Args:
            pipeline_args: Pipeline arguments
            
        Returns:
            True if successful, False otherwise
        """
        try:
            self.logger.info("Executing with hexagonal workflow service")
            
            # Map pipeline arguments to hexagonal service parameters
            output_dir = pipeline_args['output_dir']
            conditions = pipeline_args.get('conditions', [])
            regions = pipeline_args.get('regions', [])
            timepoints = pipeline_args.get('timepoints', [])
            analysis_channels = pipeline_args.get('analysis_channels', [])
            segmentation_channel = pipeline_args.get('segmentation_channel', 'ch01')
            
            # Execute each stage using the hexagonal service
            for stage in self.stages_to_run:
                self.logger.info(f"Executing stage '{stage}' with hexagonal service")
                
                if stage == 'complete_workflow':
                    # Expand complete_workflow into its component stages
                    self.logger.info("Expanding complete_workflow into component stages")
                    component_stages = [
                        'data_selection', 'segmentation', 'process_single_cell',
                        'threshold_grouped_cells', 'measure_roi_area', 'analysis', 'cleanup'
                    ]
                    
                    for component_stage in component_stages:
                        self.logger.info(f"Executing component stage '{component_stage}'")
                        if not self._execute_component_stage(component_stage, pipeline_args):
                            return False
                    
                    self.logger.info("Complete workflow finished successfully")
                    return True
                    
                elif stage == 'data_selection':
                    # Data selection is already done by the pipeline setup
                    self.logger.info("Data selection stage completed (handled by pipeline setup)")
                    continue
                    
                elif stage == 'segmentation':
                    result = self.hexagonal_workflow_service.bin_images(
                        output_dir=output_dir,
                        conditions=conditions,
                        regions=regions,
                        timepoints=timepoints,
                        channels=[segmentation_channel]
                    )
                    if result != 0:
                        self.logger.error(f"Segmentation stage failed with code: {result}")
                        return False
                        
                elif stage == 'process_single_cell':
                    # This includes resize_rois, duplicate_rois, and extract_cells
                    result = self.hexagonal_workflow_service.resize_rois(output_dir)
                    if result != 0:
                        self.logger.error(f"Resize ROIs stage failed with code: {result}")
                        return False
                        
                    result = self.hexagonal_workflow_service.duplicate_rois_for_channels(
                        output_dir, conditions, regions, timepoints, segmentation_channel, analysis_channels
                    )
                    if result != 0:
                        self.logger.error(f"Duplicate ROIs stage failed with code: {result}")
                        return False
                        
                    result = self.hexagonal_workflow_service.extract_cells(
                        output_dir, conditions, regions, timepoints, analysis_channels
                    )
                    if result != 0:
                        self.logger.error(f"Extract cells stage failed with code: {result}")
                        return False
                        
                elif stage == 'threshold_grouped_cells':
                    result = self.hexagonal_workflow_service.threshold_grouped_cells(
                        output_dir, conditions, regions, timepoints, analysis_channels
                    )
                    if result != 0:
                        self.logger.error(f"Threshold grouped cells stage failed with code: {result}")
                        return False
                        
                elif stage == 'measure_roi_area':
                    result = self.hexagonal_workflow_service.measure_roi_area(output_dir)
                    if result != 0:
                        self.logger.error(f"Measure ROI area stage failed with code: {result}")
                        return False
                        
                elif stage == 'analysis':
                    result = self.hexagonal_workflow_service.analyze_cell_masks(output_dir)
                    if result != 0:
                        self.logger.error(f"Analysis stage failed with code: {result}")
                        return False
                        
                elif stage == 'cleanup':
                    result = self.hexagonal_workflow_service.cleanup_directories(output_dir)
                    if result != 0:
                        self.logger.error(f"Cleanup stage failed with code: {result}")
                        return False
                
                self.logger.info(f"Stage '{stage}' completed successfully")
            
            self.logger.info("All stages completed successfully with hexagonal service")
            return True
            
        except Exception as e:
            self.logger.error(f"Error in hexagonal execution: {e}")
            return False

    def _execute_component_stage(self, stage: str, pipeline_args: Dict[str, Any]) -> bool:
        """
        Execute a single component stage using the hexagonal workflow service.
        
        Args:
            stage: Stage name to execute
            pipeline_args: Pipeline arguments
            
        Returns:
            True if successful, False otherwise
        """
        try:
            output_dir = pipeline_args['output_dir']
            conditions = pipeline_args.get('conditions', [])
            regions = pipeline_args.get('regions', [])
            timepoints = pipeline_args.get('timepoints', [])
            analysis_channels = pipeline_args.get('analysis_channels', [])
            segmentation_channel = pipeline_args.get('segmentation_channel', 'ch01')
            
            if stage == 'data_selection':
                # Use the data selection service to actually perform data selection
                try:
                    from percell.main.composition_root import get_composition_root
                    composition_root = get_composition_root()
                    data_selection_service = composition_root.get_service('data_selection_service')
                    
                    if data_selection_service:
                        # Extract input_dir from pipeline_args to avoid duplicate parameter
                        input_dir = pipeline_args.get('input_dir', '')
                        # Remove input_dir from kwargs to avoid duplicate parameter
                        kwargs = {k: v for k, v in pipeline_args.items() if k != 'input_dir'}
                        
                        result = data_selection_service.execute_data_selection(
                            input_dir=input_dir,
                            output_dir=output_dir,
                            **kwargs
                        )
                        
                        if result.get('success'):
                            self.logger.info("Data selection stage completed successfully")
                            # Store the results for use by other stages
                            pipeline_args['data_selection_results'] = result
                            return True
                        else:
                            self.logger.error(f"Data selection failed: {result.get('error', 'Unknown error')}")
                            return False
                    else:
                        self.logger.error("Data selection service not available")
                        return False
                        
                except Exception as e:
                    self.logger.error(f"Error in data selection: {e}")
                    return False
                
            elif stage == 'segmentation':
                result = self.hexagonal_workflow_service.bin_images(
                    output_dir=output_dir,
                    conditions=conditions,
                    regions=regions,
                    timepoints=timepoints,
                    channels=[segmentation_channel]
                )
                if result != 0:
                    self.logger.error(f"Segmentation stage failed with code: {result}")
                    return False
                    
            elif stage == 'process_single_cell':
                # This includes resize_rois, duplicate_rois, and extract_cells
                result = self.hexagonal_workflow_service.resize_rois(output_dir)
                if result != 0:
                    self.logger.error(f"Resize ROIs stage failed with code: {result}")
                    return False
                    
                result = self.hexagonal_workflow_service.duplicate_rois_for_channels(
                    output_dir, conditions, regions, timepoints, segmentation_channel, analysis_channels
                )
                if result != 0:
                    self.logger.error(f"Duplicate ROIs stage failed with code: {result}")
                    return False
                    
                result = self.hexagonal_workflow_service.extract_cells(
                    output_dir, conditions, regions, timepoints, analysis_channels
                )
                if result != 0:
                    self.logger.error(f"Extract cells stage failed with code: {result}")
                    return False
                    
            elif stage == 'threshold_grouped_cells':
                result = self.hexagonal_workflow_service.threshold_grouped_cells(
                    output_dir, conditions, regions, timepoints, analysis_channels
                )
                if result != 0:
                    self.logger.error(f"Threshold grouped cells stage failed with code: {result}")
                    return False
                    
            elif stage == 'measure_roi_area':
                result = self.hexagonal_workflow_service.measure_roi_area(output_dir)
                if result != 0:
                    self.logger.error(f"Measure ROI area stage failed with code: {result}")
                    return False
                    
            elif stage == 'analysis':
                result = self.hexagonal_workflow_service.analyze_cell_masks(output_dir)
                if result != 0:
                    self.logger.error(f"Analysis stage failed with code: {result}")
                    return False
                    
            elif stage == 'cleanup':
                result = self.hexagonal_workflow_service.cleanup_directories(output_dir)
                if result != 0:
                    self.logger.error(f"Cleanup stage failed with code: {result}")
                    return False
            
            self.logger.info(f"Component stage '{stage}' completed successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Error executing component stage '{stage}': {e}")
            return False


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