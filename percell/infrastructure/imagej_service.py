from __future__ import annotations

import subprocess
from typing import Optional, Dict

from percell.domain.ports import ImageProcessingService


class ImageJService(ImageProcessingService):
    """Thin wrapper for invoking ImageJ/Fiji macros.

    Notes:
    - ImageJ's -macro takes an optional single string argument. If you need multiple
      values, join them with a delimiter and parse inside the macro.
    - Headless mode prevents UI windows from opening; set headless=False for interactive use.
    """

    def __init__(self, imagej_path: Optional[str] = None) -> None:
        self.imagej_path = imagej_path or ""

    def run_macro(self, macro_path: str, params: Optional[Dict[str, str]] = None, *, headless: bool = False) -> int:
        if not self.imagej_path:
            return 1
        cmd = [self.imagej_path]
        if headless:
            cmd.append("--headless")
        cmd.extend(["-macro", macro_path])
        if params:
            # Join key=value pairs with semicolons for a single arg string
            arg_string = ";".join(f"{k}={v}" for k, v in params.items())
            cmd.append(arg_string)
        result = subprocess.run(cmd, capture_output=True, text=True)
        return result.returncode


__all__ = ["ImageJService"]


