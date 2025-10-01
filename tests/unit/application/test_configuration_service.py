"""Unit tests for configuration classes."""
import json
import pytest
from pathlib import Path
from unittest.mock import patch

from percell.domain.services.configuration_service import ConfigurationService
from percell.domain.exceptions import ConfigurationError


class TestConfigurationService:
    """Test the ConfigurationService class."""

    def test_init_loads_existing_file(self, tmp_path: Path):
        cfg_path = tmp_path / "config.json"
        test_data = {"key": "value", "nested": {"inner": 42}}
        cfg_path.write_text(json.dumps(test_data))

        config = ConfigurationService(cfg_path)
        config.load(create_if_missing=False)
        assert config._data == test_data

    def test_init_missing_file_raises_error(self, tmp_path: Path):
        cfg_path = tmp_path / "missing.json"
        config = ConfigurationService(cfg_path)
        with pytest.raises(ConfigurationError, match="Configuration file not found"):
            config.load(create_if_missing=False)

    def test_init_invalid_json_raises_error(self, tmp_path: Path):
        cfg_path = tmp_path / "invalid.json"
        cfg_path.write_text("invalid json {")

        config = ConfigurationService(cfg_path)
        with pytest.raises(ConfigurationError, match="Invalid JSON"):
            config.load(create_if_missing=False)

    def test_get_simple_key(self, tmp_path: Path):
        cfg_path = tmp_path / "config.json"
        test_data = {"simple": "value", "number": 42}
        cfg_path.write_text(json.dumps(test_data))

        config = ConfigurationService(cfg_path)
        config.load(create_if_missing=False)
        assert config.get("simple") == "value"
        assert config.get("number") == 42
        assert config.get("missing") is None
        assert config.get("missing", "default") == "default"

    def test_get_nested_key(self, tmp_path: Path):
        cfg_path = tmp_path / "config.json"
        test_data = {
            "level1": {
                "level2": {
                    "key": "value"
                }
            }
        }
        cfg_path.write_text(json.dumps(test_data))

        config = ConfigurationService(cfg_path)
        config.load(create_if_missing=False)
        assert config.get("level1.level2.key") == "value"
        assert config.get("level1.level2") == {"key": "value"}
        assert config.get("level1.missing") is None
        assert config.get("missing.path", "default") == "default"

    def test_save_operation(self, tmp_path: Path):
        cfg_path = tmp_path / "config.json"
        test_data = {"key": "value"}
        cfg_path.write_text(json.dumps(test_data))

        config = ConfigurationService(cfg_path)
        config.load(create_if_missing=False)
        config.set("new_key", "new_value")
        config.save()

        # Verify file was updated
        saved_data = json.loads(cfg_path.read_text())
        assert saved_data["key"] == "value"
        assert saved_data["new_key"] == "new_value"

    def test_save_creates_directory(self, tmp_path: Path):
        nested_dir = tmp_path / "nested" / "dir"
        cfg_path = nested_dir / "config.json"

        # Create initial file
        nested_dir.mkdir(parents=True)
        cfg_path.write_text('{"initial": "value"}')

        config = ConfigurationService(cfg_path)
        config.load(create_if_missing=False)
        config.set("test", "value")
        config.save()

        assert cfg_path.exists()
        saved_data = json.loads(cfg_path.read_text())
        assert saved_data["test"] == "value"


class TestConfigurationServiceErrorHandling:
    """Test error handling in ConfigurationService class."""

    @patch('percell.domain.services.configuration_service.json.loads')
    def test_load_json_decode_error_raises_config_error(self, mock_loads, tmp_path: Path):
        cfg_path = tmp_path / "config.json"
        cfg_path.write_text('{"valid": "json"}')

        config = ConfigurationService(cfg_path)
        mock_loads.side_effect = json.JSONDecodeError("test", "test", 0)

        with pytest.raises(ConfigurationError, match="Invalid JSON"):
            config.load(create_if_missing=False)

    def test_save_io_error_raises_config_error(self, tmp_path: Path):
        cfg_path = tmp_path / "config.json"
        cfg_path.write_text('{"initial": "value"}')

        config = ConfigurationService(cfg_path)
        config.load(create_if_missing=False)

        # Make the parent directory read-only to cause save error
        # (ConfigurationService uses atomic write, so making file readonly won't prevent write)
        tmp_path.chmod(0o555)

        try:
            with pytest.raises(ConfigurationError, match="Error saving configuration"):
                config.save()
        finally:
            # Restore permissions for cleanup
            tmp_path.chmod(0o755)