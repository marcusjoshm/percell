from pathlib import Path
from percell.modules import measure_roi_area as mra


def test_run_imagej_macro_missing_exe_returns_false(tmp_path: Path):
    macro = tmp_path / "dummy.ijm"
    macro.write_text("// no-op")
    ok = mra.run_imagej_macro(str(tmp_path / "no_imagej"), str(macro), auto_close=True)
    assert ok is False


