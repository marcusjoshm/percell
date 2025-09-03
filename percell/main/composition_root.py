"""
Composition Root for Hexagonal Architecture.

This module wires all dependencies together, implementing the dependency
inversion principle. All dependencies are created here and injected
into the application services.
"""

from typing import Dict, Any, Optional, List
from pathlib import Path

# Domain ports
from percell.domain.ports import (
    SubprocessPort,
    FileSystemPort,
    LoggingPort,
    ConfigurationPort,
    ImageProcessingService,
    StageRegistryPort
)

# Infrastructure adapters
from percell.infrastructure.adapters.subprocess_adapter import SubprocessAdapter
from percell.infrastructure.adapters.filesystem_adapter import FileSystemAdapter
from percell.infrastructure.adapters.configuration_adapter import ConfigurationAdapter
from percell.infrastructure.adapters.logging_adapter import LoggingAdapter
from percell.infrastructure.adapters.imagej_adapter import ImageJAdapter
from percell.infrastructure.adapters.stage_registry_adapter import StageRegistryAdapter
from percell.infrastructure.progress_reporter import ProgressReporter

# Application services
from percell.application.services.create_cell_masks_service import CreateCellMasksService
from percell.application.services.extract_cells_service import ExtractCellsService
from percell.application.services.analyze_cell_masks_service import AnalyzeCellMasksService
from percell.application.services.measure_roi_area_service import MeasureROIAreaService
from percell.application.services.cleanup_directories_service import CleanupDirectoriesService
from percell.application.services.combine_masks_service import CombineMasksService
from percell.application.services.bin_images_service import BinImagesService
from percell.application.services.group_cells_service import GroupCellsService
from percell.application.services.interactive_thresholding_service import InteractiveThresholdingService
from percell.application.services.advanced_workflow_service import AdvancedWorkflowService
from percell.application.services.duplicate_rois_service import DuplicateROIsService
from percell.application.services.group_metadata_service import GroupMetadataService
from percell.application.services.track_rois_service import TrackROIsService
from percell.application.services.resize_rois_service import ResizeROIsService
from percell.application.services.directory_management_service import DirectoryManagementService
from percell.application.services.workflow_orchestration_service import WorkflowOrchestrationService
from percell.application.services.workflow_definition_service import WorkflowDefinitionService
from percell.application.services.workflow_execution_service import WorkflowExecutionService
from percell.application.services.hexagonal_workflow_service import HexagonalWorkflowService
from percell.application.services.comprehensive_workflow_service import ComprehensiveWorkflowService
from percell.application.services.data_selection_service import DataSelectionService

# Configuration and logging (moved to infrastructure layer)
from percell.infrastructure.configuration.config import Config, create_default_config
from percell.infrastructure.logging.logger import PipelineLogger


