from __future__ import annotations

from pathlib import Path
from typing import Protocol, List


class ImageJIntegrationPort(Protocol):
    """Driven port for executing ImageJ macros or commands."""

    def run_macro(self, macro_path: Path, args: List[str]) -> int:
        """Run a macro and return process return code."""
        ...


