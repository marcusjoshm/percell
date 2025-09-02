#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Hexagonal Workflow Service for Single Cell Analysis

This service provides the same interface as the old WorkflowService but uses
the new hexagonal architecture services instead of calling legacy Python modules.
"""

from __future__ import annotations

from typing import List, Optional, Dict, Any
from percell.domain.ports import LoggingPort


class HexagonalWorkflowService:
    """
    Hexagonal implementation of the workflow service.
    
    This service provides the same interface as the old WorkflowService but uses
    the new hexagonal architecture services for actual execution.
    """

    def __init__(
        self,
        workflow_orchestration_service,
        logging_port: LoggingPort
    ):
        """
        Initialize the hexagonal workflow service.
        
        Args:
            workflow_orchestration_service: The workflow orchestration service
            logging_port: Port for logging operations
        """
        self.workflow_orchestration_service = workflow_orchestration_service
        self.logging_port = logging_port
        self.logger = logging_port.get_logger("HexagonalWorkflowService")

    def bin_images(
        self, 
        output_dir: str, 
        conditions: List[str], 
        regions: List[str], 
        timepoints: List[str], 
        channels: List[str]
    ) -> int:
        """
        Bin images using the hexagonal architecture.
        
        Args:
            output_dir: Output directory
            conditions: List of conditions
            regions: List of regions
            timepoints: List of timepoints
            channels: List of channels
            
        Returns:
            0 for success, non-zero for failure
        """
        try:
            self.logger.info("Starting image binning using hexagonal architecture...")
            
            result = self.workflow_orchestration_service._execute_workflow_step(
                'segmentation',
                input_dir=f"{output_dir}/raw_data",
                output_dir=output_dir,
                conditions=conditions,
                regions=regions,
                timepoints=timepoints,
                channels=channels
            )
            
            if result.get('success'):
                self.logger.info("Image binning completed successfully")
                return 0
            else:
                self.logger.error(f"Image binning failed: {result.get('error', 'Unknown error')}")
                return 1
                
        except Exception as e:
            self.logger.error(f"Error in bin_images: {e}")
            return 1

    def combine_masks(self, output_dir: str, analysis_channels: List[str]) -> int:
        """
        Combine masks using the hexagonal architecture.
        
        Args:
            output_dir: Output directory
            analysis_channels: List of analysis channels
            
        Returns:
            0 for success, non-zero for failure
        """
        try:
            self.logger.info("Starting mask combination using hexagonal architecture...")
            
            result = self.workflow_orchestration_service._execute_workflow_step(
                'analysis',
                input_dir=f"{output_dir}/grouped_masks",
                output_dir=output_dir,
                analysis_channels=analysis_channels
            )
            
            if result.get('success'):
                self.logger.info("Mask combination completed successfully")
                return 0
            else:
                self.logger.error(f"Mask combination failed: {result.get('error', 'Unknown error')}")
                return 1
                
        except Exception as e:
            self.logger.error(f"Error in combine_masks: {e}")
            return 1

    def create_cell_masks(
        self, 
        output_dir: str, 
        imagej_path: str, 
        analysis_channels: List[str]
    ) -> int:
        """
        Create cell masks using the hexagonal architecture.
        
        Args:
            output_dir: Output directory
            imagej_path: Path to ImageJ executable
            analysis_channels: List of analysis channels
            
        Returns:
            0 for success, non-zero for failure
        """
        try:
            self.logger.info("Starting cell mask creation using hexagonal architecture...")
            
            result = self.workflow_orchestration_service._execute_workflow_step(
                'analysis',
                input_dir=f"{output_dir}/ROIs",
                output_dir=output_dir,
                imagej_path=imagej_path,
                analysis_channels=analysis_channels
            )
            
            if result.get('success'):
                self.logger.info("Cell mask creation completed successfully")
                return 0
            else:
                self.logger.error(f"Cell mask creation failed: {result.get('error', 'Unknown error')}")
                return 1
                
        except Exception as e:
            self.logger.error(f"Error in create_cell_masks: {e}")
            return 1

    def analyze_cell_masks(
        self, 
        output_dir: str, 
        imagej_path: str, 
        regions: Optional[List[str]], 
        timepoints: Optional[List[str]], 
        analysis_channels: List[str]
    ) -> int:
        """
        Analyze cell masks using the hexagonal architecture.
        
        Args:
            output_dir: Output directory
            imagej_path: Path to ImageJ executable
            regions: Optional list of regions
            timepoints: Optional list of timepoints
            analysis_channels: List of analysis channels
            
        Returns:
            0 for success, non-zero for failure
        """
        try:
            self.logger.info("Starting cell mask analysis using hexagonal architecture...")
            
            result = self.workflow_orchestration_service._execute_workflow_step(
                'analysis',
                input_dir=f"{output_dir}/masks",
                output_dir=output_dir,
                imagej_path=imagej_path,
                regions=regions,
                timepoints=timepoints,
                analysis_channels=analysis_channels
            )
            
            if result.get('success'):
                self.logger.info("Cell mask analysis completed successfully")
                return 0
            else:
                self.logger.error(f"Cell mask analysis failed: {result.get('error', 'Unknown error')}")
                return 1
                
        except Exception as e:
            self.logger.error(f"Error in analyze_cell_masks: {e}")
            return 1

    def threshold_grouped_cells(
        self, 
        output_dir: str, 
        imagej_path: str, 
        analysis_channels: List[str]
    ) -> int:
        """
        Threshold grouped cells using the hexagonal architecture.
        
        Args:
            output_dir: Output directory
            imagej_path: Path to ImageJ executable
            analysis_channels: List of analysis channels
            
        Returns:
            0 for success, non-zero for failure
        """
        try:
            self.logger.info("Starting grouped cell thresholding using hexagonal architecture...")
            
            result = self.workflow_orchestration_service._execute_workflow_step(
                'threshold_grouped_cells',
                input_dir=f"{output_dir}/grouped_cells",
                output_dir=output_dir,
                imagej_path=imagej_path,
                analysis_channels=analysis_channels
            )
            
            if result.get('success'):
                self.logger.info("Grouped cell thresholding completed successfully")
                return 0
            else:
                self.logger.error(f"Grouped cell thresholding failed: {result.get('error', 'Unknown error')}")
                return 1
                
        except Exception as e:
            self.logger.error(f"Error in threshold_grouped_cells: {e}")
            return 1

    def include_group_metadata(
        self, 
        output_dir: str, 
        analysis_channels: List[str]
    ) -> int:
        """
        Include group metadata using the hexagonal architecture.
        
        Args:
            output_dir: Output directory
            analysis_channels: List of analysis channels
            
        Returns:
            0 for success, non-zero for failure
        """
        try:
            self.logger.info("Starting group metadata inclusion using hexagonal architecture...")
            
            result = self.workflow_orchestration_service._execute_workflow_step(
                'analysis',
                input_dir=f"{output_dir}/grouped_cells",
                output_dir=output_dir,
                analysis_channels=analysis_channels
            )
            
            if result.get('success'):
                self.logger.info("Group metadata inclusion completed successfully")
                return 0
            else:
                self.logger.error(f"Group metadata inclusion failed: {result.get('error', 'Unknown error')}")
                return 1
                
        except Exception as e:
            self.logger.error(f"Error in include_group_metadata: {e}")
            return 1

    def track_rois(self, output_dir: str, timepoints: List[str]) -> int:
        """
        Track ROIs using the hexagonal architecture.
        
        Args:
            output_dir: Output directory
            timepoints: List of timepoints
            
        Returns:
            0 for success, non-zero for failure
        """
        try:
            self.logger.info("Starting ROI tracking using hexagonal architecture...")
            
            result = self.workflow_orchestration_service._execute_workflow_step(
                'process_single_cell',
                input_dir=f"{output_dir}/preprocessed",
                output_dir=output_dir,
                timepoints=timepoints
            )
            
            if result.get('success'):
                self.logger.info("ROI tracking completed successfully")
                return 0
            else:
                self.logger.error(f"ROI tracking failed: {result.get('error', 'Unknown error')}")
                return 1
                
        except Exception as e:
            self.logger.error(f"Error in track_rois: {e}")
            return 1

    def resize_rois(self, output_dir: str) -> int:
        """
        Resize ROIs using the hexagonal architecture.
        
        Args:
            output_dir: Output directory
            
        Returns:
            0 for success, non-zero for failure
        """
        try:
            self.logger.info("Starting ROI resizing using hexagonal architecture...")
            
            result = self.workflow_orchestration_service._execute_workflow_step(
                'process_single_cell',
                input_dir=f"{output_dir}/tracked_rois",
                output_dir=output_dir
            )
            
            if result.get('success'):
                self.logger.info("ROI resizing completed successfully")
                return 0
            else:
                self.logger.error(f"ROI resizing failed: {result.get('error', 'Unknown error')}")
                return 1
                
        except Exception as e:
            self.logger.error(f"Error in resize_rois: {e}")
            return 1

    def duplicate_rois_for_channels(
        self, 
        output_dir: str, 
        analysis_channels: List[str]
    ) -> int:
        """
        Duplicate ROIs for channels using the hexagonal architecture.
        
        Args:
            output_dir: Output directory
            analysis_channels: List of analysis channels
            
        Returns:
            0 for success, non-zero for failure
        """
        try:
            self.logger.info("Starting ROI duplication using hexagonal architecture...")
            
            result = self.workflow_orchestration_service._execute_workflow_step(
                'process_single_cell',
                input_dir=f"{output_dir}/resized_rois",
                output_dir=output_dir,
                analysis_channels=analysis_channels
            )
            
            if result.get('success'):
                self.logger.info("ROI duplication completed successfully")
                return 0
            else:
                self.logger.error(f"ROI duplication failed: {result.get('error', 'Unknown error')}")
                return 1
                
        except Exception as e:
            self.logger.error(f"Error in duplicate_rois_for_channels: {e}")
            return 1

    def extract_cells(self, output_dir: str) -> int:
        """
        Extract cells using the hexagonal architecture.
        
        Args:
            output_dir: Output directory
            
        Returns:
            0 for success, non-zero for failure
        """
        try:
            self.logger.info("Starting cell extraction using hexagonal architecture...")
            
            result = self.workflow_orchestration_service._execute_workflow_step(
                'process_single_cell',
                input_dir=f"{output_dir}/duplicated_rois",
                output_dir=output_dir
            )
            
            if result.get('success'):
                self.logger.info("Cell extraction completed successfully")
                return 0
            else:
                self.logger.error(f"Cell extraction failed: {result.get('error', 'Unknown error')}")
                return 1
                
        except Exception as e:
            self.logger.error(f"Error in extract_cells: {e}")
            return 1

    def group_cells(
        self, 
        output_dir: str, 
        bins: int, 
        analysis_channels: List[str]
    ) -> int:
        """
        Group cells using the hexagonal architecture.
        
        Args:
            output_dir: Output directory
            bins: Number of bins for grouping
            analysis_channels: List of analysis channels
            
        Returns:
            0 for success, non-zero for failure
        """
        try:
            self.logger.info("Starting cell grouping using hexagonal architecture...")
            
            result = self.workflow_orchestration_service._execute_workflow_step(
                'group_cells',
                input_dir=f"{output_dir}/extracted_cells",
                output_dir=output_dir,
                bins=bins,
                analysis_channels=analysis_channels
            )
            
            if result.get('success'):
                self.logger.info("Cell grouping completed successfully")
                return 0
            else:
                self.logger.error(f"Cell grouping failed: {result.get('error', 'Unknown error')}")
                return 1
                
        except Exception as e:
            self.logger.error(f"Error in group_cells: {e}")
            return 1
