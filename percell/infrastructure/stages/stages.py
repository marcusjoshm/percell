"""
Stage Execution Framework for Microscopy Single-Cell Analysis Pipeline

Provides base classes and execution framework for pipeline stages.
"""

import time
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from pathlib import Path

from percell.infrastructure.configuration.config import Config
from percell.infrastructure.logging.logger import PipelineLogger, ModuleLogger
from typing import Any
try:
    # Optional event bus for loose coupling
    from percell.services.event_bus import PipelineEventBus, StageStarted, StageCompleted
except Exception:  # pragma: no cover - optional dependency during transition
    PipelineEventBus = None  # type: ignore
    StageStarted = None  # type: ignore
    StageCompleted = None  # type: ignore


class StageError(Exception):
    """Custom exception for stage execution errors."""
    pass


class StageBase(ABC):
    """
    Base class for all pipeline stages.
    
    Provides common functionality for stage execution, logging, and error handling.
    """
    
    def __init__(self, config: Config, logger: PipelineLogger, stage_name: str, event_bus: Any = None):
        """
        Initialize the stage.
        
        Args:
            config: Pipeline configuration
            logger: Pipeline logger
            stage_name: Name of the stage
        """
        self.config = config
        self.pipeline_logger = logger
        self.stage_name = stage_name
        self.logger = ModuleLogger(stage_name, logger)
        self.start_time: Optional[float] = None
        self.end_time: Optional[float] = None
        self.event_bus = event_bus
        
    @abstractmethod
    def run(self, **kwargs) -> bool:
        """
        Execute the stage.
        
        Args:
            **kwargs: Stage-specific arguments
            
        Returns:
            True if successful, False otherwise
        """
        pass
    
    @abstractmethod
    def validate_inputs(self, **kwargs) -> bool:
        """
        Validate stage inputs.
        
        Args:
            **kwargs: Stage-specific arguments
            
        Returns:
            True if inputs are valid, False otherwise
        """
        pass
    
    def get_description(self) -> str:
        """
        Get stage description.
        
        Returns:
            Stage description string
        """
        return f"Executing {self.stage_name}"
    
    def setup(self, **kwargs) -> bool:
        """
        Setup stage (called before run).
        
        Args:
            **kwargs: Stage-specific arguments
            
        Returns:
            True if setup successful, False otherwise
        """
        return True
    
    def cleanup(self, **kwargs) -> bool:
        """
        Cleanup stage (called after run).
        
        Args:
            **kwargs: Stage-specific arguments
            
        Returns:
            True if cleanup successful, False otherwise
        """
        return True
    
    def execute(self, **kwargs) -> bool:
        """
        Execute the stage with setup and cleanup.
        
        Args:
            **kwargs: Stage-specific arguments
            
        Returns:
            True if successful, False otherwise
        """
        try:
            self.start_time = time.time()
            self.logger.info(f"Starting {self.stage_name}")
            if self.event_bus and StageStarted:
                try:
                    self.event_bus.publish(StageStarted(stage_name=self.stage_name))
                except Exception:
                    pass
            
            # Setup
            if not self.setup(**kwargs):
                self.logger.error(f"Setup failed for {self.stage_name}")
                return False
            
            # Validate inputs
            if not self.validate_inputs(**kwargs):
                self.logger.error(f"Input validation failed for {self.stage_name}")
                return False
            
            # Run stage
            success = self.run(**kwargs)
            
            # Cleanup
            if not self.cleanup(**kwargs):
                self.logger.warning(f"Cleanup failed for {self.stage_name}")
            
            self.end_time = time.time()
            duration = self.get_duration()
            
            if success:
                self.pipeline_logger.log_stage_complete(self.stage_name, duration)
                self.logger.info(f"Completed {self.stage_name} successfully")
                if self.event_bus and StageCompleted:
                    try:
                        self.event_bus.publish(StageCompleted(stage_name=self.stage_name, success=True))
                    except Exception:
                        pass
            else:
                self.pipeline_logger.log_stage_failed(self.stage_name, "Stage execution failed")
                self.logger.error(f"Failed to complete {self.stage_name}")
                if self.event_bus and StageCompleted:
                    try:
                        self.event_bus.publish(StageCompleted(stage_name=self.stage_name, success=False))
                    except Exception:
                        pass
            
            return success
            
        except Exception as e:
            self.end_time = time.time()
            self.pipeline_logger.log_stage_failed(self.stage_name, str(e))
            self.logger.error(f"Exception in {self.stage_name}: {e}")
            return False
    
    def get_duration(self) -> Optional[float]:
        """
        Get stage execution duration.
        
        Returns:
            Duration in seconds, or None if not executed
        """
        if self.start_time is not None and self.end_time is not None:
            return self.end_time - self.start_time
        return None


