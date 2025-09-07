from __future__ import annotations

import json
from pathlib import Path

import pytest


def test_create_default_config_and_roundtrip(tmp_path: Path):
    from percell.application.config_api import create_default_config, Config

    cfg_path = tmp_path / "config.json"
    cfg = create_default_config(str(cfg_path))
    assert isinstance(cfg, Config)
    assert cfg_path.exists()

    data = json.loads(cfg_path.read_text())
    assert "analysis" in data and "output" in data and "directories" in data

    # Modify and save
    cfg.set("analysis.default_bins", 7)
    cfg.save()
    reloaded = Config(str(cfg_path))
    assert reloaded.get("analysis.default_bins") == 7


def test_get_set_nested_and_update(tmp_path: Path):
    from percell.application.config_api import create_default_config

    cfg_path = tmp_path / "config.json"
    cfg = create_default_config(str(cfg_path))
    assert cfg.get("imagej_path", "") == ""

    cfg.set("paths.imagej", "/Applications/Fiji.app")
    assert cfg.get("paths.imagej") == "/Applications/Fiji.app"

    cfg.update({"paths.python": "/usr/bin/python"})
    assert cfg.get("paths.python") == "/usr/bin/python"


def test_validate_and_software_paths(tmp_path: Path):
    from percell.application.config_api import create_default_config, ConfigError, validate_software_paths

    cfg_path = tmp_path / "config.json"
    cfg = create_default_config(str(cfg_path))

    # Missing required keys should raise
    with pytest.raises(ConfigError):
        cfg.validate()

    # Fill minimal required keys
    cfg.set("imagej_path", "/Applications/Fiji.app")
    cfg.set("cellpose_path", "")  # allow empty
    import sys
    cfg.set("python_path", sys.executable)
    cfg.save()

    assert cfg.validate() is True

    results = validate_software_paths(cfg)
    assert isinstance(results, dict)
    assert "python" in results


def test_detect_software_paths_contains_python():
    from percell.application.config_api import detect_software_paths
    paths = detect_software_paths()
    assert isinstance(paths.get("python"), str) and len(paths.get("python")) > 0


