from __future__ import annotations

from pathlib import Path
from typing import Any, Dict
from types import SimpleNamespace
import tempfile

from percell.ports.outbound.macro_runner_port import MacroRunnerPort, MacroResult
from percell.core.progress import run_subprocess_with_spinner


class ImageJMacroAdapter(MacroRunnerPort):
    """Adapter that runs ImageJ/Fiji macros using a subprocess wrapper.

    Parameters are embedded as comments at the top of a temporary macro file
    to keep the adapter simple and pure. Real parameter injection/parsing can
    be extended later if needed.
    """

    def __init__(self, imagej_path: Path, macro_dir: Path):
        self.imagej_path = Path(imagej_path)
        self.macro_dir = Path(macro_dir)

    def run_macro(self, macro_name: str, parameters: Dict[str, Any]) -> MacroResult:
        if not self.validate_macro(macro_name):
            return MacroResult(success=False, stderr=f"Macro not found: {macro_name}")

        base_macro_path = self.macro_dir / macro_name
        base_content = base_macro_path.read_text(encoding="utf-8")

        header_lines = ["// Percell Auto-generated wrapper macro", "// Parameters:"]
        for key, value in parameters.items():
            header_lines.append(f"// {key} = {value}")
        header = "\n".join(header_lines) + "\n\n"

        with tempfile.NamedTemporaryFile(suffix=".ijm", mode="w", delete=False, encoding="utf-8") as f:
            f.write(header)
            f.write(base_content)
            temp_macro_path = Path(f.name)

        try:
            cmd = [str(self.imagej_path), "--headless", "--run", str(temp_macro_path)]
            result = run_subprocess_with_spinner(cmd, f"Running {macro_name}", capture_output=True)
            # result is expected to expose returncode/stdout/stderr
            return MacroResult(
                success=getattr(result, "returncode", 1) == 0,
                stdout=getattr(result, "stdout", None),
                stderr=getattr(result, "stderr", None),
            )
        finally:
            try:
                temp_macro_path.unlink(missing_ok=True)
            except Exception:
                # Best-effort cleanup
                pass

    def validate_macro(self, macro_name: str) -> bool:
        return (self.macro_dir / macro_name).is_file()


