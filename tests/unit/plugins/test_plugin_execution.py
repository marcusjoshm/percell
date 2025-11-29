"""Unit tests for plugin execution and validation."""
import pytest
import argparse
from pathlib import Path
from unittest.mock import Mock
import tempfile

from percell.plugins.base import PerCellPlugin, PluginMetadata


class TestPluginExecution:
    """Test plugin execution functionality."""

    def test_plugin_execute_is_called(self):
        """Test that execute method is called correctly."""
        metadata = PluginMetadata(
            name="test_execution",
            version="1.0.0",
            description="Test execution",
            author="Test"
        )

        class TestExecutionPlugin(PerCellPlugin):
            def __init__(self):
                super().__init__(metadata)
                self.executed = False

            def execute(self, ui, args):
                self.executed = True
                ui.info("Plugin executed")
                return args

        plugin = TestExecutionPlugin()
        mock_ui = Mock()
        args = argparse.Namespace()

        result = plugin.execute(mock_ui, args)

        assert plugin.executed
        mock_ui.info.assert_called_once_with("Plugin executed")
        assert result == args

    def test_plugin_can_modify_args(self):
        """Test that plugin can modify and return args."""
        metadata = PluginMetadata(
            name="test_modify",
            version="1.0.0",
            description="Test modify args",
            author="Test"
        )

        class ModifyArgsPlugin(PerCellPlugin):
            def __init__(self):
                super().__init__(metadata)

            def execute(self, ui, args):
                args.modified = True
                args.value = 42
                return args

        plugin = ModifyArgsPlugin()
        mock_ui = Mock()
        args = argparse.Namespace()

        result = plugin.execute(mock_ui, args)

        assert result.modified
        assert result.value == 42

    def test_plugin_can_return_none(self):
        """Test that plugin can return None to exit."""
        metadata = PluginMetadata(
            name="test_exit",
            version="1.0.0",
            description="Test exit",
            author="Test"
        )

        class ExitPlugin(PerCellPlugin):
            def __init__(self):
                super().__init__(metadata)

            def execute(self, ui, args):
                return None

        plugin = ExitPlugin()
        mock_ui = Mock()
        args = argparse.Namespace()

        result = plugin.execute(mock_ui, args)

        assert result is None