class FileProcessingStage(StageBase):
    """
    Base class for stages that process files.
    
    Provides common file processing functionality.
    """
    
    def __init__(self, config: Config, logger: PipelineLogger, stage_name: str):
        """Initialize file processing stage."""
        super().__init__(config, logger, stage_name)
        self.processed_files = []
        self.failed_files = []
    
    def process_file(self, file_path: str, **kwargs) -> bool:
        """
        Process a single file.
        
        Args:
            file_path: Path to file to process
            **kwargs: Additional arguments
            
        Returns:
            True if successful, False otherwise
        """
        try:
            self.logger.debug(f"Processing file: {file_path}")
            success = self._process_file_impl(file_path, **kwargs)
            
            if success:
                self.processed_files.append(file_path)
                self.logger.log_file_processed(file_path, True)
            else:
                self.failed_files.append(file_path)
                self.logger.log_file_processed(file_path, False)
            
            return success
            
        except Exception as e:
            self.failed_files.append(file_path)
            self.logger.error(f"Error processing file {file_path}: {e}")
            return False
    
    @abstractmethod
    def _process_file_impl(self, file_path: str, **kwargs) -> bool:
        """
        Implement file processing logic.
        
        Args:
            file_path: Path to file to process
            **kwargs: Additional arguments
            
        Returns:
            True if successful, False otherwise
        """
        pass
    
    def get_processing_summary(self) -> Dict[str, Any]:
        """
        Get processing summary.
        
        Returns:
            Dictionary with processing statistics
        """
        return {
            'stage_name': self.stage_name,
            'total_files': len(self.processed_files) + len(self.failed_files),
            'processed_files': len(self.processed_files),
            'failed_files': len(self.failed_files),
            'success_rate': len(self.processed_files) / (len(self.processed_files) + len(self.failed_files)) if (len(self.processed_files) + len(self.failed_files)) > 0 else 0,
            'duration': self.get_duration(),
            'processed_file_list': self.processed_files,
            'failed_file_list': self.failed_files
        }


class StageRegistry:
    """
    Registry for pipeline stages.
    
    Manages stage registration and retrieval.
    """
    
    def __init__(self):
        """Initialize stage registry."""
        self.stages = {}
        self.stage_order = {}
    
    def register(self, stage_name: str, stage_class: type, order: Optional[int] = None) -> None:
        """
        Register a stage.
        
        Args:
            stage_name: Name of the stage
            stage_class: Stage class
            order: Execution order (optional)
        """
        self.stages[stage_name] = stage_class
        if order is not None:
            self.stage_order[stage_name] = order
    
    def get_stage_class(self, stage_name: str) -> Optional[type]:
        """
        Get stage class by name.
        
        Args:
            stage_name: Name of the stage
            
        Returns:
            Stage class or None if not found
        """
        return self.stages.get(stage_name)
    
    def get_available_stages(self) -> List[str]:
        """
        Get list of available stage names.
        
        Returns:
            List of stage names
        """
        return list(self.stages.keys())
    
    def get_stage_order(self) -> List[str]:
        """
        Get stages in execution order.
        
        Returns:
            List of stage names in order
        """
        sorted_stages = sorted(self.stage_order.items(), key=lambda x: x[1])
        return [stage_name for stage_name, _ in sorted_stages]


