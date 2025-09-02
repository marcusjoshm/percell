"""
Configuration management for the Percell infrastructure layer.

This package provides configuration functionality including:
- Configuration loading and validation
- JSON-based configuration
- Default configuration creation
"""

from .config import Config, ConfigError, create_default_config

__all__ = ['Config', 'ConfigError', 'create_default_config']
