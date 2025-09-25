"""Unit tests for the consolidated ConfigurationService."""
import json
import pytest
from pathlib import Path
from unittest.mock import patch, mock_open

from percell.domain.services.configuration_service import ConfigurationService, create_configuration_service
from percell.domain.exceptions import ConfigurationError


class TestConfigurationService:
    """Test the consolidated ConfigurationService class."""

    def test_init_with_string_path(self, tmp_path: Path):
        service = ConfigurationService(str(tmp_path / "config.json"))
        assert isinstance(service.path, Path)
        assert service._data == {}

    def test_init_with_path_object(self, tmp_path: Path):
        path = tmp_path / "config.json"
        service = ConfigurationService(path)
        assert service.path == path
        assert service._data == {}

    def test_load_missing_file_creates_empty(self, tmp_path: Path):
        path = tmp_path / "config.json"
        service = ConfigurationService(path)
        service.load(create_if_missing=True)
        assert service._data == {}

    def test_load_missing_file_raises_error_when_required(self, tmp_path: Path):
        path = tmp_path / "config.json"
        service = ConfigurationService(path)
        with pytest.raises(ConfigurationError, match="Configuration file not found"):
            service.load(create_if_missing=False)

    def test_load_existing_file(self, tmp_path: Path):
        path = tmp_path / "config.json"
        data = {"key": "value", "nested": {"inner": 42}}
        path.write_text(json.dumps(data))

        service = ConfigurationService(path)
        service.load()
        assert service._data == data

    def test_load_invalid_json_raises_error(self, tmp_path: Path):
        path = tmp_path / "config.json"
        path.write_text("invalid json {")

        service = ConfigurationService(path)
        with pytest.raises(ConfigurationError, match="Invalid JSON"):
            service.load()

    def test_save_creates_directory(self, tmp_path: Path):
        nested_dir = tmp_path / "nested" / "subdir"
        path = nested_dir / "config.json"

        service = ConfigurationService(path)
        service.set("test", "value")
        service.save()

        assert path.exists()
        assert json.loads(path.read_text()) == {"test": "value"}

    def test_atomic_save_operation(self, tmp_path: Path):
        path = tmp_path / "config.json"
        service = ConfigurationService(path)
        service.set("key", "value")

        # Mock tempfile to ensure atomic operation
        with patch('tempfile.NamedTemporaryFile') as mock_temp:
            mock_file = mock_open()
            mock_temp.return_value.__enter__ = mock_file
            mock_temp.return_value.__exit__ = lambda *args: None
            mock_temp.return_value.name = str(tmp_path / "temp_config.json")

            with patch('pathlib.Path.replace') as mock_replace:
                service.save()
                mock_replace.assert_called_once()

    def test_get_simple_key(self, tmp_path: Path):
        path = tmp_path / "config.json"
        service = ConfigurationService(path)
        service._data = {"key": "value", "number": 42}

        assert service.get("key") == "value"
        assert service.get("number") == 42
        assert service.get("missing") is None
        assert service.get("missing", "default") == "default"

    def test_get_nested_key(self, tmp_path: Path):
        path = tmp_path / "config.json"
        service = ConfigurationService(path)
        service._data = {
            "level1": {
                "level2": {
                    "key": "value"
                }
            }
        }

        assert service.get("level1.level2.key") == "value"
        assert service.get("level1.level2") == {"key": "value"}
        assert service.get("level1.missing") is None
        assert service.get("missing.path", "default") == "default"

    def test_set_simple_key(self, tmp_path: Path):
        path = tmp_path / "config.json"
        service = ConfigurationService(path)

        service.set("key", "value")
        assert service._data["key"] == "value"

        service.set("key", "new_value")
        assert service._data["key"] == "new_value"

    def test_set_nested_key(self, tmp_path: Path):
        path = tmp_path / "config.json"
        service = ConfigurationService(path)

        service.set("level1.level2.key", "value")
        assert service._data["level1"]["level2"]["key"] == "value"

        # Test overwriting non-dict with dict
        service.set("level1.level2", "not_dict")
        service.set("level1.level2.new_key", "new_value")
        assert service._data["level1"]["level2"]["new_key"] == "new_value"

    def test_update_multiple_values(self, tmp_path: Path):
        path = tmp_path / "config.json"
        service = ConfigurationService(path)

        service.update({
            "key1": "value1",
            "key2": "value2",
            "nested.key": "nested_value"
        })

        assert service.get("key1") == "value1"
        assert service.get("key2") == "value2"
        assert service.get("nested.key") == "nested_value"

    def test_has_key_existence(self, tmp_path: Path):
        path = tmp_path / "config.json"
        service = ConfigurationService(path)
        service._data = {"key": "value", "nested": {"inner": "value"}}

        assert service.has("key") is True
        assert service.has("missing") is False
        assert service.has("nested.inner") is True
        assert service.has("nested.missing") is False

    def test_delete_simple_key(self, tmp_path: Path):
        path = tmp_path / "config.json"
        service = ConfigurationService(path)
        service._data = {"key1": "value1", "key2": "value2"}

        assert service.delete("key1") is True
        assert "key1" not in service._data
        assert service.delete("missing") is False

    def test_delete_nested_key(self, tmp_path: Path):
        path = tmp_path / "config.json"
        service = ConfigurationService(path)
        service._data = {
            "level1": {
                "level2": {
                    "key1": "value1",
                    "key2": "value2"
                }
            }
        }

        assert service.delete("level1.level2.key1") is True
        assert "key1" not in service._data["level1"]["level2"]
        assert service._data["level1"]["level2"]["key2"] == "value2"

        assert service.delete("level1.missing.key") is False

    def test_to_dict_returns_copy(self, tmp_path: Path):
        path = tmp_path / "config.json"
        service = ConfigurationService(path)
        service._data = {"key": {"nested": "value"}}

        config_dict = service.to_dict()
        config_dict["key"]["nested"] = "modified"

        # Original should be unchanged
        assert service._data["key"]["nested"] == "value"

    def test_clear_removes_all_data(self, tmp_path: Path):
        path = tmp_path / "config.json"
        service = ConfigurationService(path)
        service._data = {"key1": "value1", "key2": "value2"}

        service.clear()
        assert service._data == {}

    def test_get_resolved_path_absolute(self, tmp_path: Path):
        path = tmp_path / "config.json"
        service = ConfigurationService(path)
        abs_path = "/absolute/path"
        service.set("absolute_path", abs_path)

        resolved = service.get_resolved_path("absolute_path")
        assert resolved == Path(abs_path)

    def test_get_resolved_path_relative(self, tmp_path: Path):
        path = tmp_path / "config.json"
        service = ConfigurationService(path)
        rel_path = "relative/path"
        service.set("relative_path", rel_path)

        project_root = Path("/project/root")
        resolved = service.get_resolved_path("relative_path", project_root)
        assert resolved == project_root / rel_path

    def test_get_resolved_path_missing_key(self, tmp_path: Path):
        path = tmp_path / "config.json"
        service = ConfigurationService(path)

        resolved = service.get_resolved_path("missing_key")
        assert resolved is None


