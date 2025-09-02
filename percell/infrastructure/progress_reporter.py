"""
Progress reporter implementation for the Percell infrastructure layer.

This module provides a concrete implementation of the ProgressReporter port
using the alive-progress library for terminal progress bars and spinners.
"""

from __future__ import annotations

from typing import Optional
import os

from percell.domain.ports import ProgressReporter
from percell.infrastructure.progress.progress import spinner, is_progress_available


class AliveProgressReporter(ProgressReporter):
    """
    Progress reporter implementation using alive-progress.
    
    Implements the ProgressReporter port interface and provides
    terminal-friendly progress indicators.
    """
    
    def __init__(self, enabled: Optional[bool] = None) -> None:
        """
        Initialize the progress reporter.
        
        Args:
            enabled: Whether to enable progress reporting. If None, checks
                    PERCELL_STAGE_SPINNER environment variable.
        """
        # Stage-level spinner disabled by default; can be enabled via env
        if enabled is None:
            env = os.getenv("PERCELL_STAGE_SPINNER", "0").strip().lower()
            enabled = env in {"1", "true", "yes", "on"}
        
        self._enabled = bool(enabled) and is_progress_available()
        self._update = None
        self._cm = None

    def start(self, title: Optional[str] = None) -> None:
        """
        Start a progress indicator.
        
        Args:
            title: Optional title for the progress indicator
        """
        # Close any existing spinner before starting a new one
        if getattr(self, "_cm", None) is not None:
            try:
                self._cm.__exit__(None, None, None)
            except Exception:
                pass
            self._cm = None
            self._update = None

        if not self._enabled:
            if title:
                print(title)
            self._cm = None
            self._update = None
            return

        # Use the infrastructure progress utilities
        try:
            self._cm = spinner(title=title)
            self._update = self._cm.__enter__()
        except Exception:
            # Fallback to simple progress if alive-progress fails
            self._cm = self._create_simple_progress(title)
            self._update = self._cm.__enter__()

    def advance(self, delta: int = 1) -> None:
        """
        Advance the progress indicator.
        
        Args:
            delta: Amount to advance (default: 1)
        """
        if self._update:
            try:
                self._update(delta)
            except Exception:
                pass

    def stop(self) -> None:
        """Stop the progress indicator."""
        if getattr(self, "_cm", None) is not None:
            try:
                self._cm.__exit__(None, None, None)
            except Exception:
                pass
            self._cm = None
            self._update = None

    def _create_simple_progress(self, title: Optional[str] = None):
        """Create a simple progress context manager for fallback."""
        class SimpleProgressContext:
            def __init__(self, title):
                self.title = title
                self._update = None
            
            def __enter__(self):
                if self.title:
                    print(f"Starting: {self.title}")
                self._update = lambda x: None  # No-op update function
                return self._update
            
            def __exit__(self, exc_type, exc_val, exc_tb):
                if self.title:
                    print(f"Completed: {self.title}")

        return SimpleProgressContext(title)


# Alias for backward compatibility
ProgressReporter = AliveProgressReporter

__all__ = ["AliveProgressReporter", "ProgressReporter"]


