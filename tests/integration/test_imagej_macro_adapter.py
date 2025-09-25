from pathlib import Path

import pytest

from percell.adapters.imagej_macro_adapter import ImageJMacroAdapter
from percell.domain.exceptions import FileSystemError


@pytest.mark.integration
def test_imagej_macro_adapter_handles_missing_executable(tmp_path: Path):
    adapter = ImageJMacroAdapter(tmp_path / "nonexistent_imagej")
    # Should raise FileSystemError when executable is not found
    with pytest.raises(FileSystemError, match="ImageJ executable not found"):
        adapter.run_macro(tmp_path / "macro.ijm", [])


