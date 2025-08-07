"""
Single-Cell-Analyzer Package

A comprehensive pipeline for microscopy single-cell analysis.
"""

__version__ = "1.0.0"
__author__ = "Joshua Marcus"

# Import main components for easy access
from .core.pipeline import Pipeline, create_pipeline
from .core.config import Config, ConfigError, create_default_config
from .core.logger import PipelineLogger, ModuleLogger
from .core.cli import PipelineCLI, parse_arguments, create_cli, CLIError

__all__ = [
    "Pipeline",
    "create_pipeline", 
    "Config",
    "ConfigError",
    "create_default_config",
    "PipelineLogger",
    "ModuleLogger",
    "PipelineCLI",
    "parse_arguments",
    "create_cli",
    "CLIError",
] 