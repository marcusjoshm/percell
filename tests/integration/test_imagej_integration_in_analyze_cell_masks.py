from pathlib import Path
import sys
import types

# Stub heavy deps to avoid environment issues in import
sys.modules['cv2'] = types.ModuleType('cv2')

pandas_stub = types.ModuleType('pandas')

def _read_csv(*args, **kwargs):
    return None

class _DataFrame:
    def __init__(self, *args, **kwargs):
        pass

    def to_csv(self, *args, **kwargs):
        pass

    @staticmethod
    def from_records(*args, **kwargs):
        return _DataFrame()

pandas_stub.read_csv = _read_csv
pandas_stub.DataFrame = _DataFrame
sys.modules['pandas'] = pandas_stub

from percell.application.imagej_tasks import run_imagej_macro


def test_run_imagej_macro_missing_exe_returns_false(tmp_path: Path):
    macro = tmp_path / "dummy.ijm"
    macro.write_text("// no-op")
    ok = run_imagej_macro(str(tmp_path / "no_imagej"), str(macro), auto_close=True)
    assert ok is False


