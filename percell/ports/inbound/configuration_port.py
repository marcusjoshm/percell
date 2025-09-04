from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional


class ConfigurationPort(ABC):
    """Driving port for application configuration management."""

    @abstractmethod
    def load(self) -> None:
        """Load configuration from persistent storage."""

    @abstractmethod
    def save(self) -> None:
        """Persist configuration to storage."""

    @abstractmethod
    def get(self, key_path: str, default: Optional[Any] = None) -> Any:
        """Get a configuration value by dotted path, with optional default."""

    @abstractmethod
    def set(self, key_path: str, value: Any) -> None:
        """Set a configuration value by dotted path."""

    @abstractmethod
    def to_dict(self) -> Dict[str, Any]:
        """Get the entire configuration as a dictionary."""


