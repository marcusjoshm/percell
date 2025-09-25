"""Consolidated configuration service.

Combines functionality from ConfigurationManager and Config classes
into a single, consistent service with proper error handling.
"""

from __future__ import annotations

import json
import tempfile
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional

from ..exceptions import ConfigurationError

logger = logging.getLogger(__name__)


@dataclass
class ConfigurationService:
    """Unified configuration service with dot-notation access and proper error handling.

    This service combines the functionality of both ConfigurationManager and Config
    classes, providing:
    - Consistent dot-notation access for nested values
    - Atomic file operations with proper error handling
    - Comprehensive logging of configuration operations
    - Type-safe operations with proper validation
    """

    path: Path
    _data: Dict[str, Any] = None

    def __post_init__(self) -> None:
        """Initialize the configuration service."""
        if self._data is None:
            self._data = {}
        if isinstance(self.path, str):
            self.path = Path(self.path)

    def load(self, create_if_missing: bool = True) -> None:
        """Load configuration from file.

        Args:
            create_if_missing: If True, create empty config if file doesn't exist.
                              If False, raise ConfigurationError if file is missing.

        Raises:
            ConfigurationError: If file is missing and create_if_missing=False,
                               or if file contains invalid JSON.
        """
        try:
            if not self.path.exists():
                if create_if_missing:
                    logger.info(f"Configuration file not found at {self.path}, starting with empty configuration")
                    self._data = {}
                    return
                else:
                    raise ConfigurationError(f"Configuration file not found: {self.path}")

            logger.debug(f"Loading configuration from {self.path}")
            content = self.path.read_text(encoding="utf-8")
            self._data = json.loads(content)
            logger.info(f"Successfully loaded configuration from {self.path}")

        except json.JSONDecodeError as e:
            error_msg = f"Invalid JSON in configuration file {self.path}: {e}"
            logger.error(error_msg)
            raise ConfigurationError(error_msg) from e
        except (OSError, IOError) as e:
            error_msg = f"Error reading configuration file {self.path}: {e}"
            logger.error(error_msg)
            raise ConfigurationError(error_msg) from e

    def save(self) -> None:
        """Save configuration to file with atomic operation.

        Uses atomic write to prevent corruption if save operation fails.

        Raises:
            ConfigurationError: If unable to save configuration.
        """
        try:
            # Ensure parent directory exists
            self.path.parent.mkdir(parents=True, exist_ok=True)

            # Use atomic write to prevent corruption
            with tempfile.NamedTemporaryFile(
                mode='w',
                suffix='.json',
                dir=str(self.path.parent),
                delete=False,
                encoding='utf-8'
            ) as temp_file:
                temp_path = Path(temp_file.name)
                json.dump(self._data, temp_file, indent=2, sort_keys=True, ensure_ascii=False)

            # Atomic replace
            temp_path.replace(self.path)
            logger.info(f"Successfully saved configuration to {self.path}")

        except (OSError, IOError) as e:
            error_msg = f"Error saving configuration to {self.path}: {e}"
            logger.error(error_msg)
            # Clean up temp file if it exists
            try:
                if 'temp_path' in locals() and temp_path.exists():
                    temp_path.unlink()
            except Exception:
                pass
            raise ConfigurationError(error_msg) from e

    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value with support for dot notation.

        Args:
            key: Configuration key, supports dot notation (e.g., 'paths.imagej')
            default: Default value if key is not found

        Returns:
            Configuration value or default if not found
        """
        if '.' in key:
            return self._get_nested(key, default)

        value = self._data.get(key, default)
        if value != default:
            logger.debug(f"Retrieved config value for '{key}': {type(value).__name__}")
        return value

    def set(self, key: str, value: Any) -> None:
        """Set configuration value with support for dot notation.

        Args:
            key: Configuration key, supports dot notation (e.g., 'paths.imagej')
            value: Value to set
        """
        if '.' in key:
            self._set_nested(key, value)
        else:
            old_value = self._data.get(key)
            self._data[key] = value

            if old_value != value:
                logger.debug(f"Updated config '{key}': {old_value} -> {value}")

    def _get_nested(self, dotted_key: str, default: Any = None) -> Any:
        """Get nested configuration value using dot notation."""
        node = self._data
        parts = dotted_key.split('.')

        for part in parts:
            if isinstance(node, dict) and part in node:
                node = node[part]
            else:
                return default

        return node

    def _set_nested(self, dotted_key: str, value: Any) -> None:
        """Set nested configuration value using dot notation."""
        parts = dotted_key.split('.')
        node = self._data

        # Navigate/create intermediate nodes
        for part in parts[:-1]:
            if part not in node:
                node[part] = {}
            elif not isinstance(node[part], dict):
                # Convert non-dict to dict to allow nesting
                node[part] = {}
            node = node[part]

        # Set the final value
        old_value = node.get(parts[-1])
        node[parts[-1]] = value

        if old_value != value:
            logger.debug(f"Updated nested config '{dotted_key}': {old_value} -> {value}")

    def update(self, values: Dict[str, Any]) -> None:
        """Update multiple configuration values.

        Args:
            values: Dictionary of key-value pairs to update
        """
        logger.debug(f"Updating {len(values)} configuration values")
        for key, value in values.items():
            self.set(key, value)

    def has(self, key: str) -> bool:
        """Check if configuration key exists.

        Args:
            key: Configuration key, supports dot notation

        Returns:
            True if key exists, False otherwise
        """
        return self.get(key, _MISSING) is not _MISSING

    def delete(self, key: str) -> bool:
        """Delete configuration key.

        Args:
            key: Configuration key, supports dot notation

        Returns:
            True if key was deleted, False if key didn't exist
        """
        if '.' in key:
            return self._delete_nested(key)

        if key in self._data:
            del self._data[key]
            logger.debug(f"Deleted config key '{key}'")
            return True
        return False

    def _delete_nested(self, dotted_key: str) -> bool:
        """Delete nested configuration key using dot notation."""
        parts = dotted_key.split('.')
        node = self._data

        # Navigate to parent node
        for part in parts[:-1]:
            if not isinstance(node, dict) or part not in node:
                return False
            node = node[part]

        # Delete the final key
        final_key = parts[-1]
        if isinstance(node, dict) and final_key in node:
            del node[final_key]
            logger.debug(f"Deleted nested config key '{dotted_key}'")
            return True
        return False

    def to_dict(self) -> Dict[str, Any]:
        """Get a copy of the entire configuration as a dictionary.

        Returns:
            Copy of configuration data
        """
        import copy
        return copy.deepcopy(self._data)

    def clear(self) -> None:
        """Clear all configuration data."""
        logger.info("Clearing all configuration data")
        self._data.clear()

    def get_resolved_path(self, key: str, project_root: Optional[Path] = None) -> Optional[Path]:
        """Get a path from configuration with automatic resolution.

        Args:
            key: Configuration key for the path
            project_root: Optional project root for resolving relative paths

        Returns:
            Resolved Path object or None if key doesn't exist
        """
        path_str = self.get(key)
        if not path_str:
            return None

        path = Path(path_str)
        if path.is_absolute() or project_root is None:
            return path

        return project_root / path


# Sentinel object for checking key existence
_MISSING = object()


def create_configuration_service(path: str | Path, create_if_missing: bool = True) -> ConfigurationService:
    """Factory function to create and load a configuration service.

    Args:
        path: Path to configuration file
        create_if_missing: Whether to create empty config if file is missing

    Returns:
        Loaded ConfigurationService instance
    """
    service = ConfigurationService(Path(path))
    service.load(create_if_missing=create_if_missing)
    return service