class TestPluginValidation:
    """Test plugin validation functionality."""

    def test_validation_passes_with_no_requirements(self):
        """Test validation passes when plugin has no requirements."""
        metadata = PluginMetadata(
            name="test_no_req",
            version="1.0.0",
            description="No requirements",
            author="Test"
        )

        class NoRequirementsPlugin(PerCellPlugin):
            def execute(self, ui, args):
                return args

        plugin = NoRequirementsPlugin(metadata)
        mock_ui = Mock()
        args = argparse.Namespace()

        assert plugin.validate(mock_ui, args) is True

    def test_validation_fails_when_input_dir_required_but_missing(self):
        """Test validation fails when input directory is required but not provided."""
        metadata = PluginMetadata(
            name="test_input_req",
            version="1.0.0",
            description="Requires input",
            author="Test",
            requires_input_dir=True
        )

        class InputRequiredPlugin(PerCellPlugin):
            def execute(self, ui, args):
                return args

        plugin = InputRequiredPlugin(metadata)
        mock_ui = Mock()
        args = argparse.Namespace()

        assert plugin.validate(mock_ui, args) is False
        mock_ui.error.assert_called()

    def test_validation_fails_when_input_dir_doesnt_exist(self):
        """Test validation fails when input directory doesn't exist."""
        metadata = PluginMetadata(
            name="test_input_exists",
            version="1.0.0",
            description="Requires input",
            author="Test",
            requires_input_dir=True
        )

        class InputExistsPlugin(PerCellPlugin):
            def execute(self, ui, args):
                return args

        plugin = InputExistsPlugin(metadata)
        mock_ui = Mock()
        args = argparse.Namespace(input="/nonexistent/path")

        assert plugin.validate(mock_ui, args) is False
        mock_ui.error.assert_called()

    def test_validation_passes_when_input_dir_exists(self):
        """Test validation passes when input directory exists."""
        with tempfile.TemporaryDirectory() as tmpdir:
            metadata = PluginMetadata(
                name="test_input_valid",
                version="1.0.0",
                description="Requires input",
                author="Test",
                requires_input_dir=True
            )

            class InputValidPlugin(PerCellPlugin):
                def execute(self, ui, args):
                    return args

            plugin = InputValidPlugin(metadata)
            mock_ui = Mock()
            args = argparse.Namespace(input=tmpdir)

            assert plugin.validate(mock_ui, args) is True

    def test_validation_fails_when_output_dir_required_but_missing(self):
        """Test validation fails when output directory is required but not provided."""
        metadata = PluginMetadata(
            name="test_output_req",
            version="1.0.0",
            description="Requires output",
            author="Test",
            requires_output_dir=True
        )

        class OutputRequiredPlugin(PerCellPlugin):
            def execute(self, ui, args):
                return args

        plugin = OutputRequiredPlugin(metadata)
        mock_ui = Mock()
        args = argparse.Namespace()

        assert plugin.validate(mock_ui, args) is False
        mock_ui.error.assert_called()

    def test_validation_passes_when_output_dir_provided(self):
        """Test validation passes when output directory is provided."""
        metadata = PluginMetadata(
            name="test_output_valid",
            version="1.0.0",
            description="Requires output",
            author="Test",
            requires_output_dir=True
        )

        class OutputValidPlugin(PerCellPlugin):
            def execute(self, ui, args):
                return args

        plugin = OutputValidPlugin(metadata)
        mock_ui = Mock()
        args = argparse.Namespace(output="/some/path")

        assert plugin.validate(mock_ui, args) is True

    def test_validation_fails_when_config_required_but_missing(self):
        """Test validation fails when config is required but not set."""
        metadata = PluginMetadata(
            name="test_config_req",
            version="1.0.0",
            description="Requires config",
            author="Test",
            requires_config=True
        )

        class ConfigRequiredPlugin(PerCellPlugin):
            def execute(self, ui, args):
                return args

        plugin = ConfigRequiredPlugin(metadata)
        mock_ui = Mock()
        args = argparse.Namespace()

        assert plugin.validate(mock_ui, args) is False
        mock_ui.error.assert_called()

    def test_validation_passes_when_config_provided(self):
        """Test validation passes when config is set."""
        metadata = PluginMetadata(
            name="test_config_valid",
            version="1.0.0",
            description="Requires config",
            author="Test",
            requires_config=True
        )

        class ConfigValidPlugin(PerCellPlugin):
            def execute(self, ui, args):
                return args

        plugin = ConfigValidPlugin(metadata)
        mock_config = Mock()
        plugin.set_config(mock_config)

        mock_ui = Mock()
        args = argparse.Namespace()

        assert plugin.validate(mock_ui, args) is True

    def test_custom_validation_can_extend_base(self):
        """Test that plugins can extend validation logic."""
        metadata = PluginMetadata(
            name="test_custom_validation",
            version="1.0.0",
            description="Custom validation",
            author="Test"
        )

        class CustomValidationPlugin(PerCellPlugin):
            def execute(self, ui, args):
                return args

            def validate(self, ui, args):
                if not super().validate(ui, args):
                    return False

                # Custom validation
                if not hasattr(args, 'custom_field'):
                    ui.error("Missing custom field")
                    return False

                return True

        plugin = CustomValidationPlugin(metadata)
        mock_ui = Mock()
        args = argparse.Namespace()

        # Should fail custom validation
        assert plugin.validate(mock_ui, args) is False

        # Should pass with custom field
        args.custom_field = "value"
        assert plugin.validate(mock_ui, args) is True