class StageExecutor:
    """
    Executes pipeline stages.
    
    Manages stage execution and provides execution summaries.
    """
    
    def __init__(self, config: Config, logger: PipelineLogger, registry: StageRegistry, event_bus: Any = None):
        """
        Initialize stage executor.
        
        Args:
            config: Pipeline configuration
            logger: Pipeline logger
            registry: Stage registry
        """
        self.config = config
        self.logger = logger
        self.registry = registry
        self.execution_history = []
        self.event_bus = event_bus
    
    def get_data_selection_filters(self) -> Dict[str, Any]:
        """Return normalized Data Selection filters from config for stage consumption.

        Keys:
        - conditions: Optional[List[str]]
        - regions: Optional[List[str]]
        - timepoints: Optional[List[str]]
        - segmentation_channel: Optional[str]
        - analysis_channels: Optional[List[str]]
        """
        ds = self.config.get('data_selection') or {}
        return {
            'conditions': ds.get('selected_conditions') or None,
            'regions': ds.get('selected_regions') or None,
            'timepoints': ds.get('selected_timepoints') or None,
            'segmentation_channel': ds.get('segmentation_channel'),
            'analysis_channels': ds.get('analysis_channels') or None,
        }

    def execute_stage(self, stage_name: str, **kwargs) -> bool:
        """
        Execute a single stage.
        
        Args:
            stage_name: Name of the stage to execute
            **kwargs: Stage-specific arguments
            
        Returns:
            True if successful, False otherwise
        """
        stage_class = self.registry.get_stage_class(stage_name)
        if not stage_class:
            self.logger.error(f"Stage not found: {stage_name}")
            return False
        
        # Reload config to ensure we have the latest data
        try:
            self.config.load()
            self.logger.debug(f"Config reloaded successfully. Data selection: {self.config.get('data_selection')}")
        except Exception as e:
            self.logger.warning(f"Could not reload config: {e}")
        
        # Prepare DI-aware constructor kwargs based on the stage's __init__ signature
        ctor_kwargs = {}
        try:
            import inspect
            params = inspect.signature(stage_class.__init__).parameters
            # Optional event bus
            if 'event_bus' in params:
                ctor_kwargs['event_bus'] = self.event_bus
            # Optional services via ServiceFactory, if available
            if 'file_service' in params:
                try:
                    # Use ServiceFactory if pipeline provided it via logger binding
                    factory = getattr(self, 'service_factory', None)
                    if factory is None and hasattr(self.logger, 'service_factory'):
                        factory = getattr(self.logger, 'service_factory')
                    if factory is not None:
                        ctor_kwargs['file_service'] = factory.get_file_service()
                    else:
                        from percell.infrastructure.file_service import FileService
                        ctor_kwargs['file_service'] = FileService()
                except Exception:
                    pass
            if 'imagej_service' in params:
                try:
                    factory = getattr(self, 'service_factory', None)
                    if factory is None and hasattr(self.logger, 'service_factory'):
                        factory = getattr(self.logger, 'service_factory')
                    if factory is not None:
                        ctor_kwargs['imagej_service'] = factory.get_imagej_service()
                    else:
                        from percell.infrastructure.imagej_service import ImageJService
                        imagej_path = self.config.get('imagej_path', '')
                        ctor_kwargs['imagej_service'] = ImageJService(imagej_path)
                except Exception:
                    pass
            if 'module_runner' in params:
                try:
                    factory = getattr(self, 'service_factory', None)
                    if factory is None and hasattr(self.logger, 'service_factory'):
                        factory = getattr(self.logger, 'service_factory')
                    if factory is not None:
                        ctor_kwargs['module_runner'] = factory.get_module_runner()
                except Exception:
                    pass
            if 'workflow_service' in params:
                try:
                    factory = getattr(self, 'service_factory', None)
                    if factory is None and hasattr(self.logger, 'service_factory'):
                        factory = getattr(self.logger, 'service_factory')
                    if factory is not None:
                        ctor_kwargs['workflow_service'] = factory.get_workflow_service()
                except Exception:
                    pass
            if 'cleanup_service' in params:
                try:
                    factory = getattr(self, 'service_factory', None)
                    if factory is None and hasattr(self.logger, 'service_factory'):
                        factory = getattr(self.logger, 'service_factory')
                    if factory is not None:
                        ctor_kwargs['cleanup_service'] = factory.get_cleanup_service()
                except Exception:
                    pass
            if 'image_binning_service' in params:
                try:
                    factory = getattr(self, 'service_factory', None)
                    if factory is None and hasattr(self.logger, 'service_factory'):
                        factory = getattr(self.logger, 'service_factory')
                    if factory is not None:
                        ctor_kwargs['image_binning_service'] = factory.get_image_binning_service()
                except Exception:
                    pass
            if 'progress_reporter' in params:
                try:
                    factory = getattr(self, 'service_factory', None)
                    if factory is None and hasattr(self.logger, 'service_factory'):
                        factory = getattr(self.logger, 'service_factory')
                    if factory is not None:
                        ctor_kwargs['progress_reporter'] = factory.get_progress_reporter()
                except Exception:
                    pass
        except Exception:
            # If reflection fails, fall back to legacy args only
            pass

        # Provide data selection filters to all stages by default (non-intrusive)
        kwargs.setdefault('data_selection_filters', self.get_data_selection_filters())

        stage = stage_class(self.config, self.logger, stage_name, **ctor_kwargs)
        success = stage.execute(**kwargs)
        
        # Record execution
        self.execution_history.append({
            'stage_name': stage_name,
            'success': success,
            'duration': stage.get_duration(),
            'timestamp': time.time()
        })
        
        return success
    
    def execute_stages(self, stage_names: List[str], **kwargs) -> bool:
        """
        Execute multiple stages in order.
        
        Args:
            stage_names: List of stage names to execute
            **kwargs: Stage-specific arguments
            
        Returns:
            True if all stages successful, False otherwise
        """
        all_successful = True
        
        for stage_name in stage_names:
            self.logger.info(f"Executing stage: {stage_name}")
            success = self.execute_stage(stage_name, **kwargs)
            
            if not success:
                all_successful = False
                self.logger.error(f"Stage {stage_name} failed, stopping execution")
                break
        
        return all_successful
    
    def get_execution_summary(self) -> Dict[str, Any]:
        """
        Get execution summary.
        
        Returns:
            Dictionary with execution statistics
        """
        total_stages = len(self.execution_history)
        successful_stages = len([h for h in self.execution_history if h['success']])
        total_duration = sum(h.get('duration', 0) for h in self.execution_history)
        
        return {
            'total_stages': total_stages,
            'successful_stages': successful_stages,
            'failed_stages': total_stages - successful_stages,
            'success_rate': successful_stages / total_stages if total_stages > 0 else 0,
            'total_duration': total_duration,
            'execution_history': self.execution_history
        }


def register_stage(stage_name: str, order: Optional[int] = None):
    """
    Decorator to register a stage.
    
    Args:
        stage_name: Name of the stage
        order: Execution order (optional)
    """
    def decorator(stage_class):
        registry = get_stage_registry()
        registry.register(stage_name, stage_class, order)
        return stage_class
    return decorator


def get_stage_registry() -> StageRegistry:
    """
    Get the global stage registry.
    
    Returns:
        Stage registry instance
    """
    if not hasattr(get_stage_registry, '_registry'):
        get_stage_registry._registry = StageRegistry()
    return get_stage_registry._registry 