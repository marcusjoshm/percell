from pathlib import Path
from unittest.mock import patch, MagicMock

from percell.adapters.outbound.imagej_macro_adapter import ImageJMacroAdapter
from percell.ports.outbound.macro_runner_port import MacroResult


def test_validate_macro(tmp_path: Path):
    macro_dir = tmp_path / 'macros'
    macro_dir.mkdir()
    (macro_dir / 'hello.ijm').write_text('print("hi");')
    adapter = ImageJMacroAdapter(imagej_path=Path('/Applications/Fiji.app/ImageJ-macosx'), macro_dir=macro_dir)
    assert adapter.validate_macro('hello.ijm') is True
    assert adapter.validate_macro('missing.ijm') is False


@patch('percell.adapters.outbound.imagej_macro_adapter.run_subprocess_with_spinner')
def test_run_macro_success(mock_runner, tmp_path: Path):
    macro_dir = tmp_path / 'macros'
    macro_dir.mkdir()
    (macro_dir / 'do.ijm').write_text('print("do");')

    # fake successful subprocess result
    fake = MagicMock()
    fake.returncode = 0
    fake.stdout = 'ok'
    fake.stderr = ''
    mock_runner.return_value = fake

    adapter = ImageJMacroAdapter(imagej_path=Path('/fake/ImageJ'), macro_dir=macro_dir)
    result = adapter.run_macro('do.ijm', {"x": 1, "y": 2})
    assert isinstance(result, MacroResult)
    assert result.success is True
    assert result.stdout == 'ok'


@patch('percell.adapters.outbound.imagej_macro_adapter.run_subprocess_with_spinner')
def test_run_macro_failure(mock_runner, tmp_path: Path):
    macro_dir = tmp_path / 'macros'
    macro_dir.mkdir()
    (macro_dir / 'do.ijm').write_text('print("do");')

    fake = MagicMock()
    fake.returncode = 1
    fake.stdout = ''
    fake.stderr = 'err'
    mock_runner.return_value = fake

    adapter = ImageJMacroAdapter(imagej_path=Path('/fake/ImageJ'), macro_dir=macro_dir)
    result = adapter.run_macro('do.ijm', {})
    assert result.success is False
