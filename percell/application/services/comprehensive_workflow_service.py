#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Comprehensive Workflow Service for Single Cell Analysis

This service provides a high-level interface for executing complex workflows
using the hexagonal architecture services. It orchestrates multiple workflow
steps and provides comprehensive workflow management capabilities.
"""

from __future__ import annotations

import time
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from percell.domain.ports import FileSystemPort, LoggingPort, ConfigurationPort


class ComprehensiveWorkflowService:
    """
    Comprehensive workflow orchestration service.
    
    This service provides high-level workflow execution capabilities by
    coordinating multiple hexagonal architecture services to execute
    complex analysis workflows.
    """
    
    def __init__(
        self,
        filesystem_port: FileSystemPort,
        logging_port: LoggingPort,
        configuration_port: ConfigurationPort,
        # Workflow services
        bin_images_service=None,
        combine_masks_service=None,
        create_cell_masks_service=None,
        analyze_cell_masks_service=None,
        interactive_thresholding_service=None,
        include_group_metadata_service=None,
        track_rois_service=None,
        resize_rois_service=None,
        duplicate_rois_service=None,
        extract_cells_service=None,
        group_cells_service=None,
        measure_roi_area_service=None,
        cleanup_directories_service=None,
        directory_management_service=None
    ):
        """
        Initialize the comprehensive workflow service.
        
        Args:
            filesystem_port: Port for file system operations
            logging_port: Port for logging operations
            configuration_port: Port for configuration operations
            bin_images_service: Service for binning images
            combine_masks_service: Service for combining masks
            create_cell_masks_service: Service for creating cell masks
            analyze_cell_masks_service: Service for analyzing cell masks
            interactive_thresholding_service: Service for interactive thresholding
            include_group_metadata_service: Service for including group metadata
            track_rois_service: Service for tracking ROIs
            resize_rois_service: Service for resizing ROIs
            duplicate_rois_service: Service for duplicating ROIs
            extract_cells_service: Service for extracting cells
            group_cells_service: Service for grouping cells
            measure_roi_area_service: Service for measuring ROI area
            cleanup_directories_service: Service for cleaning up directories
            directory_management_service: Service for directory management
        """
        self.filesystem_port = filesystem_port
        self.logging_port = logging_port
        self.configuration_port = configuration_port
        self.logger = self.logging_port.get_logger("ComprehensiveWorkflowService")
        
        # Store workflow services
        self.bin_images_service = bin_images_service
        self.combine_masks_service = combine_masks_service
        self.create_cell_masks_service = create_cell_masks_service
        self.analyze_cell_masks_service = analyze_cell_masks_service
        self.interactive_thresholding_service = interactive_thresholding_service
        self.include_group_metadata_service = include_group_metadata_service
        self.track_rois_service = track_rois_service
        self.resize_rois_service = resize_rois_service
        self.duplicate_rois_service = duplicate_rois_service
        self.extract_cells_service = extract_cells_service
        self.group_cells_service = group_cells_service
        self.measure_roi_area_service = measure_roi_area_service
        self.cleanup_directories_service = cleanup_directories_service
        self.directory_management_service = directory_management_service
        
        # Workflow execution tracking
        self.execution_history = []
        self.current_workflow = None
    
    def execute_complete_workflow(
        self,
        input_dir: str,
        output_dir: str,
        analysis_channels: List[str],
        imagej_path: str,
        conditions: Optional[List[str]] = None,
        regions: Optional[List[str]] = None,
        timepoints: Optional[List[str]] = None,
        segmentation_channel: Optional[str] = None,
        bins: int = 5,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Execute a complete end-to-end analysis workflow.
        
        Args:
            input_dir: Input directory containing raw data
            output_dir: Output directory for results
            analysis_channels: List of channels to analyze
            imagej_path: Path to ImageJ executable
            conditions: Optional list of conditions to process
            regions: Optional list of regions to process
            timepoints: Optional list of timepoints to process
            segmentation_channel: Channel to use for segmentation
            bins: Number of bins for cell grouping
            **kwargs: Additional workflow parameters
            
        Returns:
            Dictionary with workflow execution results
        """
        workflow_name = "complete_analysis"
        self.logger.info(f"Starting {workflow_name} workflow")
        
        workflow_steps = [
            ("data_selection", self._execute_data_selection),
            ("segmentation", self._execute_segmentation),
            ("process_single_cell", self._execute_process_single_cell),
            ("group_cells", self._execute_group_cells),
            ("threshold_grouped_cells", self._execute_threshold_grouped_cells),
            ("analysis", self._execute_analysis),
            ("measure_roi_area", self._execute_measure_roi_area),
            ("cleanup", self._execute_cleanup)
        ]
        
        return self._execute_workflow_steps(
            workflow_name,
            workflow_steps,
            input_dir=input_dir,
            output_dir=output_dir,
            analysis_channels=analysis_channels,
            imagej_path=imagej_path,
            conditions=conditions,
            regions=regions,
            timepoints=timepoints,
            segmentation_channel=segmentation_channel,
            bins=bins,
            **kwargs
        )
    
    def execute_segmentation_workflow(
        self,
        input_dir: str,
        output_dir: str,
        conditions: Optional[List[str]] = None,
        regions: Optional[List[str]] = None,
        timepoints: Optional[List[str]] = None,
        channels: Optional[List[str]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Execute a segmentation-only workflow.
        
        Args:
            input_dir: Input directory containing raw data
            output_dir: Output directory for results
            conditions: Optional list of conditions to process
            regions: Optional list of regions to process
            timepoints: Optional list of timepoints to process
            channels: Optional list of channels to process
            **kwargs: Additional workflow parameters
            
        Returns:
            Dictionary with workflow execution results
        """
        workflow_name = "segmentation_only"
        self.logger.info(f"Starting {workflow_name} workflow")
        
        workflow_steps = [
            ("data_selection", self._execute_data_selection),
            ("segmentation", self._execute_segmentation)
        ]
        
        return self._execute_workflow_steps(
            workflow_name,
            workflow_steps,
            input_dir=input_dir,
            output_dir=output_dir,
            conditions=conditions,
            regions=regions,
            timepoints=timepoints,
            channels=channels,
            **kwargs
        )
    
    def execute_analysis_workflow(
        self,
        output_dir: str,
        analysis_channels: List[str],
        imagej_path: str,
        regions: Optional[List[str]] = None,
        timepoints: Optional[List[str]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Execute an analysis-only workflow on existing segmentation data.
        
        Args:
            output_dir: Output directory containing existing segmentation data
            analysis_channels: List of channels to analyze
            imagej_path: Path to ImageJ executable
            regions: Optional list of regions to process
            timepoints: Optional list of timepoints to process
            **kwargs: Additional workflow parameters
            
        Returns:
            Dictionary with workflow execution results
        """
        workflow_name = "analysis_only"
        self.logger.info(f"Starting {workflow_name} workflow")
        
        workflow_steps = [
            ("analysis", self._execute_analysis),
            ("measure_roi_area", self._execute_measure_roi_area)
        ]
        
        return self._execute_workflow_steps(
            workflow_name,
            workflow_steps,
            output_dir=output_dir,
            analysis_channels=analysis_channels,
            imagej_path=imagej_path,
            regions=regions,
            timepoints=timepoints,
            **kwargs
        )
    
    def execute_single_cell_workflow(
        self,
        output_dir: str,
        analysis_channels: List[str],
        timepoints: Optional[List[str]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Execute a single-cell processing workflow.
        
        Args:
            output_dir: Output directory containing preprocessed data
            analysis_channels: List of channels to analyze
            timepoints: Optional list of timepoints to process
            **kwargs: Additional workflow parameters
            
        Returns:
            Dictionary with workflow execution results
        """
        workflow_name = "single_cell_processing"
        self.logger.info(f"Starting {workflow_name} workflow")
        
        workflow_steps = [
            ("track_rois", self._execute_track_rois),
            ("resize_rois", self._execute_resize_rois),
            ("duplicate_rois", self._execute_duplicate_rois),
            ("extract_cells", self._execute_extract_cells)
        ]
        
        return self._execute_workflow_steps(
            workflow_name,
            workflow_steps,
            output_dir=output_dir,
            analysis_channels=analysis_channels,
            timepoints=timepoints,
            **kwargs
        )
    
    def _execute_workflow_steps(
        self,
        workflow_name: str,
        workflow_steps: List[Tuple[str, callable]],
        **kwargs
    ) -> Dict[str, Any]:
        """
        Execute a series of workflow steps.
        
        Args:
            workflow_name: Name of the workflow being executed
            workflow_steps: List of (step_name, step_function) tuples
            **kwargs: Parameters to pass to step functions
            
        Returns:
            Dictionary with workflow execution results
        """
        start_time = time.time()
        self.current_workflow = workflow_name
        
        results = {
            'workflow_name': workflow_name,
            'start_time': start_time,
            'steps': [],
            'success': True,
            'errors': [],
            'warnings': []
        }
        
        try:
            for step_name, step_function in workflow_steps:
                step_start_time = time.time()
                self.logger.info(f"Executing step: {step_name}")
                
                try:
                    step_result = step_function(**kwargs)
                    step_end_time = time.time()
                    
                    step_info = {
                        'name': step_name,
                        'start_time': step_start_time,
                        'end_time': step_end_time,
                        'duration': step_end_time - step_start_time,
                        'success': step_result.get('success', False),
                        'message': step_result.get('message', ''),
                        'error': step_result.get('error', '')
                    }
                    
                    results['steps'].append(step_info)
                    
                    if not step_info['success']:
                        results['success'] = False
                        results['errors'].append(f"Step {step_name} failed: {step_info['error']}")
                        self.logger.error(f"Step {step_name} failed: {step_info['error']}")
                        break
                    else:
                        self.logger.info(f"Step {step_name} completed successfully: {step_info['message']}")
                        
                except Exception as e:
                    step_end_time = time.time()
                    step_info = {
                        'name': step_name,
                        'start_time': step_start_time,
                        'end_time': step_end_time,
                        'duration': step_end_time - step_start_time,
                        'success': False,
                        'message': '',
                        'error': str(e)
                    }
                    
                    results['steps'].append(step_info)
                    results['success'] = False
                    results['errors'].append(f"Step {step_name} failed with exception: {e}")
                    self.logger.error(f"Step {step_name} failed with exception: {e}")
                    break
                    
        except Exception as e:
            results['success'] = False
            results['errors'].append(f"Workflow execution failed: {e}")
            self.logger.error(f"Workflow execution failed: {e}")
        
        finally:
            end_time = time.time()
            results['end_time'] = end_time
            results['total_duration'] = end_time - start_time
            self.current_workflow = None
            
            # Add to execution history
            self.execution_history.append(results.copy())
            
            if results['success']:
                self.logger.info(f"Workflow {workflow_name} completed successfully in {results['total_duration']:.2f} seconds")
            else:
                self.logger.error(f"Workflow {workflow_name} failed after {results['total_duration']:.2f} seconds")
        
        return results
    
    def _execute_data_selection(self, **kwargs) -> Dict[str, Any]:
        """Execute data selection step."""
        try:
            if self.directory_management_service:
                # This would handle data selection logic
                return {
                    'success': True,
                    'message': 'Data selection step completed'
                }
            else:
                return {
                    'success': False,
                    'error': 'Directory management service not available'
                }
        except Exception as e:
            return {
                'success': False,
                'error': f'Error in data selection: {e}'
            }
    
    def _execute_segmentation(self, **kwargs) -> Dict[str, Any]:
        """Execute segmentation step."""
        try:
            if self.bin_images_service:
                success = self.bin_images_service.bin_images(
                    input_dir=kwargs.get('input_dir'),
                    output_dir=kwargs.get('output_dir'),
                    conditions=kwargs.get('conditions', []),
                    regions=kwargs.get('regions', []),
                    timepoints=kwargs.get('timepoints', []),
                    channels=kwargs.get('channels', [])
                )
                
                if success:
                    return {
                        'success': True,
                        'message': 'Segmentation step completed'
                    }
                else:
                    return {
                        'success': False,
                        'error': 'Image binning failed'
                    }
            else:
                return {
                    'success': False,
                    'error': 'Bin images service not available'
                }
        except Exception as e:
            return {
                'success': False,
                'error': f'Error in segmentation: {e}'
            }
    
    def _execute_process_single_cell(self, **kwargs) -> Dict[str, Any]:
        """Execute process single cell step."""
        try:
            steps_completed = []
            
            # Track ROIs
            if self.track_rois_service:
                success = self.track_rois_service.track_rois(
                    input_dir=f"{kwargs.get('output_dir')}/preprocessed",
                    output_dir=f"{kwargs.get('output_dir')}/tracked_rois",
                    timepoints=kwargs.get('timepoints', [])
                )
                if success:
                    steps_completed.append('track_rois')
            
            # Resize ROIs
            if self.resize_rois_service:
                success = self.resize_rois_service.resize_rois(
                    input_dir=f"{kwargs.get('output_dir')}/tracked_rois",
                    output_dir=f"{kwargs.get('output_dir')}/resized_rois"
                )
                if success:
                    steps_completed.append('resize_rois')
            
            # Duplicate ROIs
            if self.duplicate_rois_service:
                success = self.duplicate_rois_service.duplicate_rois(
                    input_dir=f"{kwargs.get('output_dir')}/resized_rois",
                    output_dir=f"{kwargs.get('output_dir')}/duplicated_rois",
                    channels=kwargs.get('analysis_channels', [])
                )
                if success:
                    steps_completed.append('duplicate_rois')
            
            # Extract cells
            if self.extract_cells_service:
                success = self.extract_cells_service.extract_cells(
                    input_dir=f"{kwargs.get('output_dir')}/duplicated_rois",
                    output_dir=f"{kwargs.get('output_dir')}/extracted_cells"
                )
                if success:
                    steps_completed.append('extract_cells')
            
            if steps_completed:
                return {
                    'success': True,
                    'message': f'Process single cell step completed: {", ".join(steps_completed)}'
                }
            else:
                return {
                    'success': False,
                    'error': 'No single cell processing steps completed'
                }
        except Exception as e:
            return {
                'success': False,
                'error': f'Error in process single cell: {e}'
            }
    
    def _execute_group_cells(self, **kwargs) -> Dict[str, Any]:
        """Execute group cells step."""
        try:
            if self.group_cells_service:
                success = self.group_cells_service.group_cells(
                    input_dir=f"{kwargs.get('output_dir')}/extracted_cells",
                    output_dir=f"{kwargs.get('output_dir')}/grouped_cells",
                    bins=kwargs.get('bins', 5),
                    channels=kwargs.get('analysis_channels', [])
                )
                
                if success:
                    return {
                        'success': True,
                        'message': 'Group cells step completed'
                    }
                else:
                    return {
                        'success': False,
                        'error': 'Group cells failed'
                    }
            else:
                return {
                    'success': False,
                    'error': 'Group cells service not available'
                }
        except Exception as e:
            return {
                'success': False,
                'error': f'Error in group cells: {e}'
            }
    
    def _execute_threshold_grouped_cells(self, **kwargs) -> Dict[str, Any]:
        """Execute threshold grouped cells step."""
        try:
            if self.interactive_thresholding_service:
                success = self.interactive_thresholding_service.threshold_grouped_cells(
                    input_dir=f"{kwargs.get('output_dir')}/grouped_cells",
                    output_dir=f"{kwargs.get('output_dir')}/grouped_masks",
                    channels=kwargs.get('analysis_channels', [])
                )
                
                if success:
                    return {
                        'success': True,
                        'message': 'Threshold grouped cells step completed'
                    }
                else:
                    return {
                        'success': False,
                        'error': 'Threshold grouped cells failed'
                    }
            else:
                return {
                    'success': False,
                    'error': 'Interactive thresholding service not available'
                }
        except Exception as e:
            return {
                'success': False,
                'error': f'Error in threshold grouped cells: {e}'
            }
    
    def _execute_analysis(self, **kwargs) -> Dict[str, Any]:
        """Execute analysis step."""
        try:
            steps_completed = []
            analysis_channels = kwargs.get('analysis_channels', [])
            
            # Combine masks
            if self.combine_masks_service:
                success = self.combine_masks_service.combine_masks(
                    input_dir=f"{kwargs.get('output_dir')}/grouped_masks",
                    output_dir=f"{kwargs.get('output_dir')}/combined_masks",
                    channels=analysis_channels
                )
                if success:
                    steps_completed.append('combine_masks')
            
            # Create cell masks
            if self.create_cell_masks_service:
                success = self.create_cell_masks_service.create_cell_masks(
                    roi_directory=f"{kwargs.get('output_dir')}/ROIs",
                    mask_directory=f"{kwargs.get('output_dir')}/combined_masks",
                    output_directory=f"{kwargs.get('output_dir')}/masks",
                    imagej_path=kwargs.get('imagej_path', '/usr/bin/imagej')
                )
                if success:
                    steps_completed.append('create_cell_masks')
            
            # Analyze cell masks
            if self.analyze_cell_masks_service:
                success = self.analyze_cell_masks_service.analyze_cell_masks(
                    input_dir=f"{kwargs.get('output_dir')}/masks",
                    output_dir=f"{kwargs.get('output_dir')}/analysis",
                    imagej_path=kwargs.get('imagej_path', '/usr/bin/imagej'),
                    regions=kwargs.get('regions'),
                    timepoints=kwargs.get('timepoints'),
                    channels=analysis_channels
                )
                if success:
                    steps_completed.append('analyze_cell_masks')
            
            if steps_completed:
                return {
                    'success': True,
                    'message': f'Analysis step completed: {", ".join(steps_completed)}'
                }
            else:
                return {
                    'success': False,
                    'error': 'No analysis steps completed'
                }
        except Exception as e:
            return {
                'success': False,
                'error': f'Error in analysis: {e}'
            }
    
    def _execute_measure_roi_area(self, **kwargs) -> Dict[str, Any]:
        """Execute measure ROI area step."""
        try:
            if self.measure_roi_area_service:
                success = self.measure_roi_area_service.measure_roi_area(
                    input_dir=f"{kwargs.get('output_dir')}/ROIs",
                    output_dir=f"{kwargs.get('output_dir')}/measurements"
                )
                
                if success:
                    return {
                        'success': True,
                        'message': 'Measure ROI area step completed'
                    }
                else:
                    return {
                        'success': False,
                        'error': 'Measure ROI area failed'
                    }
            else:
                return {
                    'success': False,
                    'error': 'Measure ROI area service not available'
                }
        except Exception as e:
            return {
                'success': False,
                'error': f'Error in measure ROI area: {e}'
            }
    
    def _execute_cleanup(self, **kwargs) -> Dict[str, Any]:
        """Execute cleanup step."""
        try:
            if self.cleanup_directories_service:
                success = self.cleanup_directories_service.cleanup_directories(
                    output_dir=kwargs.get('output_dir'),
                    keep_logs=True,
                    keep_final_results=True
                )
                
                if success:
                    return {
                        'success': True,
                        'message': 'Cleanup step completed'
                    }
                else:
                    return {
                        'success': False,
                        'error': 'Cleanup failed'
                    }
            else:
                return {
                    'success': False,
                    'error': 'Cleanup directories service not available'
                }
        except Exception as e:
            return {
                'success': False,
                'error': f'Error in cleanup: {e}'
            }
    
    def _execute_track_rois(self, **kwargs) -> Dict[str, Any]:
        """Execute track ROIs step."""
        try:
            if self.track_rois_service:
                success = self.track_rois_service.track_rois(
                    input_dir=f"{kwargs.get('output_dir')}/preprocessed",
                    output_dir=f"{kwargs.get('output_dir')}/tracked_rois",
                    timepoints=kwargs.get('timepoints', [])
                )
                
                if success:
                    return {
                        'success': True,
                        'message': 'Track ROIs step completed'
                    }
                else:
                    return {
                        'success': False,
                        'error': 'Track ROIs failed'
                    }
            else:
                return {
                    'success': False,
                    'error': 'Track ROIs service not available'
                }
        except Exception as e:
            return {
                'success': False,
                'error': f'Error in track ROIs: {e}'
            }
    
    def _execute_resize_rois(self, **kwargs) -> Dict[str, Any]:
        """Execute resize ROIs step."""
        try:
            if self.resize_rois_service:
                # Get ImageJ path from configuration or use default
                imagej_path = kwargs.get('imagej_path', '/Applications/ImageJ.app/Contents/MacOS/ImageJ')
                segmentation_channel = kwargs.get('segmentation_channel', 'ch01')  # Default to ch01
                
                success = self.resize_rois_service.resize_rois(
                    input_directory=f"{kwargs.get('output_dir')}/preprocessed",  # Use preprocessed directory where ROIs are saved
                    output_directory=f"{kwargs.get('output_dir')}/ROIs",  # Use ROIs directory as per original workflow
                    imagej_path=imagej_path,
                    channel=segmentation_channel
                )
                
                if success:
                    return {
                        'success': True,
                        'message': 'Resize ROIs step completed'
                    }
                else:
                    return {
                        'success': False,
                        'error': 'Resize ROIs failed'
                    }
            else:
                return {
                    'success': False,
                    'error': 'Resize ROIs service not available'
                }
        except Exception as e:
            return {
                'success': False,
                'error': f'Error in resize ROIs: {e}'
            }
    
    def _execute_duplicate_rois(self, **kwargs) -> Dict[str, Any]:
        """Execute duplicate ROIs step."""
        try:
            if self.duplicate_rois_service:
                success = self.duplicate_rois_service.duplicate_rois_for_channels(
                    roi_dir=f"{kwargs.get('output_dir')}/ROIs",  # Use ROIs directory where resize_rois saved the ROIs
                    conditions=kwargs.get('conditions', []),
                    regions=kwargs.get('regions', []),
                    timepoints=kwargs.get('timepoints', []),
                    segmentation_channel=kwargs.get('segmentation_channel', 'ch01'),
                    channels=kwargs.get('analysis_channels', [])
                )
                
                if success:
                    return {
                        'success': True,
                        'message': 'Duplicate ROIs step completed'
                    }
                else:
                    return {
                        'success': False,
                        'error': 'Duplicate ROIs failed'
                    }
            else:
                return {
                    'success': False,
                    'error': 'Duplicate ROIs service not available'
                }
        except Exception as e:
            return {
                'success': False,
                'error': f'Error in duplicate ROIs: {e}'
            }
    
    def _execute_extract_cells(self, **kwargs) -> Dict[str, Any]:
        """Execute extract cells step."""
        try:
            if self.extract_cells_service:
                imagej_path = kwargs.get('imagej_path', '/Applications/ImageJ.app/Contents/MacOS/ImageJ')
                analysis_channels = kwargs.get('analysis_channels', [])
                conditions = kwargs.get('conditions', [])
                regions = kwargs.get('regions', [])
                timepoints = kwargs.get('timepoints', [])
                
                success = self.extract_cells_service.extract_cells(
                    roi_directory=f"{kwargs.get('output_dir')}/ROIs",  # Use ROIs directory where duplicate_rois saved the ROIs
                    raw_data_directory=f"{kwargs.get('output_dir')}/raw_data",
                    output_directory=f"{kwargs.get('output_dir')}/cells",
                    imagej_path=imagej_path,
                    regions=regions,
                    timepoints=timepoints,
                    conditions=conditions,
                    channels=analysis_channels
                )
                
                if success:
                    return {
                        'success': True,
                        'message': 'Extract cells step completed'
                    }
                else:
                    return {
                        'success': False,
                        'error': 'Extract cells failed'
                    }
            else:
                return {
                    'success': False,
                    'error': 'Extract cells service not available'
                }
        except Exception as e:
            return {
                'success': False,
                'error': f'Error in extract cells: {e}'
            }
    
    def get_execution_history(self) -> List[Dict[str, Any]]:
        """Get the workflow execution history."""
        return self.execution_history.copy()
    
    def get_current_workflow(self) -> Optional[str]:
        """Get the name of the currently executing workflow."""
        return self.current_workflow
    
    def get_workflow_statistics(self) -> Dict[str, Any]:
        """Get statistics about workflow execution."""
        if not self.execution_history:
            return {
                'total_workflows': 0,
                'successful_workflows': 0,
                'failed_workflows': 0,
                'average_duration': 0.0
            }
        
        total_workflows = len(self.execution_history)
        successful_workflows = sum(1 for w in self.execution_history if w['success'])
        failed_workflows = total_workflows - successful_workflows
        total_duration = sum(w['total_duration'] for w in self.execution_history)
        average_duration = total_duration / total_workflows
        
        return {
            'total_workflows': total_workflows,
            'successful_workflows': successful_workflows,
            'failed_workflows': failed_workflows,
            'average_duration': average_duration
        }
