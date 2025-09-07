from pathlib import Path
from percell.application.container import build_container, Container


def test_build_container(tmp_path: Path):
    cfg = tmp_path / "cfg.json"
    cfg.write_text('{"paths": {"imagej": "/usr/bin/true", "cellpose": "/usr/bin/python"}}')
    c = build_container(cfg)
    assert isinstance(c, Container)
    # Ensure core services exist
    assert c.workflow is not None and c.step_exec is not None
    assert c.fs is not None and c.imgproc is not None


