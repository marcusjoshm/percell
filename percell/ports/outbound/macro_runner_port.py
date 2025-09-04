from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict, Optional


@dataclass(frozen=True)
class MacroResult:
    """Outcome of running an external macro."""

    success: bool
    stdout: Optional[str] = None
    stderr: Optional[str] = None


class MacroRunnerPort(ABC):
    """Driven port for executing ImageJ/Fiji or similar macros."""

    @abstractmethod
    def run_macro(self, macro_name: str, parameters: Dict[str, Any]) -> MacroResult:
        """Execute a macro with parameter mapping and return structured result."""

    @abstractmethod
    def validate_macro(self, macro_name: str) -> bool:
        """Return True if a macro with the given name can be executed."""


