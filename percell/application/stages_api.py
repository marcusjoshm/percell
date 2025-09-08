from __future__ import annotations

"""Application-level stages API mirroring legacy core.stages exports."""

import time
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List

from percell.application.config_api import Config
from percell.application.logger_api import PipelineLogger, ModuleLogger


class StageError(Exception):
    pass


class StageBase(ABC):
    def __init__(self, config: Config, logger: PipelineLogger, stage_name: str):
        self.config = config
        self.pipeline_logger = logger
        self.stage_name = stage_name
        self.logger = ModuleLogger(stage_name, logger)
        self.start_time: Optional[float] = None
        self.end_time: Optional[float] = None

    @abstractmethod
    def run(self, **kwargs) -> bool: ...

    @abstractmethod
    def validate_inputs(self, **kwargs) -> bool: ...

    def get_description(self) -> str:
        return f"Executing {self.stage_name}"

    def setup(self, **kwargs) -> bool:
        return True

    def cleanup(self, **kwargs) -> bool:
        return True

    def execute(self, **kwargs) -> bool:
        try:
            self.start_time = time.time()
            self.logger.info(f"Starting {self.stage_name}")
            if not self.setup(**kwargs):
                self.logger.error(f"Setup failed for {self.stage_name}")
                return False
            if not self.validate_inputs(**kwargs):
                self.logger.error(f"Input validation failed for {self.stage_name}")
                return False
            success = self.run(**kwargs)
            if not self.cleanup(**kwargs):
                self.logger.warning(f"Cleanup failed for {self.stage_name}")
            self.end_time = time.time()
            duration = self.get_duration()
            if success:
                self.pipeline_logger.log_stage_complete(self.stage_name, duration)
                self.logger.info(f"Completed {self.stage_name} successfully")
            else:
                self.pipeline_logger.log_stage_failed(self.stage_name, "Stage execution failed")
                self.logger.error(f"Failed to complete {self.stage_name}")
            return success
        except Exception as e:
            self.end_time = time.time()
            self.pipeline_logger.log_stage_failed(self.stage_name, str(e))
            self.logger.error(f"Exception in {self.stage_name}: {e}")
            return False

    def get_duration(self) -> Optional[float]:
        if self.start_time is not None and self.end_time is not None:
            return self.end_time - self.start_time
        return None


class FileProcessingStage(StageBase):
    def __init__(self, config: Config, logger: PipelineLogger, stage_name: str):
        super().__init__(config, logger, stage_name)
        self.processed_files: List[str] = []
        self.failed_files: List[str] = []

    @abstractmethod
    def _process_file_impl(self, file_path: str, **kwargs) -> bool: ...

    def process_file(self, file_path: str, **kwargs) -> bool:
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

    def get_processing_summary(self) -> Dict[str, Any]:
        total = len(self.processed_files) + len(self.failed_files)
        success_rate = len(self.processed_files) / total if total > 0 else 0
        return {
            "stage_name": self.stage_name,
            "total_files": total,
            "processed_files": len(self.processed_files),
            "failed_files": len(self.failed_files),
            "success_rate": success_rate,
            "duration": self.get_duration(),
            "processed_file_list": self.processed_files,
            "failed_file_list": self.failed_files,
        }


class StageRegistry:
    def __init__(self) -> None:
        self.stages: Dict[str, type] = {}
        self.stage_order: Dict[str, int] = {}

    def register(self, stage_name: str, stage_class: type, order: Optional[int] = None) -> None:
        self.stages[stage_name] = stage_class
        if order is not None:
            self.stage_order[stage_name] = order

    def get_stage_class(self, stage_name: str) -> Optional[type]:
        return self.stages.get(stage_name)

    def get_available_stages(self) -> List[str]:
        return list(self.stages.keys())

    def get_stage_order(self) -> List[str]:
        return [name for name, _ in sorted(self.stage_order.items(), key=lambda x: x[1])]


class StageExecutor:
    def __init__(
        self,
        config: Config,
        logger: PipelineLogger,
        registry: StageRegistry,
        *,
        ports: Optional[Dict[str, Any]] = None,
    ):
        self.config = config
        self.logger = logger
        self.registry = registry
        self.ports: Dict[str, Any] = ports or {}
        self.execution_history: List[Dict[str, Any]] = []

    def execute_stage(self, stage_name: str, **kwargs) -> bool:
        stage_class = self.registry.get_stage_class(stage_name)
        if not stage_class:
            self.logger.error(f"Stage not found: {stage_name}")
            return False
        try:
            self.config.load()
            self.logger.debug(
                f"Config reloaded successfully. Data selection: {self.config.get('data_selection')}"
            )
        except Exception as e:
            self.logger.warning(f"Could not reload config: {e}")
        stage = stage_class(self.config, self.logger, stage_name)
        # Thread injected ports into stage kwargs where helpers expect them
        # Conventional keys: imagej, fs, imgproc, cellpose
        port_kwargs = {}
        for key in ("imagej", "fs", "imgproc", "cellpose"):
            if key in self.ports and key not in kwargs:
                port_kwargs[key] = self.ports[key]
        merged = {**kwargs, **port_kwargs}
        success = stage.execute(**merged)
        self.execution_history.append(
            {
                "stage_name": stage_name,
                "success": success,
                "duration": stage.get_duration(),
                "timestamp": time.time(),
            }
        )
        return success

    def execute_stages(self, stage_names: List[str], **kwargs) -> bool:
        all_successful = True
        for stage_name in stage_names:
            self.logger.info(f"Executing stage: {stage_name}")
            if not self.execute_stage(stage_name, **kwargs):
                all_successful = False
                self.logger.error(f"Stage {stage_name} failed, stopping execution")
                break
        return all_successful

    def get_execution_summary(self) -> Dict[str, Any]:
        total = len(self.execution_history)
        successful = len([h for h in self.execution_history if h["success"]])
        total_duration = sum(h.get("duration", 0) or 0 for h in self.execution_history)
        return {
            "total_stages": total,
            "successful_stages": successful,
            "failed_stages": total - successful,
            "success_rate": successful / total if total > 0 else 0,
            "total_duration": total_duration,
            "execution_history": self.execution_history,
        }


def register_stage(stage_name: str, order: Optional[int] = None):
    def decorator(stage_class):
        registry = get_stage_registry()
        registry.register(stage_name, stage_class, order)
        return stage_class
    return decorator


def get_stage_registry() -> StageRegistry:
    if not hasattr(get_stage_registry, "_registry"):
        get_stage_registry._registry = StageRegistry()  # type: ignore[attr-defined]
    return get_stage_registry._registry  # type: ignore[attr-defined]


