"""
Percell Package

A comprehensive pipeline for microscopy single-cell analysis.
"""

__version__ = "1.0.0"
__author__ = "Joshua Marcus"

# Import main components for easy access
from percell.application.pipeline_api import Pipeline, create_pipeline
from percell.domain.exceptions import ConfigurationError
from percell.application.logger_api import PipelineLogger, ModuleLogger

# Backward compatibility: Import deprecated Config classes from compat layer
# These will emit deprecation warnings when used
from percell.application.configuration_service_compat import Config, ConfigError

# CLI components are now provided via application layer and UI adapters.

__all__ = [
    "Pipeline",
    "create_pipeline",
    "Config",  # Deprecated - use ConfigurationService
    "ConfigError",  # Deprecated - use ConfigurationError
    "ConfigurationError",  # Preferred
    "PipelineLogger",
    "ModuleLogger",
] 