from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict


@dataclass
class AnalysisContext:
    """Minimal context passed to plugins for processing."""
    input_dir: str
    output_dir: str
    parameters: Dict[str, Any]


@dataclass
class AnalysisResult:
    """Result returned by plugins after processing."""
    success: bool
    details: Dict[str, Any]


class AnalysisPlugin(ABC):
    """Base interface for analysis plugins."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Unique plugin name used for registration and selection."""
        raise NotImplementedError

    @abstractmethod
    def validate_inputs(self, context: AnalysisContext) -> bool:
        """Validate inputs before processing begins."""
        raise NotImplementedError

    @abstractmethod
    def process(self, context: AnalysisContext) -> AnalysisResult:
        """Run the plugin's analysis and return a result."""
        raise NotImplementedError


__all__ = [
    "AnalysisPlugin",
    "AnalysisContext",
    "AnalysisResult",
]


