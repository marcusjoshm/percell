from __future__ import annotations

import sys
import subprocess
from typing import List, Optional

from percell.core.progress import run_subprocess_with_spinner


class ModuleRunner:
    """Service to invoke Python helper modules with consistent UX and logging."""

    def run(self, script_path: str, args: List[str], title: Optional[str] = None) -> int:
        cmd = [sys.executable, script_path] + args
        result = run_subprocess_with_spinner(cmd, title=title)
        return result.returncode


__all__ = ["ModuleRunner"]


