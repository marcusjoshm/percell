"""
Core modules for Microscopy Single-Cell Analysis Pipeline

This package contains the core functionality for the microscopy analysis pipeline:
- CLI: Command line interface
- Config: Configuration management
- Logger: Logging framework
- Pipeline: Main pipeline orchestrator
- Stages: Stage execution framework
- Utils: Utility functions for package resource management
"""

# CLI has been migrated to application layer; no imports here
from percell.application.config_api import (
    Config,
    ConfigError,
    create_default_config,
    validate_software_paths,
    detect_software_paths,
)
from percell.application.logger_api import PipelineLogger, ModuleLogger, create_logger
from .pipeline import Pipeline, create_pipeline
from .stages import (
    StageBase, 
    FileProcessingStage, 
    StageRegistry, 
    StageExecutor, 
    StageError,
    register_stage, 
    get_stage_registry
)
# Note: legacy utils functions are no longer re-exported here.
# They remain available under percell.core.utils during migration.
from percell.application.paths_api import (
    get_path_config,
    get_path,
    get_path_str,
    path_exists,
    ensure_executable,
    list_all_paths,
)
from .progress import (
    is_progress_available,
    configure_global,
    progress_bar,
    iter_with_progress,
    spinner,
    run_subprocess_with_spinner,
)

__all__ = [
    'Config',
    'ConfigError',
    'create_default_config',
    'validate_software_paths',
    'detect_software_paths',
    'PipelineLogger',
    'ModuleLogger',
    'create_logger',
    'Pipeline',
    'create_pipeline',
    'StageBase',
    'FileProcessingStage',
    'StageRegistry',
    'StageExecutor',
    'StageError',
    'register_stage',
    'get_stage_registry',
    'get_path_config',
    'get_path',
    'get_path_str',
    'path_exists',
    'ensure_executable',
    'list_all_paths',
    'is_progress_available',
    'configure_global',
    'progress_bar',
    'iter_with_progress',
    'spinner',
    'run_subprocess_with_spinner',
] 