class CompositionRoot:
    """
    Composition root that wires all dependencies together.
    
    This class follows the dependency inversion principle by:
    1. Creating concrete implementations of domain ports
    2. Injecting them into application services
    3. Providing a clean interface for the application to use
    """
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize the composition root.
        
        Args:
            config_path: Optional path to configuration file
        """
        self.config = self._create_configuration(config_path)
        self._wired_services: Dict[str, Any] = {}
        self._wire_dependencies()
    
    def _create_configuration(self, config_path: Optional[str]) -> Config:
        """Create and load configuration."""
        if config_path and Path(config_path).exists():
            return Config.from_file(config_path)
        else:
            # Create a temporary config path for testing
            import tempfile
            temp_config_path = Path(tempfile.gettempdir()) / "percell_test_config.json"
            return create_default_config(str(temp_config_path))
    
    def _wire_dependencies(self):
        """Wire all dependencies together."""
        # Create infrastructure adapters
        self._create_infrastructure_adapters()
        
        # Create application services
        self._create_application_services()
    
    def _create_infrastructure_adapters(self):
        """Create infrastructure adapters implementing domain ports."""
        # Create progress reporter
        progress_reporter = ProgressReporter()
        
        # Create subprocess adapter
        subprocess_adapter = SubprocessAdapter(progress_reporter)
        
        # Create file system adapter
        filesystem_adapter = FileSystemAdapter(self.config)
        
        # Create configuration adapter
        config_adapter = ConfigurationAdapter(str(self.config.config_path))
        
        # Create logging adapter
        logging_adapter = LoggingAdapter()
        
        # Create ImageJ adapter
        imagej_adapter = ImageJAdapter(str(self.config.get('imagej_path', '/usr/bin/imagej')))
        
        # Create stage registry adapter
        stage_registry_adapter = StageRegistryAdapter()
        
        # Store adapters
        self._wired_services['subprocess_port'] = subprocess_adapter
        self._wired_services['filesystem_port'] = filesystem_adapter
        self._wired_services['logging_port'] = logging_adapter
        self._wired_services['configuration_port'] = config_adapter
        self._wired_services['image_processing_service'] = imagej_adapter
        self._wired_services['stage_registry_port'] = stage_registry_adapter
        self._wired_services['progress_reporter'] = progress_reporter
    
    def _create_application_services(self):
        """Create application services with injected dependencies."""
        # Create cell masks service
        create_cell_masks_service = CreateCellMasksService(
            subprocess_port=self._wired_services['subprocess_port'],
            filesystem_port=self._wired_services['filesystem_port'],
            logging_port=self._wired_services['logging_port'],
            image_processing_service=self._wired_services['image_processing_service']
        )
        
        # Create extract cells service
        extract_cells_service = ExtractCellsService(
            subprocess_port=self._wired_services['subprocess_port'],
            filesystem_port=self._wired_services['filesystem_port'],
            logging_port=self._wired_services['logging_port'],
            image_processing_service=self._wired_services['image_processing_service']
        )
        
        # Create analyze cell masks service
        analyze_cell_masks_service = AnalyzeCellMasksService(
            subprocess_port=self._wired_services['subprocess_port'],
            filesystem_port=self._wired_services['filesystem_port'],
            logging_port=self._wired_services['logging_port'],
            image_processing_service=self._wired_services['image_processing_service']
        )
        
        # Create measure ROI area service
        measure_roi_area_service = MeasureROIAreaService(
            subprocess_port=self._wired_services['subprocess_port'],
            filesystem_port=self._wired_services['filesystem_port'],
            logging_port=self._wired_services['logging_port'],
            image_processing_service=self._wired_services['image_processing_service']
        )
        
        # Create cleanup directories service
        cleanup_directories_service = CleanupDirectoriesService(
            filesystem_port=self._wired_services['filesystem_port'],
            logging_port=self._wired_services['logging_port']
        )
        
        # Create combine masks service
        combine_masks_service = CombineMasksService(
            filesystem_port=self._wired_services['filesystem_port'],
            logging_port=self._wired_services['logging_port']
        )
        
        # Create bin images service
        bin_images_service = BinImagesService(
            filesystem_port=self._wired_services['filesystem_port'],
            logging_port=self._wired_services['logging_port']
        )
        
        # Create group cells service
        group_cells_service = GroupCellsService(
            filesystem_port=self._wired_services['filesystem_port'],
            logging_port=self._wired_services['logging_port']
        )
        
        # Create interactive thresholding service
        interactive_thresholding_service = InteractiveThresholdingService(
            filesystem_port=self._wired_services['filesystem_port'],
            logging_port=self._wired_services['logging_port'],
            subprocess_port=self._wired_services['subprocess_port']
        )
        
        # Create advanced workflow service
        advanced_workflow_service = AdvancedWorkflowService(
            filesystem_port=self._wired_services['filesystem_port'],
            logging_port=self._wired_services['logging_port'],
            subprocess_port=self._wired_services['subprocess_port'],
            configuration_port=self._wired_services['configuration_port']
        )
        
        # Create duplicate ROIs service
        duplicate_rois_service = DuplicateROIsService(
            filesystem_port=self._wired_services['filesystem_port'],
            logging_port=self._wired_services['logging_port']
        )
        
        # Create group metadata service
        group_metadata_service = GroupMetadataService(
            filesystem_port=self._wired_services['filesystem_port'],
            logging_port=self._wired_services['logging_port']
        )
        
        # Create track ROIs service
        track_rois_service = TrackROIsService(
            filesystem_port=self._wired_services['filesystem_port'],
            logging_port=self._wired_services['logging_port']
        )
        
        # Create resize ROIs service
        resize_rois_service = ResizeROIsService(
            subprocess_port=self._wired_services['subprocess_port'],
            filesystem_port=self._wired_services['filesystem_port'],
            logging_port=self._wired_services['logging_port'],
            image_processing_service=self._wired_services['image_processing_service']
        )
        
        # Create directory management service
        directory_management_service = DirectoryManagementService(
            filesystem_port=self._wired_services['filesystem_port'],
            logging_port=self._wired_services['logging_port'],
            configuration_port=self._wired_services['configuration_port']
        )

        # Create data selection service
        data_selection_service = DataSelectionService(
            filesystem_port=self._wired_services['filesystem_port'],
            logging_port=self._wired_services['logging_port'],
            subprocess_port=self._wired_services['subprocess_port']
        )
        
        # Create workflow orchestration service
        workflow_orchestration_service = WorkflowOrchestrationService(
            filesystem_port=self._wired_services['filesystem_port'],
            logging_port=self._wired_services['logging_port'],
            configuration_port=self._wired_services['configuration_port'],
            # Inject workflow services
            bin_images_service=bin_images_service,
            combine_masks_service=combine_masks_service,
            create_cell_masks_service=create_cell_masks_service,
            analyze_cell_masks_service=analyze_cell_masks_service,
            interactive_thresholding_service=interactive_thresholding_service,
            include_group_metadata_service=group_metadata_service,
            track_rois_service=track_rois_service,
            resize_rois_service=resize_rois_service,
            duplicate_rois_service=duplicate_rois_service,
            extract_cells_service=extract_cells_service,
            group_cells_service=group_cells_service,
            measure_roi_area_service=measure_roi_area_service,
            cleanup_directories_service=cleanup_directories_service,
            directory_management_service=directory_management_service,
            data_selection_service=data_selection_service
        )
        
        # Create workflow definition service
        workflow_definition_service = WorkflowDefinitionService(
            filesystem_port=self._wired_services['filesystem_port'],
            logging_port=self._wired_services['logging_port'],
            configuration_port=self._wired_services['configuration_port']
        )
        
        # Create workflow execution service
        workflow_execution_service = WorkflowExecutionService(
            filesystem_port=self._wired_services['filesystem_port'],
            logging_port=self._wired_services['logging_port'],
            configuration_port=self._wired_services['configuration_port']
        )
        
        # Create hexagonal workflow service
        hexagonal_workflow_service = HexagonalWorkflowService(
            workflow_orchestration_service=workflow_orchestration_service,
            logging_port=self._wired_services['logging_port']
        )
        
        # Create comprehensive workflow service
        comprehensive_workflow_service = ComprehensiveWorkflowService(
            filesystem_port=self._wired_services['filesystem_port'],
            logging_port=self._wired_services['logging_port'],
            configuration_port=self._wired_services['configuration_port'],
            # Inject all workflow services
            bin_images_service=bin_images_service,
            combine_masks_service=combine_masks_service,
            create_cell_masks_service=create_cell_masks_service,
            analyze_cell_masks_service=analyze_cell_masks_service,
            interactive_thresholding_service=interactive_thresholding_service,
            include_group_metadata_service=group_metadata_service,
            track_rois_service=track_rois_service,
            resize_rois_service=resize_rois_service,
            duplicate_rois_service=duplicate_rois_service,
            extract_cells_service=extract_cells_service,
            group_cells_service=group_cells_service,
            measure_roi_area_service=measure_roi_area_service,
            cleanup_directories_service=cleanup_directories_service,
            directory_management_service=directory_management_service
        )
        
        self._wired_services['create_cell_masks_service'] = create_cell_masks_service
        self._wired_services['extract_cells_service'] = extract_cells_service
        self._wired_services['analyze_cell_masks_service'] = analyze_cell_masks_service
        self._wired_services['measure_roi_area_service'] = measure_roi_area_service
        self._wired_services['cleanup_directories_service'] = cleanup_directories_service
        self._wired_services['combine_masks_service'] = combine_masks_service
        self._wired_services['bin_images_service'] = bin_images_service
        self._wired_services['group_cells_service'] = group_cells_service
        self._wired_services['interactive_thresholding_service'] = interactive_thresholding_service
        self._wired_services['advanced_workflow_service'] = advanced_workflow_service
        self._wired_services['duplicate_rois_service'] = duplicate_rois_service
        self._wired_services['group_metadata_service'] = group_metadata_service
        self._wired_services['track_rois_service'] = track_rois_service
        self._wired_services['directory_management_service'] = directory_management_service
        self._wired_services['data_selection_service'] = data_selection_service
        self._wired_services['workflow_orchestration_service'] = workflow_orchestration_service
        self._wired_services['workflow_definition_service'] = workflow_definition_service
        self._wired_services['workflow_execution_service'] = workflow_execution_service
        self._wired_services['hexagonal_workflow_service'] = hexagonal_workflow_service
        self._wired_services['comprehensive_workflow_service'] = comprehensive_workflow_service
    
    def get_service(self, service_name: str) -> Any:
        """
        Get a service by name.
        
        Args:
            service_name: Name of the service to retrieve
            
        Returns:
            The requested service
            
        Raises:
            KeyError: If service is not found
        """
        if service_name not in self._wired_services:
            raise KeyError(f"Service '{service_name}' not found in composition root")
        
        return self._wired_services[service_name]
    
    def get_config(self) -> Config:
        """Get the configuration."""
        return self.config
    
    def list_available_services(self) -> List[str]:
        """List all available services."""
        return list(self._wired_services.keys())


# Global composition root instance
_composition_root: Optional[CompositionRoot] = None


def get_composition_root(config_path: Optional[str] = None) -> CompositionRoot:
    """
    Get the global composition root instance.
    
    Args:
        config_path: Optional path to configuration file
        
    Returns:
        The composition root instance
    """
    global _composition_root
    
    if _composition_root is None:
        _composition_root = CompositionRoot(config_path)
    
    return _composition_root


def reset_composition_root():
    """Reset the global composition root (useful for testing)."""
    global _composition_root
    _composition_root = None
