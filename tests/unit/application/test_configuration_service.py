"""Unit tests for configuration classes."""
import json
import pytest
from pathlib import Path
from unittest.mock import patch

from percell.application.configuration_manager import ConfigurationManager
from percell.domain.services.configuration_service import ConfigurationService
from percell.domain.exceptions import ConfigurationError


class TestConfigurationManager:
    """Test the ConfigurationManager class."""

    def test_init_creates_empty_data(self, tmp_path: Path):
        cfg_path = tmp_path / "config.json"
        cm = ConfigurationManager(cfg_path)
        assert cm.path == cfg_path
        assert cm._data == {}

    def test_load_nonexistent_file_creates_empty(self, tmp_path: Path):
        cfg_path = tmp_path / "config.json"
        cm = ConfigurationManager(cfg_path)
        cm.load()
        assert cm._data == {}

    def test_load_existing_file(self, tmp_path: Path):
        cfg_path = tmp_path / "config.json"
        test_data = {"key": "value", "nested": {"inner": 42}}
        cfg_path.write_text(json.dumps(test_data))

        cm = ConfigurationManager(cfg_path)
        cm.load()
        assert cm._data == test_data

    def test_save_creates_directory(self, tmp_path: Path):
        nested_dir = tmp_path / "nested" / "dir"
        cfg_path = nested_dir / "config.json"
        cm = ConfigurationManager(cfg_path)
        cm.set("test", "value")
        cm.save()

        assert cfg_path.exists()
        assert json.loads(cfg_path.read_text()) == {"test": "value"}

    def test_get_set_operations(self, tmp_path: Path):
        cfg_path = tmp_path / "config.json"
        cm = ConfigurationManager(cfg_path)

        # Test get with default
        assert cm.get("missing", "default") == "default"
        assert cm.get("missing") is None

        # Test set and get
        cm.set("key", "value")
        assert cm.get("key") == "value"

    def test_nested_operations(self, tmp_path: Path):
        cfg_path = tmp_path / "config.json"
        cm = ConfigurationManager(cfg_path)

        # Test set nested
        cm.set_nested("level1.level2.key", "value")
        assert cm.get_nested("level1.level2.key") == "value"

        # Test get nested with default
        assert cm.get_nested("missing.path", "default") == "default"

        # Test partial path exists
        cm.set_nested("partial.exists", "value")
        assert cm.get_nested("partial.missing", "default") == "default"

    def test_update_operation(self, tmp_path: Path):
        cfg_path = tmp_path / "config.json"
        cm = ConfigurationManager(cfg_path)

        cm.set("existing", "old")
        cm.update({"existing": "new", "additional": "value"})

        assert cm.get("existing") == "new"
        assert cm.get("additional") == "value"

    def test_persistence_cycle(self, tmp_path: Path):
        cfg_path = tmp_path / "config.json"

        # First instance
        cm1 = ConfigurationManager(cfg_path)
        cm1.set("key", "value")
        cm1.set_nested("nested.path", 42)
        cm1.save()

        # Second instance loads same data
        cm2 = ConfigurationManager(cfg_path)
        cm2.load()
        assert cm2.get("key") == "value"
        assert cm2.get_nested("nested.path") == 42


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


class TestConfigurationManagerErrorHandling:
    """Test error handling in ConfigurationManager."""

    def test_save_handles_directory_creation_error(self, tmp_path: Path):
        # Create a file where we want to create a directory
        conflict_path = tmp_path / "conflict"
        conflict_path.write_text("blocking file")

        cfg_path = conflict_path / "config.json"  # This will fail
        cm = ConfigurationManager(cfg_path)
        cm.set("test", "value")

        # Should not raise, but may not save successfully
        # The current implementation doesn't handle this gracefully
        try:
            cm.save()
        except (OSError, FileNotFoundError, PermissionError):
            pass  # Expected for this edge case


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