class TestConfigurationServiceIntegration:
    """Integration tests for ConfigurationService."""

    def test_full_lifecycle(self, tmp_path: Path):
        path = tmp_path / "config.json"

        # Create and populate
        service1 = ConfigurationService(path)
        service1.set("simple_key", "value")
        service1.set("nested.key", "nested_value")
        service1.set("paths.imagej", "/path/to/imagej")
        service1.save()

        # Load in new instance
        service2 = ConfigurationService(path)
        service2.load(create_if_missing=False)

        assert service2.get("simple_key") == "value"
        assert service2.get("nested.key") == "nested_value"
        assert service2.get("paths.imagej") == "/path/to/imagej"

        # Modify and save again
        service2.set("new_key", "new_value")
        service2.delete("simple_key")
        service2.save()

        # Verify changes persist
        service3 = ConfigurationService(path)
        service3.load()

        assert service3.has("simple_key") is False
        assert service3.get("new_key") == "new_value"
        assert service3.get("nested.key") == "nested_value"


class TestConfigurationServiceErrorHandling:
    """Test error handling in ConfigurationService."""

    def test_save_io_error(self, tmp_path: Path):
        path = tmp_path / "readonly" / "config.json"
        readonly_dir = tmp_path / "readonly"
        readonly_dir.mkdir()
        readonly_dir.chmod(0o444)  # Read-only directory

        service = ConfigurationService(path)
        service.set("key", "value")

        with pytest.raises(ConfigurationError, match="Error saving configuration"):
            service.save()

        # Clean up
        readonly_dir.chmod(0o755)

    def test_load_io_error(self, tmp_path: Path):
        path = tmp_path / "config.json"
        path.write_text('{"key": "value"}')

        service = ConfigurationService(path)

        # Mock Path.read_text at class level to raise IOError
        with patch('pathlib.Path.read_text', side_effect=IOError("Mock IO error")):
            with pytest.raises(ConfigurationError, match="Error reading configuration"):
                service.load()


class TestConfigurationServiceFactory:
    """Test the factory function."""

    def test_create_configuration_service(self, tmp_path: Path):
        path = tmp_path / "config.json"
        data = {"key": "value"}
        path.write_text(json.dumps(data))

        service = create_configuration_service(path)
        assert service.get("key") == "value"

    def test_create_configuration_service_missing_file(self, tmp_path: Path):
        path = tmp_path / "missing.json"

        service = create_configuration_service(path, create_if_missing=True)
        assert service._data == {}

        with pytest.raises(ConfigurationError):
            create_configuration_service(path, create_if_missing=False)