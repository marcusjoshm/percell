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

from .cli import PipelineCLI, parse_arguments, create_cli, CLIError
from .config import Config, ConfigError, create_default_config, validate_software_paths, detect_software_paths
from .logger import PipelineLogger, ModuleLogger, create_logger
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
from .utils import (
    get_package_root,
    get_package_resource,
    get_bash_script,
    get_config_file,
    get_macro_file,
    ensure_executable,
    find_package_root_from_script
)
from .paths import (
    get_path_config,
    get_path,
    get_path_str,
    path_exists,
    ensure_executable,
    list_all_paths
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
    'get_package_root',
    'get_package_resource',
    'get_bash_script',
    'get_config_file',
    'get_macro_file',
    'ensure_executable',
    'find_package_root_from_script',
    'get_path_config',
    'get_path',
    'get_path_str',
    'path_exists',
    'ensure_executable',
    'list_all_paths'
] 