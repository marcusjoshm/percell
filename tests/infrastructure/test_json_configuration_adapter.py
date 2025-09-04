from pathlib import Path

from percell.infrastructure.config.json_configuration_adapter import JSONConfigurationAdapter


def test_json_configuration_adapter_roundtrip(tmp_path: Path):
    path = tmp_path / 'config.json'
    cfg = JSONConfigurationAdapter(path)
    cfg.load()  # should start empty
    assert cfg.to_dict() == {}

    cfg.set('a.b.c', 123)
    cfg.set('x', 'y')
    cfg.save()

    # Reload and ensure values persist
    cfg2 = JSONConfigurationAdapter(path)
    cfg2.load()
    assert cfg2.get('a.b.c') == 123
    assert cfg2.get('x') == 'y'
    assert cfg2.get('missing', 'default') == 'default'