class TestPluginServiceAccess:
    """Test plugin service access functionality."""

    def test_plugin_can_access_config(self):
        """Test that plugin can access configuration service."""
        metadata = PluginMetadata(
            name="test_config_access",
            version="1.0.0",
            description="Config access",
            author="Test"
        )

        class ConfigAccessPlugin(PerCellPlugin):
            def execute(self, ui, args):
                config_value = self.config.get("test_key")
                ui.info(f"Config: {config_value}")
                return args

        plugin = ConfigAccessPlugin(metadata)
        mock_config = Mock()
        mock_config.get.return_value = "test_value"
        plugin.set_config(mock_config)

        mock_ui = Mock()
        args = argparse.Namespace()

        plugin.execute(mock_ui, args)

        mock_config.get.assert_called_once_with("test_key")

    def test_plugin_can_access_container(self):
        """Test that plugin can access dependency container."""
        metadata = PluginMetadata(
            name="test_container_access",
            version="1.0.0",
            description="Container access",
            author="Test"
        )

        class ContainerAccessPlugin(PerCellPlugin):
            def execute(self, ui, args):
                container = self.container
                ui.info(f"Container: {container}")
                return args

        plugin = ContainerAccessPlugin(metadata)
        mock_container = Mock()
        plugin.set_container(mock_container)

        mock_ui = Mock()
        args = argparse.Namespace()

        plugin.execute(mock_ui, args)

    def test_plugin_can_get_imagej_adapter(self):
        """Test that plugin can access ImageJ adapter."""
        metadata = PluginMetadata(
            name="test_imagej",
            version="1.0.0",
            description="ImageJ access",
            author="Test"
        )

        class ImageJAccessPlugin(PerCellPlugin):
            def execute(self, ui, args):
                imagej = self.get_imagej()
                if imagej:
                    ui.info("Has ImageJ")
                return args

        plugin = ImageJAccessPlugin(metadata)
        mock_container = Mock()
        mock_container.imagej = Mock()
        plugin.set_container(mock_container)

        mock_ui = Mock()
        args = argparse.Namespace()

        plugin.execute(mock_ui, args)

        assert plugin.get_imagej() == mock_container.imagej

    def test_plugin_adapters_return_none_when_not_available(self):
        """Test that adapter getters return None when container has no adapters."""
        metadata = PluginMetadata(
            name="test_no_adapters",
            version="1.0.0",
            description="No adapters",
            author="Test"
        )

        class NoAdaptersPlugin(PerCellPlugin):
            def __init__(self):
                super().__init__(metadata)

            def execute(self, ui, args):
                return args

        plugin = NoAdaptersPlugin()
        # Set container with no adapter attributes
        mock_container = Mock(spec=[])
        plugin.set_container(mock_container)

        # With container but no adapters, should return None via getattr default
        assert plugin.get_imagej() is None
        assert plugin.get_filesystem() is None
        assert plugin.get_image_processor() is None
        assert plugin.get_cellpose() is None

    def test_plugin_raises_error_when_config_not_set(self):
        """Test that accessing config without setting it raises error."""
        metadata = PluginMetadata(
            name="test_no_config",
            version="1.0.0",
            description="No config",
            author="Test"
        )

        class NoConfigPlugin(PerCellPlugin):
            def execute(self, ui, args):
                return args

        plugin = NoConfigPlugin(metadata)

        with pytest.raises(RuntimeError, match="Config not set"):
            _ = plugin.config


class TestPluginMetadata:
    """Test plugin metadata functionality."""

    def test_plugin_metadata_properties(self):
        """Test that plugin exposes metadata properties."""
        metadata = PluginMetadata(
            name="test_properties",
            version="2.0.0",
            description="Test properties",
            author="Test Author"
        )

        class PropertiesPlugin(PerCellPlugin):
            def execute(self, ui, args):
                return args

        plugin = PropertiesPlugin(metadata)

        assert plugin.name == "test_properties"
        assert plugin.version == "2.0.0"
        assert plugin.description == "Test properties"

    def test_get_menu_title_uses_metadata(self):
        """Test that get_menu_title uses metadata."""
        metadata = PluginMetadata(
            name="test_menu",
            version="1.0.0",
            description="Test menu",
            author="Test",
            menu_title="Custom Menu Title"
        )

        class MenuTitlePlugin(PerCellPlugin):
            def execute(self, ui, args):
                return args

        plugin = MenuTitlePlugin(metadata)

        assert plugin.get_menu_title() == "Custom Menu Title"

    def test_get_menu_title_generates_from_name(self):
        """Test that menu title is generated from name when not provided."""
        metadata = PluginMetadata(
            name="auto_generate_title",
            version="1.0.0",
            description="Test",
            author="Test"
        )

        class AutoTitlePlugin(PerCellPlugin):
            def execute(self, ui, args):
                return args

        plugin = AutoTitlePlugin(metadata)

        # Should convert underscores to spaces and title case
        assert plugin.get_menu_title() == "Auto Generate Title"

    def test_get_menu_description(self):
        """Test that get_menu_description works correctly."""
        metadata = PluginMetadata(
            name="test_desc",
            version="1.0.0",
            description="Default description",
            author="Test",
            menu_description="Custom menu description"
        )

        class DescriptionPlugin(PerCellPlugin):
            def execute(self, ui, args):
                return args

        plugin = DescriptionPlugin(metadata)

        assert plugin.get_menu_description() == "Custom menu description"

    def test_metadata_to_dict_and_from_dict(self):
        """Test metadata serialization."""
        metadata = PluginMetadata(
            name="test_serialize",
            version="1.0.0",
            description="Test serialization",
            author="Test Author",
            author_email="test@example.com",
            dependencies=["numpy", "pandas"],
            requires_config=True,
            requires_input_dir=True,
            requires_output_dir=False,
            category="test",
            menu_title="Test Menu",
            menu_description="Test Description"
        )

        # Convert to dict
        data = metadata.to_dict()

        assert data["name"] == "test_serialize"
        assert data["version"] == "1.0.0"
        assert data["author_email"] == "test@example.com"
        assert data["dependencies"] == ["numpy", "pandas"]

        # Convert back from dict
        restored = PluginMetadata.from_dict(data)

        assert restored.name == metadata.name
        assert restored.version == metadata.version
        assert restored.author_email == metadata.author_email
        assert restored.dependencies == metadata.dependencies
