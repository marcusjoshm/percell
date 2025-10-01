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
from percell.domain.services.configuration_service import ConfigurationService, create_configuration_service

# CLI components are now provided via application layer and UI adapters.

__all__ = [
    "Pipeline",
    "create_pipeline",
    "ConfigurationService",
    "create_configuration_service",
    "ConfigurationError",
    "PipelineLogger",
    "ModuleLogger",
] 