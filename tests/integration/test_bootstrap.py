from pathlib import Path
from percell.main.bootstrap import bootstrap
from percell.application.container import Container


def test_bootstrap_builds_container(tmp_path: Path):
    cfg = tmp_path / "cfg.json"
    cfg.write_text('{"paths": {"imagej": "/usr/bin/true", "cellpose": "/usr/bin/python"}}')
    c = bootstrap(cfg)
    assert isinstance(c, Container)


