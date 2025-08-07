"""
Core modules for Microscopy Single-Cell Analysis Pipeline

This package contains the core functionality for the microscopy analysis pipeline:
- CLI: Command line interface
- Config: Configuration management
- Logger: Logging framework
- Pipeline: Main pipeline orchestrator
- Stages: Stage execution framework
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
    'get_stage_registry'
] 