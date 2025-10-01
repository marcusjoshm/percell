from pathlib import Path
from percell.domain.services.configuration_service import ConfigurationService


def test_configuration_service_load_save_get_set(tmp_path: Path):
    cfg_path = tmp_path / "config.json"
    cm = ConfigurationService(cfg_path)
    cm.load(create_if_missing=True)
    assert cm.get("missing", 42) == 42
    cm.set("imagej_path", "/Applications/ImageJ.app")
    cm.set("paths.cellpose", "cellpose_venv/bin/python")  # Uses dot notation directly
    cm.save()

    # Reload and check
    cm2 = ConfigurationService(cfg_path)
    cm2.load(create_if_missing=False)
    assert cm2.get("imagej_path") == "/Applications/ImageJ.app"
    assert cm2.get("paths.cellpose") == "cellpose_venv/bin/python"  # Uses dot notation directly


