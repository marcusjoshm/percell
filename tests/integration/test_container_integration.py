from pathlib import Path
from percell.application.container import build_container, Container


def test_build_container_creates_container(tmp_path: Path):
    """Test that build_container successfully creates a Container instance."""
    cfg = tmp_path / "cfg.json"
    cfg.write_text('{"paths": {"imagej": "/usr/bin/true", "cellpose": "/usr/bin/python"}}')
    c = build_container(cfg)
    assert isinstance(c, Container)
    assert c.cfg is not None
    assert c.imagej is not None
    assert c.cellpose is not None


