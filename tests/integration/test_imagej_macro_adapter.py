from pathlib import Path

import pytest

from percell.adapters.imagej_macro_adapter import ImageJMacroAdapter


@pytest.mark.integration
def test_imagej_macro_adapter_handles_missing_executable(tmp_path: Path):
    adapter = ImageJMacroAdapter(tmp_path / "nonexistent_imagej")
    # Should return non-zero (1) due to execution failure
    rc = adapter.run_macro(tmp_path / "macro.ijm", [])
    assert rc != 0


