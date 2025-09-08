from pathlib import Path

import sys
import types

# Provide a dummy cv2 to avoid heavy dependency during import of module under test
sys.modules['cv2'] = types.ModuleType('cv2')

from percell.application.imagej_tasks import run_imagej_macro


def test_run_imagej_macro_with_missing_exe_returns_false(tmp_path: Path):
    # Prepare a dummy macro file
    macro = tmp_path / "dummy.ijm"
    macro.write_text("// no-op")
    ok = run_imagej_macro(str(tmp_path / "no_imagej"), str(macro), auto_close=True)
    assert ok is False


