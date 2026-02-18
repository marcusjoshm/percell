"""Integration tests for ImageJMacroAdapter, including sentinel-based
completion detection and stub cleanup."""

import sys
import textwrap
from pathlib import Path

import pytest

from percell.adapters.imagej_macro_adapter import (
    ImageJMacroAdapter,
    MACRO_DONE_SENTINEL,
)
from percell.domain.exceptions import FileSystemError


@pytest.mark.integration
def test_imagej_macro_adapter_handles_missing_executable(tmp_path: Path):
    adapter = ImageJMacroAdapter(tmp_path / "nonexistent_imagej")
    # Should raise FileSystemError when executable is not found
    with pytest.raises(FileSystemError, match="ImageJ executable not found"):
        adapter.run_macro(tmp_path / "macro.ijm", [])


# ---------------------------------------------------------------------------
# Helper: write a tiny Python script that pretends to be ImageJ
# ---------------------------------------------------------------------------

def _write_fake_imagej(tmp_path: Path, script_body: str) -> Path:
    """Create a Python script in *tmp_path* that acts as a fake ImageJ.

    The script is passed the same argv structure as real ImageJ:
        python fake_imagej.py -macro <macro_path> [args]
    """
    fake = tmp_path / "fake_imagej.py"
    fake.write_text(textwrap.dedent(script_body))
    return fake


def _adapter_for_script(
    tmp_path: Path, script_body: str
) -> tuple[ImageJMacroAdapter, Path]:
    """Return an adapter wired to a fake ImageJ script."""
    script = _write_fake_imagej(tmp_path, script_body)
    adapter = ImageJMacroAdapter(imagej_executable=Path(sys.executable))
    # Override _build_command so it runs our fake script instead
    real_build = adapter._build_command

    def patched_build(macro_path: Path, args):
        return [sys.executable, str(script)]

    adapter._build_command = patched_build
    return adapter, script


# ---------------------------------------------------------------------------
# Test: sentinel with clean exit
# ---------------------------------------------------------------------------

@pytest.mark.integration
def test_sentinel_detected_with_clean_exit(tmp_path: Path):
    """When the process prints MACRO_DONE and exits cleanly, the adapter
    should detect the sentinel and return 0."""
    adapter, _ = _adapter_for_script(tmp_path, f"""\
        import sys
        print("EXTRACT_TOTAL: 2")
        print("EXTRACT_CELL: 1/2")
        print("EXTRACT_CELL: 2/2")
        print("{MACRO_DONE_SENTINEL}")
        sys.exit(0)
    """)
    macro = tmp_path / "fake.ijm"
    macro.write_text("")
    result = adapter.run_macro(macro, [])
    assert result == 0
    assert adapter._sentinel_seen is True
    assert adapter._force_killed is False


# ---------------------------------------------------------------------------
# Test: sentinel with hung process (force-kill after grace)
# ---------------------------------------------------------------------------

@pytest.mark.integration
def test_sentinel_detected_with_hung_process(tmp_path: Path):
    """When the process prints MACRO_DONE but then hangs (simulating a
    hung JVM), the adapter should detect the sentinel, wait the short
    grace period, then force-kill and return 0."""
    adapter, _ = _adapter_for_script(tmp_path, f"""\
        import time, sys
        print("{MACRO_DONE_SENTINEL}")
        sys.stdout.flush()
        # Simulate hung JVM — sleep longer than POST_SENTINEL_GRACE
        time.sleep(60)
    """)
    # Use a very short grace period so the test runs fast
    adapter._POST_SENTINEL_GRACE = 1
    macro = tmp_path / "fake.ijm"
    macro.write_text("")
    result = adapter.run_macro(macro, [])
    assert result == 0
    assert adapter._sentinel_seen is True
    assert adapter._force_killed is True


# ---------------------------------------------------------------------------
# Test: no sentinel — fallback idle timeout
# ---------------------------------------------------------------------------

@pytest.mark.integration
def test_fallback_timeout_without_sentinel(tmp_path: Path):
    """When the process never prints MACRO_DONE, the adapter should fall
    back to the idle timeout and force-kill."""
    adapter, _ = _adapter_for_script(tmp_path, """\
        import time, sys
        print("some output")
        sys.stdout.flush()
        # Hang without printing sentinel
        time.sleep(60)
    """)
    # Use short timeouts so the test runs fast
    adapter._OUTPUT_IDLE_TIMEOUT = 1
    adapter._POST_SENTINEL_GRACE = 1
    macro = tmp_path / "fake.ijm"
    macro.write_text("")
    result = adapter.run_macro(macro, [])
    assert result == 0
    assert adapter._sentinel_seen is False
    assert adapter._force_killed is True


# ---------------------------------------------------------------------------
# Test: stub cleanup is called
# ---------------------------------------------------------------------------

@pytest.mark.integration
def test_stub_cleanup_called(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    """Stub cleanup should be called both before and after macro execution."""
    cleanup_calls: list[str] = []

    def mock_cleanup() -> None:
        cleanup_calls.append("cleanup")

    monkeypatch.setattr(
        ImageJMacroAdapter, "_cleanup_imagej_stubs", staticmethod(mock_cleanup)
    )

    adapter, _ = _adapter_for_script(tmp_path, f"""\
        import sys
        print("{MACRO_DONE_SENTINEL}")
        sys.exit(0)
    """)
    macro = tmp_path / "fake.ijm"
    macro.write_text("")
    adapter.run_macro(macro, [])

    # Should be called at least twice: once before, once in finally
    assert len(cleanup_calls) >= 2
