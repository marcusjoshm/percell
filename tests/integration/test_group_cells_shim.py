from pathlib import Path
import os
import sys
import numpy as np

import importlib.util
import importlib


def test_group_cells_legacy_shim_uses_new_arch(tmp_path, monkeypatch):
    # Ensure package root on sys.path
    repo_root = Path(__file__).resolve().parents[2]
    if str(repo_root) not in sys.path:
        sys.path.insert(0, str(repo_root))

    # Prepare input directory with channel path containing CELL*.tif images
    base = tmp_path / "cells"
    chan_dir = base / "condA" / "region1_chanA"
    chan_dir.mkdir(parents=True, exist_ok=True)

    # Create two small images matching legacy naming
    img_a = np.ones((4, 4), dtype=np.uint16)
    img_b = np.full((4, 4), 2, dtype=np.uint16)

    # Try normal import first; fall back to dynamic import for container
    try:
        from percell.infrastructure.bootstrap.container import get_container  # type: ignore
        container = get_container()
    except Exception:
        container_path = (repo_root / "percell" / "infrastructure" / "bootstrap" / "container.py")
        spec_c = importlib.util.spec_from_file_location("container_mod", container_path)
        container_mod = importlib.util.module_from_spec(spec_c)  # type: ignore[arg-type]
        assert spec_c is not None and spec_c.loader is not None
        spec_c.loader.exec_module(container_mod)  # type: ignore[attr-defined]
        container = container_mod.get_container()

    image = container.image_adapter()
    image.write(chan_dir / "CELL001.tif", img_a)
    image.write(chan_dir / "CELL002.tif", img_b)

    out_dir = tmp_path / "out"

    # Activate shim via environment and construct argv
    monkeypatch.setenv("PERCELL_USE_NEW_ARCH", "1")
    argv = [
        "prog",
        "--cells-dir",
        str(base),
        "--output-dir",
        str(out_dir),
        "--bins",
        "2",
        "--channels",
        "chanA",
        "--use-new-arch",
    ]
    monkeypatch.setattr("sys.argv", argv, raising=False)

    # Dynamically import legacy module by file path to avoid site-package shadowing issues
    group_cells_path = (repo_root / "percell" / "modules" / "group_cells.py")
    spec = importlib.util.spec_from_file_location("legacy_group_cells", group_cells_path)
    legacy_group_cells = importlib.util.module_from_spec(spec)  # type: ignore[arg-type]
    assert spec is not None and spec.loader is not None
    spec.loader.exec_module(legacy_group_cells)  # type: ignore[attr-defined]

    rc = legacy_group_cells.main()
    assert rc == 0

    # Verify shim wrote outputs under legacy layout: <out>/<parent>/<leaf>/group_*.tif
    expected_subdir = out_dir / chan_dir.parent.name / chan_dir.name
    group_files = sorted(expected_subdir.glob("group_*.tif"))
    assert len(group_files) >= 1


