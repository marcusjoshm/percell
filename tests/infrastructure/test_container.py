from pathlib import Path

from percell.infrastructure.bootstrap.container import Container, AppConfig


def test_container_wires_group_cells_use_case(tmp_path: Path):
    cfg = AppConfig()
    c = Container(cfg)
    uc = c.group_cells_use_case()
    assert uc is not None


def test_container_wires_segment_cells_use_case(tmp_path: Path):
    c = Container(AppConfig())
    uc = c.segment_cells_use_case()
    assert uc is not None


