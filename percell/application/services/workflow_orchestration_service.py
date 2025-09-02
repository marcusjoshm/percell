#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Workflow Orchestration Service for Single Cell Analysis

This service coordinates the execution of analysis workflows using the hexagonal architecture services.
It replaces the old pipeline.py orchestration logic with a clean, service-based approach.
"""

import os
import time
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from percell.domain.ports import FileSystemPort, LoggingPort, ConfigurationPort


class WorkflowOrchestrationService:
    """
    Service for orchestrating single-cell analysis workflows.
    
    This service coordinates the execution of various analysis steps using the hexagonal
    architecture services, replacing the old stage-based pipeline system.
    """
    
    def __init__(
        self,
        filesystem_port: FileSystemPort,
        logging_port: LoggingPort,
        configuration_port: ConfigurationPort
    ):
        """
        Initialize the Workflow Orchestration Service.
        
        Args:
            filesystem_port: Port for file system operations
            logging_port: Port for logging operations
            configuration_port: Port for configuration operations
        """
        self.filesystem_port = filesystem_port
        self.logging_port = logging_port
        self.configuration_port = configuration_port
        self.logger = self.logging_port.get_logger("WorkflowOrchestrationService")
        
        # Workflow execution tracking
        self.execution_history = []
        self.current_workflow = None
    
    def get_available_workflows(self) -> Dict[str, Dict[str, Any]]:
        """
        Get list of available predefined workflows.
        
        Returns:
            Dictionary of workflow definitions
        """
        workflows = {
            'complete_analysis': {
                'name': 'Complete Analysis Workflow',
                'description': 'Full end-to-end analysis from data selection to final results',
                'steps': [
                    'data_selection',
                    'segmentation', 
                    'process_single_cell',
                    'threshold_grouped_cells',
                    'measure_roi_area',
                    'analysis',
                    'cleanup'
                ],
                'estimated_duration': '2-4 hours',
                'requirements': ['input_data', 'output_directory', 'imagej_path']
            },
            'segmentation_only': {
                'name': 'Segmentation Only',
                'description': 'Perform only image binning and interactive segmentation',
                'steps': ['data_selection', 'segmentation'],
                'estimated_duration': '30-60 minutes',
                'requirements': ['input_data', 'output_directory']
            },
            'analysis_only': {
                'name': 'Analysis Only',
                'description': 'Run analysis on existing segmentation data',
                'steps': ['analysis'],
                'estimated_duration': '1-2 hours',
                'requirements': ['existing_segmentation', 'output_directory']
            },
            'cleanup_only': {
                'name': 'Cleanup Only',
                'description': 'Clean up intermediate files to free disk space',
                'steps': ['cleanup'],
                'estimated_duration': '5-10 minutes',
                'requirements': ['output_directory']
            }
        }
        
        return workflows
    
    def validate_workflow_requirements(
        self,
        workflow_name: str,
        input_dir: str,
        output_dir: str,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Validate that all requirements for a workflow are met.
        
        Args:
            workflow_name: Name of the workflow to validate
            input_dir: Input directory path
            output_dir: Output directory path
            **kwargs: Additional workflow parameters
            
        Returns:
            Dictionary with validation results
        """
        try:
            workflows = self.get_available_workflows()
            if workflow_name not in workflows:
                return {
                    'valid': False,
                    'error': f'Unknown workflow: {workflow_name}'
                }
            
            workflow = workflows[workflow_name]
            validation_results = {
                'valid': True,
                'workflow': workflow,
                'errors': [],
                'warnings': []
            }
            
            # Validate input directory
            if 'input_data' in workflow['requirements']:
                if not input_dir:
                    validation_results['errors'].append('Input directory is required for this workflow')
                    validation_results['valid'] = False
                elif not self.filesystem_port.path_exists(input_dir):
                    validation_results['errors'].append(f'Input directory does not exist: {input_dir}')
                    validation_results['valid'] = False
                elif not self.filesystem_port.is_directory(input_dir):
                    validation_results['errors'].append(f'Input path is not a directory: {input_dir}')
                    validation_results['valid'] = False
            
            # Validate output directory
            if not output_dir:
                validation_results['errors'].append('Output directory is required')
                validation_results['valid'] = False
            else:
                # Try to create output directory
                try:
                    self.filesystem_port.create_directories(output_dir)
                except Exception as e:
                    validation_results['errors'].append(f'Cannot create output directory: {e}')
                    validation_results['valid'] = False
            
            # Validate ImageJ path if required
            if 'imagej_path' in workflow['requirements']:
                imagej_path = kwargs.get('imagej_path') or self.configuration_port.get_configuration().get('imagej_path')
                if not imagej_path:
                    validation_results['warnings'].append('ImageJ path not specified - some steps may fail')
                elif not self.filesystem_port.path_exists(imagej_path):
                    validation_results['warnings'].append(f'ImageJ path does not exist: {imagej_path}')
            
            # Validate existing segmentation if required
            if 'existing_segmentation' in workflow['requirements']:
                roi_dir = os.path.join(output_dir, 'ROIs')
                if not self.filesystem_port.path_exists(roi_dir):
                    validation_results['errors'].append('ROI directory not found - run segmentation first')
                    validation_results['valid'] = False
            
            return validation_results
            
        except Exception as e:
            return {
                'valid': False,
                'error': f'Validation error: {e}'
            }
    
    def setup_workflow_directories(self, output_dir: str, workflow_name: str) -> Dict[str, Any]:
        """
        Set up required directories for a workflow.
        
        Args:
            output_dir: Base output directory
            workflow_name: Name of the workflow
            
        Returns:
            Dictionary with setup results
        """
        try:
            workflows = self.get_available_workflows()
            if workflow_name not in workflows:
                return {
                    'success': False,
                    'error': f'Unknown workflow: {workflow_name}'
                }
            
            workflow = workflows[workflow_name]
            created_dirs = []
            
            # Always create logs directory
            logs_dir = os.path.join(output_dir, 'logs')
            self.filesystem_port.create_directories(logs_dir)
            created_dirs.append(logs_dir)
            
            # Create workflow-specific directories
            if 'segmentation' in workflow['steps']:
                preprocessed_dir = os.path.join(output_dir, 'preprocessed')
                self.filesystem_port.create_directories(preprocessed_dir)
                created_dirs.append(preprocessed_dir)
            
            if 'process_single_cell' in workflow['steps']:
                roi_dir = os.path.join(output_dir, 'ROIs')
                cells_dir = os.path.join(output_dir, 'cells')
                grouped_cells_dir = os.path.join(output_dir, 'grouped_cells')
                
                self.filesystem_port.create_directories(roi_dir)
                self.filesystem_port.create_directories(cells_dir)
                self.filesystem_port.create_directories(grouped_cells_dir)
                
                created_dirs.extend([roi_dir, cells_dir, grouped_cells_dir])
            
            if 'threshold_grouped_cells' in workflow['steps']:
                grouped_masks_dir = os.path.join(output_dir, 'grouped_masks')
                self.filesystem_port.create_directories(grouped_masks_dir)
                created_dirs.append(grouped_masks_dir)
            
            if 'analysis' in workflow['steps']:
                masks_dir = os.path.join(output_dir, 'masks')
                combined_masks_dir = os.path.join(output_dir, 'combined_masks')
                analysis_dir = os.path.join(output_dir, 'analysis')
                
                self.filesystem_port.create_directories(masks_dir)
                self.filesystem_port.create_directories(combined_masks_dir)
                self.filesystem_port.create_directories(analysis_dir)
                
                created_dirs.extend([masks_dir, combined_masks_dir, analysis_dir])
            
            self.logger.info(f"Created {len(created_dirs)} directories for workflow '{workflow_name}'")
            
            return {
                'success': True,
                'created_directories': created_dirs,
                'message': f'Workflow directories setup completed for {workflow_name}'
            }
            
        except Exception as e:
            error_msg = f'Error setting up workflow directories: {e}'
            self.logger.error(error_msg)
            return {
                'success': False,
                'error': error_msg
            }
    
    def execute_workflow(
        self,
        workflow_name: str,
        input_dir: str,
        output_dir: str,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Execute a complete workflow.
        
        Args:
            workflow_name: Name of the workflow to execute
            input_dir: Input directory path
            output_dir: Output directory path
            **kwargs: Additional workflow parameters
            
        Returns:
            Dictionary with execution results
        """
        try:
            start_time = time.time()
            
            # Validate workflow requirements
            validation = self.validate_workflow_requirements(workflow_name, input_dir, output_dir, **kwargs)
            if not validation['valid']:
                return {
                    'success': False,
                    'error': f'Workflow validation failed: {validation["errors"]}'
                }
            
            # Setup directories
            setup_result = self.setup_workflow_directories(output_dir, workflow_name)
            if not setup_result['success']:
                return setup_result
            
            # Get workflow definition
            workflows = self.get_available_workflows()
            workflow = workflows[workflow_name]
            
            self.logger.info(f"Starting workflow: {workflow['name']}")
            self.logger.info(f"Steps: {', '.join(workflow['steps'])}")
            
            # Track execution
            self.current_workflow = {
                'name': workflow_name,
                'start_time': start_time,
                'steps': workflow['steps'],
                'status': 'running'
            }
            
            execution_results = {
                'workflow_name': workflow_name,
                'start_time': start_time,
                'steps_completed': [],
                'steps_failed': [],
                'total_duration': 0,
                'success': False
            }
            
            # Execute each step
            for step in workflow['steps']:
                step_start = time.time()
                self.logger.info(f"Executing step: {step}")
                
                try:
                    step_result = self._execute_workflow_step(
                        step, input_dir, output_dir, **kwargs
                    )
                    
                    if step_result['success']:
                        execution_results['steps_completed'].append({
                            'step': step,
                            'duration': time.time() - step_start,
                            'message': step_result.get('message', 'Step completed successfully')
                        })
                        self.logger.info(f"Step '{step}' completed successfully")
                    else:
                        execution_results['steps_failed'].append({
                            'step': step,
                            'duration': time.time() - step_start,
                            'error': step_result.get('error', 'Unknown error')
                        })
                        self.logger.error(f"Step '{step}' failed: {step_result.get('error')}")
                        
                        # Stop execution on first failure
                        break
                        
                except Exception as e:
                    execution_results['steps_failed'].append({
                        'step': step,
                        'duration': time.time() - step_start,
                        'error': str(e)
                    })
                    self.logger.error(f"Step '{step}' failed with exception: {e}")
                    break
            
            # Calculate total duration
            total_duration = time.time() - start_time
            execution_results['total_duration'] = total_duration
            
            # Determine overall success
            if not execution_results['steps_failed']:
                execution_results['success'] = True
                self.current_workflow['status'] = 'completed'
                self.logger.info(f"Workflow '{workflow_name}' completed successfully in {total_duration:.2f}s")
            else:
                self.current_workflow['status'] = 'failed'
                self.logger.error(f"Workflow '{workflow_name}' failed after {total_duration:.2f}s")
            
            # Update execution history
            self.execution_history.append(execution_results)
            
            return execution_results
            
        except Exception as e:
            error_msg = f'Error executing workflow: {e}'
            self.logger.error(error_msg)
            return {
                'success': False,
                'error': error_msg
            }
    
    def _execute_workflow_step(
        self,
        step: str,
        input_dir: str,
        output_dir: str,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Execute a single workflow step.
        
        Args:
            step: Step name to execute
            input_dir: Input directory path
            output_dir: Output directory path
            **kwargs: Additional parameters
            
        Returns:
            Dictionary with step execution results
        """
        try:
            # This method would coordinate with the appropriate hexagonal services
            # For now, return a placeholder that indicates the step would be executed
            # In the full implementation, this would call the appropriate services
            
            step_handlers = {
                'data_selection': self._handle_data_selection,
                'segmentation': self._handle_segmentation,
                'process_single_cell': self._handle_process_single_cell,
                'threshold_grouped_cells': self._handle_threshold_grouped_cells,
                'measure_roi_area': self._handle_measure_roi_area,
                'analysis': self._handle_analysis,
                'cleanup': self._handle_cleanup
            }
            
            if step in step_handlers:
                return step_handlers[step](input_dir, output_dir, **kwargs)
            else:
                return {
                    'success': False,
                    'error': f'Unknown workflow step: {step}'
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': f'Error executing step {step}: {e}'
            }
    
    def _handle_data_selection(self, input_dir: str, output_dir: str, **kwargs) -> Dict[str, Any]:
        """Handle data selection step."""
        # This would use the DirectoryManagementService and other relevant services
        return {
            'success': True,
            'message': 'Data selection step completed (placeholder)'
        }
    
    def _handle_segmentation(self, input_dir: str, output_dir: str, **kwargs) -> Dict[str, Any]:
        """Handle segmentation step."""
        # This would use the BinImagesService and other relevant services
        return {
            'success': True,
            'message': 'Segmentation step completed (placeholder)'
        }
    
    def _handle_process_single_cell(self, input_dir: str, output_dir: str, **kwargs) -> Dict[str, Any]:
        """Handle process single cell step."""
        # This would use multiple services: TrackROIsService, DuplicateROIsService, etc.
        return {
            'success': True,
            'message': 'Process single cell step completed (placeholder)'
        }
    
    def _handle_threshold_grouped_cells(self, input_dir: str, output_dir: str, **kwargs) -> Dict[str, Any]:
        """Handle threshold grouped cells step."""
        # This would use the InteractiveThresholdingService
        return {
            'success': True,
            'message': 'Threshold grouped cells step completed (placeholder)'
        }
    
    def _handle_measure_roi_area(self, input_dir: str, output_dir: str, **kwargs) -> Dict[str, Any]:
        """Handle measure ROI area step."""
        # This would use the MeasureROIAreaService
        return {
            'success': True,
            'message': 'Measure ROI area step completed (placeholder)'
        }
    
    def _handle_analysis(self, input_dir: str, output_dir: str, **kwargs) -> Dict[str, Any]:
        """Handle analysis step."""
        # This would use multiple services: CombineMasksService, CreateCellMasksService, etc.
        return {
            'success': True,
            'message': 'Analysis step completed (placeholder)'
        }
    
    def _handle_cleanup(self, input_dir: str, output_dir: str, **kwargs) -> Dict[str, Any]:
        """Handle cleanup step."""
        # This would use the CleanupDirectoriesService
        return {
            'success': True,
            'message': 'Cleanup step completed (placeholder)'
        }
    
    def get_execution_history(self) -> List[Dict[str, Any]]:
        """
        Get the execution history of workflows.
        
        Returns:
            List of workflow execution results
        """
        return self.execution_history.copy()
    
    def get_current_workflow(self) -> Optional[Dict[str, Any]]:
        """
        Get information about the currently running workflow.
        
        Returns:
            Current workflow information or None
        """
        return self.current_workflow.copy() if self.current_workflow else None
    
    def cancel_current_workflow(self) -> Dict[str, Any]:
        """
        Cancel the currently running workflow.
        
        Returns:
            Dictionary with cancellation results
        """
        if not self.current_workflow:
            return {
                'success': False,
                'error': 'No workflow is currently running'
            }
        
        try:
            self.current_workflow['status'] = 'cancelled'
            self.logger.info(f"Workflow '{self.current_workflow['name']}' cancelled by user")
            
            return {
                'success': True,
                'message': f"Workflow '{self.current_workflow['name']}' cancelled successfully"
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Error cancelling workflow: {e}'
            }
    
    def get_workflow_status(self, workflow_name: str) -> Dict[str, Any]:
        """
        Get the status of a specific workflow.
        
        Args:
            workflow_name: Name of the workflow
            
        Returns:
            Dictionary with workflow status
        """
        try:
            # Check if it's the current workflow
            if self.current_workflow and self.current_workflow['name'] == workflow_name:
                return {
                    'status': self.current_workflow['status'],
                    'current_step': self.current_workflow.get('current_step'),
                    'start_time': self.current_workflow['start_time'],
                    'is_running': self.current_workflow['status'] == 'running'
                }
            
            # Check execution history
            for execution in self.execution_history:
                if execution['workflow_name'] == workflow_name:
                    return {
                        'status': 'completed' if execution['success'] else 'failed',
                        'total_duration': execution['total_duration'],
                        'steps_completed': len(execution['steps_completed']),
                        'steps_failed': len(execution['steps_failed']),
                        'is_running': False
                    }
            
            return {
                'status': 'not_found',
                'error': f'Workflow "{workflow_name}" not found in history'
            }
            
        except Exception as e:
            return {
                'status': 'error',
                'error': f'Error getting workflow status: {e}'
            }
