"""
Workflow Configuration Service

Provides centralized workflow configuration management for the Percell application.
This service acts as the single source of truth for which tools are used in each
stage of the analysis workflow.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Optional, Tuple
from percell.domain.services.configuration_service import ConfigurationService


@dataclass
class WorkflowTool:
    """Represents a tool that can be used in a workflow stage."""
    stage_name: str
    display_name: str
    description: str


class WorkflowConfigurationService:
    """
    Manages workflow configuration and tool selection.

    This service provides a centralized way to configure which tools are used
    for different stages of the microscopy analysis workflow. It serves as the
    single source of truth for workflow configuration throughout the application.
    """

    # Define available tools for each workflow stage
    SEGMENTATION_TOOLS = {
        'cellpose': WorkflowTool(
            stage_name='cellpose_segmentation',
            display_name='Cellpose',
            description='SAM-based segmentation using Cellpose'
        ),
    }

    THRESHOLDING_TOOLS = {
        'semi_auto': WorkflowTool(
            stage_name='semi_auto_threshold_grouped_cells',
            display_name='Semi-Auto Threshold',
            description='Interactive ImageJ thresholding with user ROI selection'
        ),
        'full_auto': WorkflowTool(
            stage_name='full_auto_threshold_grouped_cells',
            display_name='Full-Auto Threshold',
            description='Automatic Otsu thresholding without user interaction'
        ),
    }

    PROCESSING_TOOLS = {
        'cellpose': WorkflowTool(
            stage_name='process_cellpose_single_cell',
            display_name='Cellpose Processing',
            description='Process single-cell data from Cellpose segmentation'
        ),
    }

    def __init__(self, config: ConfigurationService):
        """
        Initialize the workflow configuration service.

        Args:
            config: Configuration service for reading/writing workflow settings
        """
        self.config = config
        self._ensure_defaults()

    def _ensure_defaults(self) -> None:
        """Ensure default workflow configuration exists."""
        if not self.config.has('workflow.segmentation_tool'):
            self.config.set('workflow.segmentation_tool', 'cellpose')
        if not self.config.has('workflow.thresholding_tool'):
            self.config.set('workflow.thresholding_tool', 'semi_auto')
        if not self.config.has('workflow.processing_tool'):
            self.config.set('workflow.processing_tool', 'cellpose')
        self.config.save()

    # Segmentation tool management

    def get_segmentation_tool(self) -> str:
        """Get the configured segmentation tool key."""
        return self.config.get('workflow.segmentation_tool', 'cellpose')

    def set_segmentation_tool(self, tool_key: str) -> None:
        """
        Set the segmentation tool.

        Args:
            tool_key: Key of the tool to use (e.g., 'cellpose')

        Raises:
            ValueError: If tool_key is not valid
        """
        if tool_key not in self.SEGMENTATION_TOOLS:
            raise ValueError(
                f"Invalid segmentation tool: {tool_key}. "
                f"Valid options: {list(self.SEGMENTATION_TOOLS.keys())}"
            )
        self.config.set('workflow.segmentation_tool', tool_key)
        self.config.save()

    def get_segmentation_stage_name(self) -> str:
        """Get the stage name for the configured segmentation tool."""
        tool_key = self.get_segmentation_tool()
        return self.SEGMENTATION_TOOLS[tool_key].stage_name

    def get_segmentation_display_name(self) -> str:
        """Get the display name for the configured segmentation tool."""
        tool_key = self.get_segmentation_tool()
        return self.SEGMENTATION_TOOLS[tool_key].display_name

    # Thresholding tool management

    def get_thresholding_tool(self) -> str:
        """Get the configured thresholding tool key."""
        return self.config.get('workflow.thresholding_tool', 'semi_auto')

    def set_thresholding_tool(self, tool_key: str) -> None:
        """
        Set the thresholding tool.

        Args:
            tool_key: Key of the tool to use (e.g., 'semi_auto', 'full_auto')

        Raises:
            ValueError: If tool_key is not valid
        """
        if tool_key not in self.THRESHOLDING_TOOLS:
            raise ValueError(
                f"Invalid thresholding tool: {tool_key}. "
                f"Valid options: {list(self.THRESHOLDING_TOOLS.keys())}"
            )
        self.config.set('workflow.thresholding_tool', tool_key)
        self.config.save()

    def get_thresholding_stage_name(self) -> str:
        """Get the stage name for the configured thresholding tool."""
        tool_key = self.get_thresholding_tool()
        return self.THRESHOLDING_TOOLS[tool_key].stage_name

    def get_thresholding_display_name(self) -> str:
        """Get the display name for the configured thresholding tool."""
        tool_key = self.get_thresholding_tool()
        return self.THRESHOLDING_TOOLS[tool_key].display_name

    # Processing tool management

    def get_processing_tool(self) -> str:
        """Get the configured processing tool key."""
        return self.config.get('workflow.processing_tool', 'cellpose')

    def set_processing_tool(self, tool_key: str) -> None:
        """
        Set the processing tool.

        Args:
            tool_key: Key of the tool to use (e.g., 'cellpose')

        Raises:
            ValueError: If tool_key is not valid
        """
        if tool_key not in self.PROCESSING_TOOLS:
            raise ValueError(
                f"Invalid processing tool: {tool_key}. "
                f"Valid options: {list(self.PROCESSING_TOOLS.keys())}"
            )
        self.config.set('workflow.processing_tool', tool_key)
        self.config.save()

    def get_processing_stage_name(self) -> str:
        """Get the stage name for the configured processing tool."""
        tool_key = self.get_processing_tool()
        return self.PROCESSING_TOOLS[tool_key].stage_name

    def get_processing_display_name(self) -> str:
        """Get the display name for the configured processing tool."""
        tool_key = self.get_processing_tool()
        return self.PROCESSING_TOOLS[tool_key].display_name

    # Complete workflow stages

    def get_complete_workflow_stages(self) -> list[Tuple[str, str]]:
        """
        Get the complete workflow stages based on current configuration.

        Returns:
            List of (stage_name, display_name) tuples in execution order
        """
        return [
            ('data_selection', 'Data Selection'),
            (self.get_segmentation_stage_name(), self.get_segmentation_display_name()),
            (self.get_processing_stage_name(), self.get_processing_display_name()),
            (self.get_thresholding_stage_name(), self.get_thresholding_display_name()),
            ('measure_roi_area', 'Measure ROI Areas'),
            ('analysis', 'Analysis')
        ]

    # Tool information

    def get_available_segmentation_tools(self) -> Dict[str, WorkflowTool]:
        """Get all available segmentation tools."""
        return self.SEGMENTATION_TOOLS.copy()

    def get_available_thresholding_tools(self) -> Dict[str, WorkflowTool]:
        """Get all available thresholding tools."""
        return self.THRESHOLDING_TOOLS.copy()

    def get_available_processing_tools(self) -> Dict[str, WorkflowTool]:
        """Get all available processing tools."""
        return self.PROCESSING_TOOLS.copy()

    def get_workflow_summary(self) -> Dict[str, str]:
        """
        Get a summary of the current workflow configuration.

        Returns:
            Dictionary with workflow stage categories and their configured tools
        """
        return {
            'segmentation': self.get_segmentation_display_name(),
            'processing': self.get_processing_display_name(),
            'thresholding': self.get_thresholding_display_name(),
        }


def create_workflow_configuration_service(
    config: ConfigurationService
) -> WorkflowConfigurationService:
    """
    Create a workflow configuration service.

    Args:
        config: Configuration service for reading/writing settings

    Returns:
        Initialized workflow configuration service
    """
    return WorkflowConfigurationService(config)
