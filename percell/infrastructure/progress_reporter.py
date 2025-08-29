from __future__ import annotations

from typing import Optional
import os

from percell.domain.ports import ProgressReporter
from percell.core import progress


class AliveProgressReporter(ProgressReporter):
    def __init__(self, enabled: Optional[bool] = None) -> None:
        # Stage-level spinner disabled by default; can be enabled via env
        if enabled is None:
            env = os.getenv("PERCELL_STAGE_SPINNER", "0").strip().lower()
            enabled = env in {"1", "true", "yes", "on"}
        self._enabled = bool(enabled)
        self._update = None

    def start(self, title: Optional[str] = None) -> None:
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

        self._cm = progress.progress_bar(total=None, title=title)
        self._update = self._cm.__enter__()

    def advance(self, delta: int = 1) -> None:
        if self._update:
            try:
                self._update(delta)
            except Exception:
                pass

    def stop(self) -> None:
        if getattr(self, "_cm", None) is not None:
            try:
                self._cm.__exit__(None, None, None)
            except Exception:
                pass
            self._cm = None
            self._update = None


__all__ = ["AliveProgressReporter"]


