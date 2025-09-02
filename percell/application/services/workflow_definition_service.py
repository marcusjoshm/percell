#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Workflow Definition Service for Single Cell Analysis

This service manages workflow definitions, configurations, and metadata.
It replaces the old stage_registry.py functionality with a clean, service-based approach.
"""

import os
import json
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from percell.domain.ports import FileSystemPort, LoggingPort, ConfigurationPort


class WorkflowDefinitionService:
    """
    Service for managing workflow definitions and configurations.
    
    This service handles the registration, storage, and retrieval of workflow definitions,
    replacing the old stage-based registry system with a more flexible approach.
    """
    
    def __init__(
        self,
        filesystem_port: FileSystemPort,
        logging_port: LoggingPort,
        configuration_port: ConfigurationPort
    ):
        """
        Initialize the Workflow Definition Service.
        
        Args:
            filesystem_port: Port for file system operations
            logging_port: Port for logging operations
            configuration_port: Port for configuration operations
        """
        self.filesystem_port = filesystem_port
        self.logging_port = logging_port
        self.configuration_port = configuration_port
        self.logger = self.logging_port.get_logger("WorkflowDefinitionService")
        
        # Initialize default workflow definitions
        self._initialize_default_workflows()
    
    def _initialize_default_workflows(self) -> None:
        """Initialize the default workflow definitions."""
        self.default_workflows = {
            'complete_analysis': {
                'id': 'complete_analysis',
                'name': 'Complete Analysis Workflow',
                'description': 'Full end-to-end analysis from data selection to final results',
                'version': '1.0.0',
                'category': 'full_analysis',
                'steps': [
                    {
                        'id': 'data_selection',
                        'name': 'Data Selection',
                        'description': 'Select conditions, regions, timepoints, and channels',
                        'order': 1,
                        'required': True,
                        'dependencies': [],
                        'estimated_duration': '10-15 minutes',
                        'service': 'directory_management_service'
                    },
                    {
                        'id': 'segmentation',
                        'name': 'Image Segmentation',
                        'description': 'Bin images and perform interactive segmentation',
                        'order': 2,
                        'required': True,
                        'dependencies': ['data_selection'],
                        'estimated_duration': '30-60 minutes',
                        'service': 'bin_images_service'
                    },
                    {
                        'id': 'process_single_cell',
                        'name': 'Single Cell Processing',
                        'description': 'Track ROIs, duplicate for channels, extract cells, and group',
                        'order': 3,
                        'required': True,
                        'dependencies': ['segmentation'],
                        'estimated_duration': '45-90 minutes',
                        'service': 'track_rois_service'
                    },
                    {
                        'id': 'threshold_grouped_cells',
                        'name': 'Threshold Grouped Cells',
                        'description': 'Apply Otsu thresholding to grouped cell images',
                        'order': 4,
                        'required': True,
                        'dependencies': ['process_single_cell'],
                        'estimated_duration': '30-60 minutes',
                        'service': 'interactive_thresholding_service'
                    },
                    {
                        'id': 'measure_roi_area',
                        'name': 'Measure ROI Areas',
                        'description': 'Measure areas of ROIs using ImageJ',
                        'order': 5,
                        'required': True,
                        'dependencies': ['threshold_grouped_cells'],
                        'estimated_duration': '15-30 minutes',
                        'service': 'measure_roi_area_service'
                    },
                    {
                        'id': 'analysis',
                        'name': 'Analysis',
                        'description': 'Combine masks, create cell masks, analyze, and include metadata',
                        'order': 6,
                        'required': True,
                        'dependencies': ['measure_roi_area'],
                        'estimated_duration': '30-60 minutes',
                        'service': 'combine_masks_service'
                    },
                    {
                        'id': 'cleanup',
                        'name': 'Cleanup',
                        'description': 'Clean up intermediate files to free disk space',
                        'order': 7,
                        'required': False,
                        'dependencies': ['analysis'],
                        'estimated_duration': '5-10 minutes',
                        'service': 'cleanup_directories_service'
                    }
                ],
                'estimated_total_duration': '2-4 hours',
                'requirements': ['input_data', 'output_directory', 'imagej_path'],
                'tags': ['full_workflow', 'end_to_end', 'production'],
                'created_date': '2024-01-01',
                'last_modified': '2024-01-01'
            },
            'segmentation_only': {
                'id': 'segmentation_only',
                'name': 'Segmentation Only',
                'description': 'Perform only image binning and interactive segmentation',
                'version': '1.0.0',
                'category': 'segmentation',
                'steps': [
                    {
                        'id': 'data_selection',
                        'name': 'Data Selection',
                        'description': 'Select conditions, regions, timepoints, and channels',
                        'order': 1,
                        'required': True,
                        'dependencies': [],
                        'estimated_duration': '10-15 minutes',
                        'service': 'directory_management_service'
                    },
                    {
                        'id': 'segmentation',
                        'name': 'Image Segmentation',
                        'description': 'Bin images and perform interactive segmentation',
                        'order': 2,
                        'required': True,
                        'dependencies': ['data_selection'],
                        'estimated_duration': '30-60 minutes',
                        'service': 'bin_images_service'
                    }
                ],
                'estimated_total_duration': '30-60 minutes',
                'requirements': ['input_data', 'output_directory'],
                'tags': ['segmentation', 'quick', 'development'],
                'created_date': '2024-01-01',
                'last_modified': '2024-01-01'
            },
            'analysis_only': {
                'id': 'analysis_only',
                'name': 'Analysis Only',
                'description': 'Run analysis on existing segmentation data',
                'version': '1.0.0',
                'category': 'analysis',
                'steps': [
                    {
                        'id': 'analysis',
                        'name': 'Analysis',
                        'description': 'Combine masks, create cell masks, analyze, and include metadata',
                        'order': 1,
                        'required': True,
                        'dependencies': [],
                        'estimated_duration': '30-60 minutes',
                        'service': 'combine_masks_service'
                    }
                ],
                'estimated_total_duration': '1-2 hours',
                'requirements': ['existing_segmentation', 'output_directory'],
                'tags': ['analysis', 'post_processing', 'reanalysis'],
                'created_date': '2024-01-01',
                'last_modified': '2024-01-01'
            },
            'cleanup_only': {
                'id': 'cleanup_only',
                'name': 'Cleanup Only',
                'description': 'Clean up intermediate files to free disk space',
                'version': '1.0.0',
                'category': 'maintenance',
                'steps': [
                    {
                        'id': 'cleanup',
                        'name': 'Cleanup',
                        'description': 'Clean up intermediate files to free disk space',
                        'order': 1,
                        'required': True,
                        'dependencies': [],
                        'estimated_duration': '5-10 minutes',
                        'service': 'cleanup_directories_service'
                    }
                ],
                'estimated_total_duration': '5-10 minutes',
                'requirements': ['output_directory'],
                'tags': ['maintenance', 'cleanup', 'disk_space'],
                'created_date': '2024-01-01',
                'last_modified': '2024-01-01'
            }
        }
    
    def get_workflow_definition(self, workflow_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a workflow definition by ID.
        
        Args:
            workflow_id: ID of the workflow to retrieve
            
        Returns:
            Workflow definition dictionary or None if not found
        """
        try:
            # First check default workflows
            if workflow_id in self.default_workflows:
                return self.default_workflows[workflow_id].copy()
            
            # Then check custom workflows from configuration
            config = self.configuration_port.get_configuration()
            custom_workflows = config.get('workflows', {})
            
            if workflow_id in custom_workflows:
                return custom_workflows[workflow_id].copy()
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error getting workflow definition {workflow_id}: {e}")
            return None
    
    def get_all_workflow_definitions(self) -> Dict[str, Dict[str, Any]]:
        """
        Get all available workflow definitions.
        
        Returns:
            Dictionary of all workflow definitions
        """
        try:
            all_workflows = self.default_workflows.copy()
            
            # Add custom workflows from configuration
            config = self.configuration_port.get_configuration()
            custom_workflows = config.get('workflows', {})
            all_workflows.update(custom_workflows)
            
            return all_workflows
            
        except Exception as e:
            self.logger.error(f"Error getting all workflow definitions: {e}")
            return self.default_workflows.copy()
    
    def get_workflows_by_category(self, category: str) -> List[Dict[str, Any]]:
        """
        Get workflows filtered by category.
        
        Args:
            category: Category to filter by
            
        Returns:
            List of workflow definitions in the specified category
        """
        try:
            all_workflows = self.get_all_workflow_definitions()
            filtered_workflows = []
            
            for workflow in all_workflows.values():
                if workflow.get('category') == category:
                    filtered_workflows.append(workflow.copy())
            
            return filtered_workflows
            
        except Exception as e:
            self.logger.error(f"Error getting workflows by category {category}: {e}")
            return []
    
    def get_workflows_by_tag(self, tag: str) -> List[Dict[str, Any]]:
        """
        Get workflows filtered by tag.
        
        Args:
            tag: Tag to filter by
            
        Returns:
            List of workflow definitions with the specified tag
        """
        try:
            all_workflows = self.get_all_workflow_definitions()
            filtered_workflows = []
            
            for workflow in all_workflows.values():
                if 'tags' in workflow and tag in workflow['tags']:
                    filtered_workflows.append(workflow.copy())
            
            return filtered_workflows
            
        except Exception as e:
            self.logger.error(f"Error getting workflows by tag {tag}: {e}")
            return []
    
    def create_custom_workflow(self, workflow_definition: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a custom workflow definition.
        
        Args:
            workflow_definition: Complete workflow definition
            
        Returns:
            Dictionary with operation results
        """
        try:
            # Validate workflow definition
            validation_result = self._validate_workflow_definition(workflow_definition)
            if not validation_result['valid']:
                return {
                    'success': False,
                    'error': f'Invalid workflow definition: {validation_result["errors"]}'
                }
            
            # Check if workflow ID already exists
            workflow_id = workflow_definition['id']
            existing_workflow = self.get_workflow_definition(workflow_id)
            if existing_workflow:
                return {
                    'success': False,
                    'error': f'Workflow with ID "{workflow_id}" already exists'
                }
            
            # Add metadata
            workflow_definition['created_date'] = self._get_current_date()
            workflow_definition['last_modified'] = self._get_current_date()
            
            # Save to configuration
            config = self.configuration_port.get_configuration()
            if 'workflows' not in config:
                config['workflows'] = {}
            
            config['workflows'][workflow_id] = workflow_definition
            self.configuration_port.update_configuration(config)
            
            self.logger.info(f"Custom workflow '{workflow_id}' created successfully")
            
            return {
                'success': True,
                'workflow_id': workflow_id,
                'message': f'Custom workflow "{workflow_id}" created successfully'
            }
            
        except Exception as e:
            error_msg = f'Error creating custom workflow: {e}'
            self.logger.error(error_msg)
            return {
                'success': False,
                'error': error_msg
            }
    
    def update_workflow_definition(self, workflow_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update an existing workflow definition.
        
        Args:
            workflow_id: ID of the workflow to update
            updates: Dictionary of updates to apply
            
        Returns:
            Dictionary with operation results
        """
        try:
            # Check if workflow exists
            existing_workflow = self.get_workflow_definition(workflow_id)
            if not existing_workflow:
                return {
                    'success': False,
                    'error': f'Workflow "{workflow_id}" not found'
                }
            
            # Apply updates
            updated_workflow = existing_workflow.copy()
            updated_workflow.update(updates)
            updated_workflow['last_modified'] = self._get_current_date()
            
            # Validate updated workflow
            validation_result = self._validate_workflow_definition(updated_workflow)
            if not validation_result['valid']:
                return {
                    'success': False,
                    'error': f'Invalid workflow definition after updates: {validation_result["errors"]}'
                }
            
            # Save to configuration
            config = self.configuration_port.get_configuration()
            if 'workflows' not in config:
                config['workflows'] = {}
            
            config['workflows'][workflow_id] = updated_workflow
            self.configuration_port.update_configuration(config)
            
            self.logger.info(f"Workflow '{workflow_id}' updated successfully")
            
            return {
                'success': True,
                'workflow_id': workflow_id,
                'message': f'Workflow "{workflow_id}" updated successfully'
            }
            
        except Exception as e:
            error_msg = f'Error updating workflow {workflow_id}: {e}'
            self.logger.error(error_msg)
            return {
                'success': False,
                'error': error_msg
            }
    
    def delete_custom_workflow(self, workflow_id: str) -> Dict[str, Any]:
        """
        Delete a custom workflow definition.
        
        Args:
            workflow_id: ID of the workflow to delete
            
        Returns:
            Dictionary with operation results
        """
        try:
            # Check if workflow exists and is custom (not default)
            if workflow_id in self.default_workflows:
                return {
                    'success': False,
                    'error': f'Cannot delete default workflow "{workflow_id}"'
                }
            
            existing_workflow = self.get_workflow_definition(workflow_id)
            if not existing_workflow:
                return {
                    'success': False,
                    'error': f'Workflow "{workflow_id}" not found'
                }
            
            # Remove from configuration
            config = self.configuration_port.get_configuration()
            if 'workflows' in config and workflow_id in config['workflows']:
                del config['workflows'][workflow_id]
                self.configuration_port.update_configuration(config)
            
            self.logger.info(f"Custom workflow '{workflow_id}' deleted successfully")
            
            return {
                'success': True,
                'workflow_id': workflow_id,
                'message': f'Custom workflow "{workflow_id}" deleted successfully'
            }
            
        except Exception as e:
            error_msg = f'Error deleting workflow {workflow_id}: {e}'
            self.logger.error(error_msg)
            return {
                'success': False,
                'error': error_msg
            }
    
    def get_workflow_steps(self, workflow_id: str) -> List[Dict[str, Any]]:
        """
        Get the steps for a specific workflow.
        
        Args:
            workflow_id: ID of the workflow
            
        Returns:
            List of workflow steps
        """
        try:
            workflow = self.get_workflow_definition(workflow_id)
            if not workflow:
                return []
            
            return workflow.get('steps', [])
            
        except Exception as e:
            self.logger.error(f"Error getting workflow steps for {workflow_id}: {e}")
            return []
    
    def get_workflow_dependencies(self, workflow_id: str) -> Dict[str, List[str]]:
        """
        Get the dependency graph for a workflow.
        
        Args:
            workflow_id: ID of the workflow
            
        Returns:
            Dictionary mapping step IDs to their dependencies
        """
        try:
            steps = self.get_workflow_steps(workflow_id)
            dependencies = {}
            
            for step in steps:
                step_id = step['id']
                deps = step.get('dependencies', [])
                dependencies[step_id] = deps
            
            return dependencies
            
        except Exception as e:
            self.logger.error(f"Error getting workflow dependencies for {workflow_id}: {e}")
            return {}
    
    def validate_workflow_execution_order(self, workflow_id: str) -> Dict[str, Any]:
        """
        Validate that a workflow's execution order is valid.
        
        Args:
            workflow_id: ID of the workflow to validate
            
        Returns:
            Dictionary with validation results
        """
        try:
            dependencies = self.get_workflow_dependencies(workflow_id)
            if not dependencies:
                return {
                    'valid': False,
                    'error': 'No workflow steps found'
                }
            
            # Check for circular dependencies
            visited = set()
            rec_stack = set()
            
            def has_cycle(node: str) -> bool:
                visited.add(node)
                rec_stack.add(node)
                
                for neighbor in dependencies.get(node, []):
                    if neighbor not in visited:
                        if has_cycle(neighbor):
                            return True
                    elif neighbor in rec_stack:
                        return True
                
                rec_stack.remove(node)
                return False
            
            # Check each step for cycles
            for step_id in dependencies:
                if step_id not in visited:
                    if has_cycle(step_id):
                        return {
                            'valid': False,
                            'error': f'Circular dependency detected in workflow "{workflow_id}"'
                        }
            
            return {
                'valid': True,
                'message': f'Workflow "{workflow_id}" execution order is valid'
            }
            
        except Exception as e:
            return {
                'valid': False,
                'error': f'Error validating workflow execution order: {e}'
            }
    
    def export_workflow_definition(self, workflow_id: str, format: str = 'json') -> Dict[str, Any]:
        """
        Export a workflow definition to a file.
        
        Args:
            workflow_id: ID of the workflow to export
            format: Export format ('json' or 'yaml')
            
        Returns:
            Dictionary with operation results
        """
        try:
            workflow = self.get_workflow_definition(workflow_id)
            if not workflow:
                return {
                    'success': False,
                    'error': f'Workflow "{workflow_id}" not found'
                }
            
            if format.lower() == 'json':
                content = json.dumps(workflow, indent=2)
                extension = 'json'
            elif format.lower() == 'yaml':
                try:
                    import yaml
                    content = yaml.dump(workflow, default_flow_style=False, indent=2)
                    extension = 'yaml'
                except ImportError:
                    return {
                        'success': False,
                        'error': 'YAML export requires PyYAML package'
                    }
            else:
                return {
                    'success': False,
                    'error': f'Unsupported export format: {format}'
                }
            
            # Create export filename
            filename = f"{workflow_id}_workflow.{extension}"
            
            return {
                'success': True,
                'filename': filename,
                'content': content,
                'format': format,
                'message': f'Workflow "{workflow_id}" exported successfully'
            }
            
        except Exception as e:
            error_msg = f'Error exporting workflow {workflow_id}: {e}'
            self.logger.error(error_msg)
            return {
                'success': False,
                'error': error_msg
            }
    
    def _validate_workflow_definition(self, workflow: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate a workflow definition.
        
        Args:
            workflow: Workflow definition to validate
            
        Returns:
            Dictionary with validation results
        """
        errors = []
        
        # Check required fields
        required_fields = ['id', 'name', 'description', 'steps']
        for field in required_fields:
            if field not in workflow:
                errors.append(f'Missing required field: {field}')
        
        # Check steps
        if 'steps' in workflow:
            steps = workflow['steps']
            if not isinstance(steps, list) or len(steps) == 0:
                errors.append('Workflow must have at least one step')
            else:
                for i, step in enumerate(steps):
                    if not isinstance(step, dict):
                        errors.append(f'Step {i} must be a dictionary')
                        continue
                    
                    # Check step required fields
                    step_required = ['id', 'name', 'description', 'order']
                    for field in step_required:
                        if field not in step:
                            errors.append(f'Step {i} missing required field: {field}')
                    
                    # Check step order
                    if 'order' in step and not isinstance(step['order'], int):
                        errors.append(f'Step {i} order must be an integer')
        
        return {
            'valid': len(errors) == 0,
            'errors': errors
        }
    
    def _get_current_date(self) -> str:
        """
        Get current date in ISO format.
        
        Returns:
            Current date as string
        """
        from datetime import datetime
        return datetime.now().strftime('%Y-%m-%d')
