from pathlib import Path
import sys
import types

# Stub cv2 if import occurs indirectly somewhere
sys.modules['cv2'] = types.ModuleType('cv2')

from percell.modules import extract_cells as ec


def test_run_imagej_macro_missing_exe_returns_false(tmp_path: Path):
    macro = tmp_path / "dummy.ijm"
    macro.write_text("// no-op")
    ok = ec.run_imagej_macro(str(tmp_path / "no_imagej"), str(macro), auto_close=True)
    assert ok is False


