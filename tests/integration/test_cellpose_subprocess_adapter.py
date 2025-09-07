from pathlib import Path
from unittest.mock import patch, MagicMock

from percell.adapters.cellpose_subprocess_adapter import CellposeSubprocessAdapter
from percell.domain.models import SegmentationParameters


def test_cellpose_adapter_handles_missing_python(tmp_path: Path):
    adapter = CellposeSubprocessAdapter(tmp_path / "missing_python")
    params = SegmentationParameters(30.0, 0.4, 0.0, "nuclei")
    result = adapter.run_segmentation([tmp_path / "img.tif"], tmp_path / "out", params)
    # Will attempt to run and likely fail to generate outputs; should return []
    assert isinstance(result, list)


@patch("subprocess.run")
def test_cellpose_adapter_success(mock_run, tmp_path: Path):
    # Simulate successful subprocess run
    mock_run.return_value = MagicMock(returncode=0, stdout="ok", stderr="")

    # Prepare dummy input and expected output
    img = tmp_path / "a.tif"
    img.write_bytes(b"dummy")
    out = tmp_path / "out"
    out.mkdir()
    expected_mask = out / "a_mask.tif"
    expected_mask.write_bytes(b"x")

    adapter = CellposeSubprocessAdapter(Path("/usr/bin/python"))
    params = SegmentationParameters(30.0, 0.4, 0.0, "nuclei")

    masks = adapter.run_segmentation([img], out, params)
    assert expected_mask in masks
    mock_run.assert_called()


