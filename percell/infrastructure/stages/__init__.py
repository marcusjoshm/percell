"""
Infrastructure stages module.

This module provides the stage execution framework for the Percell pipeline.
"""

from .stages import (
    StageBase,
    StageExecutor,
    StageRegistry,
    StageError,
    get_stage_registry
)

__all__ = [
    "StageBase",
    "StageExecutor", 
    "StageRegistry",
    "StageError",
    "get_stage_registry"
]
