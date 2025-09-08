from __future__ import annotations

import subprocess
from pathlib import Path
from typing import List, Optional

from ..ports.driven.imagej_integration_port import ImageJIntegrationPort
from percell.application.progress_api import run_subprocess_with_spinner


class ImageJMacroAdapter(ImageJIntegrationPort):
    """Adapter for executing ImageJ macros via the command line.

    This adapter is responsible only for process execution. Higher layers
    decide what macro to run and how to interpret results.
    """

    def __init__(self, imagej_executable: Path) -> None:
        self._exe = Path(imagej_executable)

    def run_macro(self, macro_path: Path, args: List[str]) -> int:
        # Prefer -batch for headless macro execution
        cmd: List[str] = [str(self._exe), "-batch", str(macro_path)]
        if args:
            # ImageJ -batch takes only a single string parameter; join args appropriately if needed
            # Many macros handle a single arg; callers can pre-serialize if required
            cmd.append(" ".join(args))

        try:
            title = f"ImageJ: {Path(macro_path).stem}"
            completed = run_subprocess_with_spinner(cmd, title=title, capture_output=True, text=True)
            return completed.returncode
        except Exception:
            return 1


