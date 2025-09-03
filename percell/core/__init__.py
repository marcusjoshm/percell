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

from percell.cli.app import PipelineCLI, parse_arguments, create_cli, CLIError
from percell.infrastructure.configuration.config import Config, ConfigError, create_default_config, validate_software_paths, detect_software_paths
from percell.infrastructure.logging.logger import PipelineLogger, ModuleLogger, create_logger
from percell.core.pipeline import Pipeline, create_pipeline
from percell.infrastructure.stages.stages import (
    StageBase, 
    FileProcessingStage, 
    StageRegistry, 
    StageExecutor, 
    StageError,
    register_stage, 
    get_stage_registry
)
from percell.infrastructure.filesystem.paths import (
    get_path_config,
    get_path,
    get_path_str,
    path_exists,
    ensure_executable,
    list_all_paths
)
from percell.infrastructure.progress.progress import (
    is_progress_available,
    configure_global,
    progress_bar,
    iter_with_progress,
    spinner,
    run_subprocess_with_spinner,
)

__all__ = [
    'PipelineCLI',
    'parse_arguments',
    'create_cli',
    'CLIError',
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