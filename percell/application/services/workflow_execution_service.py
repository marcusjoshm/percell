#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Workflow Execution Service for Single Cell Analysis

This service handles the actual execution of analysis workflows using the hexagonal architecture services.
It replaces the old pipeline.py execution logic with a clean, service-based approach.
"""

import os
import time
import threading
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple, Callable
from percell.domain.ports import FileSystemPort, LoggingPort, ConfigurationPort


class WorkflowExecutionService:
    """
    Service for executing single-cell analysis workflows.
    
    This service coordinates the execution of workflow steps using the hexagonal
    architecture services, replacing the old stage-based execution system.
    """
    
    def __init__(
        self,
        filesystem_port: FileSystemPort,
        logging_port: LoggingPort,
        configuration_port: ConfigurationPort
    ):
        """
        Initialize the Workflow Execution Service.
        
        Args:
            filesystem_port: Port for file system operations
            logging_port: Port for logging operations
            configuration_port: Port for configuration operations
        """
        self.filesystem_port = filesystem_port
        self.logging_port = logging_port
        self.configuration_port = configuration_port
        self.logger = self.logging_port.get_logger("WorkflowExecutionService")
        
        # Execution state
        self.current_execution = None
        self.execution_lock = threading.Lock()
        self.execution_callbacks = {}
        
        # Register default step handlers
        self.register_step_handler('data_selection', self._execute_data_selection_step)
        self.register_step_handler('segmentation', self._execute_segmentation_step)
        self.register_step_handler('process_single_cell', self._execute_process_single_cell_step)
        self.register_step_handler('threshold_grouped_cells', self._execute_threshold_grouped_cells_step)
        self.register_step_handler('measure_roi_area', self._execute_measure_roi_area_step)
        self.register_step_handler('analysis', self._execute_analysis_step)
        self.register_step_handler('cleanup', self._execute_cleanup_step)
    
    def execute_workflow_step(
        self,
        step_id: str,
        input_dir: str,
        output_dir: str,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Execute a single workflow step.
        
        Args:
            step_id: ID of the step to execute
            input_dir: Input directory path
            output_dir: Output directory path
            **kwargs: Additional step parameters
            
        Returns:
            Dictionary with step execution results
        """
        try:
            step_start = time.time()
            self.logger.info(f"Executing workflow step: {step_id}")
            
            # Get step handler
            step_handler = self._get_step_handler(step_id)
            if not step_handler:
                return {
                    'success': False,
                    'error': f'No handler found for step: {step_id}'
                }
            
            # Execute the step
            step_result = step_handler(input_dir, output_dir, **kwargs)
            
            # Calculate duration
            duration = time.time() - step_start
            
            # Add execution metadata
            step_result['step_id'] = step_id
            step_result['duration'] = duration
            step_result['timestamp'] = time.time()
            
            if step_result['success']:
                self.logger.info(f"Step '{step_id}' completed successfully in {duration:.2f}s")
            else:
                self.logger.error(f"Step '{step_id}' failed after {duration:.2f}s: {step_result.get('error')}")
            
            return step_result
            
        except Exception as e:
            error_msg = f'Error executing step {step_id}: {e}'
            self.logger.error(error_msg)
            return {
                'success': False,
                'step_id': step_id,
                'error': error_msg,
                'duration': time.time() - step_start if 'step_start' in locals() else 0,
                'timestamp': time.time()
            }
    
    def execute_workflow_sequence(
        self,
        workflow_id: str,
        step_sequence: List[str],
        input_dir: str,
        output_dir: str,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Execute a sequence of workflow steps.
        
        Args:
            workflow_id: ID of the workflow being executed
            step_sequence: List of step IDs to execute in order
            input_dir: Input directory path
            output_dir: Output directory path
            **kwargs: Additional workflow parameters
            
        Returns:
            Dictionary with workflow execution results
        """
        try:
            with self.execution_lock:
                if self.current_execution:
                    return {
                        'success': False,
                        'error': 'Another workflow is currently executing'
                    }
                
                # Start execution
                execution_id = f"{workflow_id}_{int(time.time())}"
                self.current_execution = {
                    'id': execution_id,
                    'workflow_id': workflow_id,
                    'start_time': time.time(),
                    'status': 'running',
                    'current_step': None,
                    'steps_completed': [],
                    'steps_failed': [],
                    'total_duration': 0
                }
            
            self.logger.info(f"Starting workflow execution: {execution_id}")
            self.logger.info(f"Steps to execute: {', '.join(step_sequence)}")
            
            execution_results = {
                'execution_id': execution_id,
                'workflow_id': workflow_id,
                'start_time': self.current_execution['start_time'],
                'steps_completed': [],
                'steps_failed': [],
                'total_duration': 0,
                'success': False
            }
            
            # Execute each step in sequence
            for i, step_id in enumerate(step_sequence):
                with self.execution_lock:
                    if self.current_execution:
                        self.current_execution['current_step'] = step_id
                
                self.logger.info(f"Executing step {i+1}/{len(step_sequence)}: {step_id}")
                
                # Execute the step
                step_result = self.execute_workflow_step(
                    step_id, input_dir, output_dir, **kwargs
                )
                
                # Record result
                if step_result['success']:
                    execution_results['steps_completed'].append(step_result)
                    self.logger.info(f"Step '{step_id}' completed successfully")
                else:
                    execution_results['steps_failed'].append(step_result)
                    self.logger.error(f"Step '{step_id}' failed: {step_result.get('error')}")
                    
                    # Stop execution on first failure
                    break
            
            # Calculate total duration
            total_duration = time.time() - self.current_execution['start_time']
            execution_results['total_duration'] = total_duration
            
            # Determine overall success
            if not execution_results['steps_failed']:
                execution_results['success'] = True
                with self.execution_lock:
                    if self.current_execution:
                        self.current_execution['status'] = 'completed'
                self.logger.info(f"Workflow execution completed successfully in {total_duration:.2f}s")
            else:
                with self.execution_lock:
                    if self.current_execution:
                        self.current_execution['status'] = 'failed'
                self.logger.error(f"Workflow execution failed after {total_duration:.2f}s")
            
            # Clear current execution
            with self.execution_lock:
                self.current_execution = None
            
            return execution_results
            
        except Exception as e:
            error_msg = f'Error executing workflow sequence: {e}'
            self.logger.error(error_msg)
            
            # Clear current execution
            with self.execution_lock:
                self.current_execution = None
            
            return {
                'success': False,
                'error': error_msg,
                'total_duration': time.time() - self.current_execution['start_time'] if self.current_execution else 0
            }
    
    def execute_workflow_with_dependencies(
        self,
        workflow_id: str,
        input_dir: str,
        output_dir: str,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Execute a workflow with automatic dependency resolution.
        
        Args:
            workflow_id: ID of the workflow to execute
            input_dir: Input directory path
            output_dir: Output directory path
            **kwargs: Additional workflow parameters
            
        Returns:
            Dictionary with workflow execution results
        """
        try:
            # Get workflow definition (this would come from WorkflowDefinitionService)
            # For now, use a simple mapping
            workflow_steps = self._get_workflow_steps(workflow_id)
            if not workflow_steps:
                return {
                    'success': False,
                    'error': f'Workflow "{workflow_id}" not found'
                }
            
            # Execute the workflow
            return self.execute_workflow_sequence(
                workflow_id, workflow_steps, input_dir, output_dir, **kwargs
            )
            
        except Exception as e:
            error_msg = f'Error executing workflow with dependencies: {e}'
            self.logger.error(error_msg)
            return {
                'success': False,
                'error': error_msg
            }
    
    def get_execution_status(self) -> Optional[Dict[str, Any]]:
        """
        Get the status of the current workflow execution.
        
        Returns:
            Current execution status or None if no execution is running
        """
        with self.execution_lock:
            if self.current_execution:
                return self.current_execution.copy()
            return None
    
    def cancel_current_execution(self) -> Dict[str, Any]:
        """
        Cancel the currently running workflow execution.
        
        Returns:
            Dictionary with cancellation results
        """
        try:
            with self.execution_lock:
                if not self.current_execution:
                    return {
                        'success': False,
                        'error': 'No workflow execution is currently running'
                    }
                
                execution_id = self.current_execution['id']
                self.current_execution['status'] = 'cancelled'
                
                self.logger.info(f"Workflow execution {execution_id} cancelled by user")
                
                return {
                    'success': True,
                    'execution_id': execution_id,
                    'message': f'Workflow execution {execution_id} cancelled successfully'
                }
                
        except Exception as e:
            error_msg = f'Error cancelling workflow execution: {e}'
            self.logger.error(error_msg)
            return {
                'success': False,
                'error': error_msg
            }
    
    def register_step_handler(self, step_id: str, handler: Callable) -> None:
        """
        Register a handler function for a specific workflow step.
        
        Args:
            step_id: ID of the step
            handler: Function to handle step execution
        """
        self.execution_callbacks[step_id] = handler
        self.logger.info(f"Registered handler for step: {step_id}")
    
    def get_available_steps(self) -> List[str]:
        """
        Get list of available workflow steps.
        
        Returns:
            List of step IDs that have registered handlers
        """
        return list(self.execution_callbacks.keys())
    
    def _get_step_handler(self, step_id: str) -> Optional[Callable]:
        """
        Get the handler function for a specific step.
        
        Args:
            step_id: ID of the step
            
        Returns:
            Handler function or None if not found
        """
        return self.execution_callbacks.get(step_id)
    
    def _get_workflow_steps(self, workflow_id: str) -> List[str]:
        """
        Get the steps for a specific workflow.
        
        Args:
            workflow_id: ID of the workflow
            
        Returns:
            List of step IDs
        """
        # This would typically come from WorkflowDefinitionService
        # For now, use a simple mapping
        workflow_mappings = {
            'complete_analysis': [
                'data_selection',
                'segmentation',
                'process_single_cell',
                'threshold_grouped_cells',
                'measure_roi_area',
                'analysis',
                'cleanup'
            ],
            'segmentation_only': [
                'data_selection',
                'segmentation'
            ],
            'analysis_only': [
                'analysis'
            ],
            'cleanup_only': [
                'cleanup'
            ]
        }
        
        return workflow_mappings.get(workflow_id, [])
    
    def _execute_data_selection_step(self, input_dir: str, output_dir: str, **kwargs) -> Dict[str, Any]:
        """Execute data selection step."""
        try:
            # This would use the DirectoryManagementService
            # For now, return a placeholder
            return {
                'success': True,
                'message': 'Data selection step completed (placeholder)',
                'output': {
                    'conditions': kwargs.get('conditions', []),
                    'timepoints': kwargs.get('timepoints', []),
                    'regions': kwargs.get('regions', []),
                    'segmentation_channel': kwargs.get('segmentation_channel'),
                    'analysis_channels': kwargs.get('analysis_channels', [])
                }
            }
        except Exception as e:
            return {
                'success': False,
                'error': f'Data selection step failed: {e}'
            }
    
    def _execute_segmentation_step(self, input_dir: str, output_dir: str, **kwargs) -> Dict[str, Any]:
        """Execute segmentation step."""
        try:
            # This would use the BinImagesService and other relevant services
            # For now, return a placeholder
            return {
                'success': True,
                'message': 'Segmentation step completed (placeholder)',
                'output': {
                    'preprocessed_dir': os.path.join(output_dir, 'preprocessed'),
                    'roi_files': []
                }
            }
        except Exception as e:
            return {
                'success': False,
                'error': f'Segmentation step failed: {e}'
            }
    
    def _execute_process_single_cell_step(self, input_dir: str, output_dir: str, **kwargs) -> Dict[str, Any]:
        """Execute process single cell step."""
        try:
            # This would use multiple services: TrackROIsService, DuplicateROIsService, etc.
            # For now, return a placeholder
            return {
                'success': True,
                'message': 'Process single cell step completed (placeholder)',
                'output': {
                    'roi_dir': os.path.join(output_dir, 'ROIs'),
                    'cells_dir': os.path.join(output_dir, 'cells'),
                    'grouped_cells_dir': os.path.join(output_dir, 'grouped_cells')
                }
            }
        except Exception as e:
            return {
                'success': False,
                'error': f'Process single cell step failed: {e}'
            }
    
    def _execute_threshold_grouped_cells_step(self, input_dir: str, output_dir: str, **kwargs) -> Dict[str, Any]:
        """Execute threshold grouped cells step."""
        try:
            # This would use the InteractiveThresholdingService
            # For now, return a placeholder
            return {
                'success': True,
                'message': 'Threshold grouped cells step completed (placeholder)',
                'output': {
                    'grouped_masks_dir': os.path.join(output_dir, 'grouped_masks')
                }
            }
        except Exception as e:
            return {
                'success': False,
                'error': f'Threshold grouped cells step failed: {e}'
            }
    
    def _execute_measure_roi_area_step(self, input_dir: str, output_dir: str, **kwargs) -> Dict[str, Any]:
        """Execute measure ROI area step."""
        try:
            # This would use the MeasureROIAreaService
            # For now, return a placeholder
            return {
                'success': True,
                'message': 'Measure ROI area step completed (placeholder)',
                'output': {
                    'analysis_dir': os.path.join(output_dir, 'analysis')
                }
            }
        except Exception as e:
            return {
                'success': False,
                'error': f'Measure ROI area step failed: {e}'
            }
    
    def _execute_analysis_step(self, input_dir: str, output_dir: str, **kwargs) -> Dict[str, Any]:
        """Execute analysis step."""
        try:
            # This would use multiple services: CombineMasksService, CreateCellMasksService, etc.
            # For now, return a placeholder
            return {
                'success': True,
                'message': 'Analysis step completed (placeholder)',
                'output': {
                    'masks_dir': os.path.join(output_dir, 'masks'),
                    'combined_masks_dir': os.path.join(output_dir, 'combined_masks'),
                    'analysis_dir': os.path.join(output_dir, 'analysis')
                }
            }
        except Exception as e:
            return {
                'success': False,
                'error': f'Analysis step failed: {e}'
            }
    
    def _execute_cleanup_step(self, input_dir: str, output_dir: str, **kwargs) -> Dict[str, Any]:
        """Execute cleanup step."""
        try:
            # This would use the CleanupDirectoriesService
            # For now, return a placeholder
            return {
                'success': True,
                'message': 'Cleanup step completed (placeholder)',
                'output': {
                    'space_freed': '0 bytes',
                    'files_removed': 0
                }
            }
        except Exception as e:
            return {
                'success': False,
                'error': f'Cleanup step failed: {e}'
            }
    
        # Register default step handlers
        self.register_step_handler('data_selection', self._execute_data_selection_step)
        self.register_step_handler('segmentation', self._execute_segmentation_step)
        self.register_step_handler('process_single_cell', self._execute_process_single_cell_step)
        self.register_step_handler('threshold_grouped_cells', self._execute_threshold_grouped_cells_step)
        self.register_step_handler('measure_roi_area', self._execute_measure_roi_area_step)
        self.register_step_handler('analysis', self._execute_analysis_step)
        self.register_step_handler('cleanup', self._execute_cleanup_step)
