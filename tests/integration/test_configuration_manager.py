from pathlib import Path
from percell.application.configuration_manager import ConfigurationManager


def test_configuration_manager_load_save_get_set(tmp_path: Path):
    cfg_path = tmp_path / "config.json"
    cm = ConfigurationManager(cfg_path)
    cm.load()
    assert cm.get("missing", 42) == 42
    cm.set("imagej_path", "/Applications/ImageJ.app")
    cm.set_nested("paths.cellpose", "cellpose_venv/bin/python")
    cm.save()

    # Reload and check
    cm2 = ConfigurationManager(cfg_path)
    cm2.load()
    assert cm2.get("imagej_path") == "/Applications/ImageJ.app"
    assert cm2.get_nested("paths.cellpose") == "cellpose_venv/bin/python"


