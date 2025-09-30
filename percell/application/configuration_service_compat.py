"""Backward compatibility layer for configuration classes.

This module provides aliases and compatibility wrappers for the old
ConfigurationManager and Config classes to ensure existing code continues
to work during the transition period.
"""

from __future__ import annotations

import warnings
from pathlib import Path
from typing import Any, Dict

from percell.domain.services.configuration_service import ConfigurationService as NewConfigurationService
from percell.domain.exceptions import ConfigurationError


# Define ConfigError for compatibility
class ConfigError(Exception):
    """Compatibility exception for old config_api.ConfigError."""
    pass


class ConfigurationManager:
    """Compatibility wrapper for the old ConfigurationManager class.

    This class maintains the same interface as the original ConfigurationManager
    but delegates to the new consolidated ConfigurationService.
    """

    def __init__(self, path: Path) -> None:
        warnings.warn(
            "ConfigurationManager is deprecated. Use percell.domain.services.configuration_service.ConfigurationService instead.",
            DeprecationWarning,
            stacklevel=2
        )
        self.path = path
        self._service = NewConfigurationService(path)

    def load(self) -> None:
        """Load configuration from file."""
        self._service.load(create_if_missing=True)

    def save(self) -> None:
        """Save configuration to file."""
        self._service.save()

    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value."""
        return self._service.get(key, default)

    def set(self, key: str, value: Any) -> None:
        """Set configuration value."""
        self._service.set(key, value)

    def get_nested(self, dotted: str, default: Any = None) -> Any:
        """Get nested configuration value using dot notation."""
        return self._service.get(dotted, default)

    def set_nested(self, dotted: str, value: Any) -> None:
        """Set nested configuration value using dot notation."""
        self._service.set(dotted, value)

    def update(self, values: Dict[str, Any]) -> None:
        """Update multiple configuration values."""
        self._service.update(values)

    @property
    def _data(self) -> Dict[str, Any]:
        """Access to internal data (for compatibility)."""
        return self._service._data


class Config:
    """Compatibility wrapper for the old Config class.

    This class maintains the same interface as the original Config class
    but delegates to the new consolidated ConfigurationService.
    """

    def __init__(self, config_path: str) -> None:
        warnings.warn(
            "Config is deprecated. Use percell.domain.services.configuration_service.ConfigurationService instead.",
            DeprecationWarning,
            stacklevel=2
        )
        self.config_path = Path(config_path)
        self._service = NewConfigurationService(self.config_path)
        try:
            self._service.load(create_if_missing=False)
        except ConfigurationError:
            # Re-raise as the old exception type for compatibility
            raise ConfigError(f"Configuration file not found: {config_path}")

    def load(self) -> None:
        """Load configuration from file."""
        try:
            self._service.load(create_if_missing=False)
        except ConfigurationError as e:
            raise ConfigError(str(e)) from e

    def save(self) -> None:
        """Save configuration to file."""
        try:
            self._service.save()
        except ConfigurationError as e:
            raise ConfigError(str(e)) from e

    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value with support for dot notation."""
        return self._service.get(key, default)

    @property
    def config_data(self) -> Dict[str, Any]:
        """Access to configuration data (for compatibility)."""
        return self._service._data

    @config_data.setter
    def config_data(self, value: Dict[str, Any]) -> None:
        """Set configuration data (for compatibility)."""
        self._service._data = value
