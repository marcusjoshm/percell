"""Unit tests for the plugin registry."""
import pytest
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch
import argparse

from percell.plugins.base import PerCellPlugin, PluginMetadata, LegacyPluginAdapter
from percell.plugins.registry import PluginRegistry


# Test fixtures
@pytest.fixture
def sample_metadata():
    """Create sample plugin metadata."""
    return PluginMetadata(
        name="test_plugin",
        version="1.0.0",
        description="Test plugin",
        author="Test Author"
    )


@pytest.fixture
def sample_plugin_class(sample_metadata):
    """Create a sample plugin class."""
    class TestPlugin(PerCellPlugin):
        METADATA = sample_metadata

        def __init__(self):
            super().__init__(sample_metadata)

        def execute(self, ui, args):
            ui.info("Test plugin executed")
            return args

    return TestPlugin


@pytest.fixture
def registry():
    """Create a fresh plugin registry."""
    return PluginRegistry()


class TestPluginRegistry:
    """Test the PluginRegistry class."""

    def test_creates_empty_registry(self, registry):
        """Test that registry starts empty."""
        assert len(registry.get_plugin_names()) == 0
        assert len(registry.get_all_plugins()) == 0

    def test_register_plugin_instance(self, registry, sample_plugin_class, sample_metadata):
        """Test registering a plugin instance."""
        plugin = sample_plugin_class()
        registry.register(plugin, sample_metadata)

        assert "test_plugin" in registry.get_plugin_names()
        assert registry.get_plugin("test_plugin") == plugin
        assert registry.get_metadata("test_plugin") == sample_metadata

    def test_register_plugin_class(self, registry, sample_metadata):
        """Test registering a plugin class (lazy instantiation)."""
        class TestPlugin(PerCellPlugin):
            METADATA = sample_metadata

            def __init__(self, metadata=None):
                # Registry will pass metadata, so accept it
                super().__init__(metadata or sample_metadata)

            def execute(self, ui, args):
                ui.info("Test plugin executed")
                return args

        registry.register_class(TestPlugin, sample_metadata)

        assert "test_plugin" in registry.get_plugin_names()
        assert registry.get_metadata("test_plugin") == sample_metadata

        # Plugin should not be instantiated yet
        assert "test_plugin" not in registry._plugins

        # Get plugin triggers instantiation
        plugin = registry.get_plugin("test_plugin")
        assert plugin is not None
        assert isinstance(plugin, TestPlugin)
        assert "test_plugin" in registry._plugins

    def test_register_legacy_function(self, registry):
        """Test registering a legacy plugin function."""
        def legacy_plugin(ui, args):
            ui.info("Legacy plugin executed")
            return args

        metadata = PluginMetadata(
            name="legacy_plugin",
            version="1.0.0",
            description="Legacy plugin",
            author="Test"
        )

        registry.register_legacy_function(legacy_plugin, metadata)

        assert "legacy_plugin" in registry.get_plugin_names()
        plugin = registry.get_plugin("legacy_plugin")
        assert isinstance(plugin, LegacyPluginAdapter)

    def test_get_nonexistent_plugin_returns_none(self, registry):
        """Test getting a plugin that doesn't exist."""
        assert registry.get_plugin("nonexistent") is None
        assert registry.get_metadata("nonexistent") is None

    def test_get_all_plugins(self, registry, sample_plugin_class, sample_metadata):
        """Test getting all plugins."""
        plugin1 = sample_plugin_class()
        registry.register(plugin1, sample_metadata)

        metadata2 = PluginMetadata(
            name="test_plugin_2",
            version="1.0.0",
            description="Test plugin 2",
            author="Test"
        )

        class TestPlugin2(PerCellPlugin):
            def execute(self, ui, args):
                return args

        plugin2 = TestPlugin2(metadata2)
        registry.register(plugin2, metadata2)

        all_plugins = registry.get_all_plugins()
        assert len(all_plugins) == 2
        assert plugin1 in all_plugins
        assert plugin2 in all_plugins

    def test_register_class_without_metadata(self, registry):
        """Test registering a class without explicit metadata."""
        class SimplePlugin(PerCellPlugin):
            def execute(self, ui, args):
                return args

        registry.register_class(SimplePlugin)

        # Should create default metadata from class name
        assert "simple" in registry.get_plugin_names()
        metadata = registry.get_metadata("simple")
        assert metadata.name == "simple"
        assert metadata.version == "1.0.0"

    def test_register_class_with_class_metadata_attribute(self, registry):
        """Test registering a class with METADATA class attribute."""
        metadata = PluginMetadata(
            name="attributed_plugin",
            version="2.0.0",
            description="Has METADATA attribute",
            author="Test"
        )

        class AttributedPlugin(PerCellPlugin):
            METADATA = metadata

            def execute(self, ui, args):
                return args

        registry.register_class(AttributedPlugin)

        assert "attributed_plugin" in registry.get_plugin_names()
        assert registry.get_metadata("attributed_plugin") == metadata


class TestPluginDiscovery:
    """Test plugin discovery functionality."""

    def test_discover_plugins_from_file(self, registry):
        """Test discovering plugins from a Python file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            plugin_dir = Path(tmpdir)

            # Create a test plugin file
            plugin_file = plugin_dir / "test_discovery_plugin.py"
            plugin_code = '''
from percell.plugins.base import PerCellPlugin, PluginMetadata

METADATA = PluginMetadata(
    name="discovered_plugin",
    version="1.0.0",
    description="Discovered plugin",
    author="Test"
)

class DiscoveredPlugin(PerCellPlugin):
    METADATA = METADATA

    def __init__(self):
        super().__init__(METADATA)

    def execute(self, ui, args):
        return args
'''
            plugin_file.write_text(plugin_code)

            # Discover plugins
            registry.discover_plugins(plugin_dir)

            # Should have discovered the plugin
            assert "discovered_plugin" in registry.get_plugin_names()

    def test_discover_legacy_plugin_function(self, registry):
        """Test discovering legacy plugin functions."""
        with tempfile.TemporaryDirectory() as tmpdir:
            plugin_dir = Path(tmpdir)

            # Create a legacy plugin file
            plugin_file = plugin_dir / "legacy_plugin.py"
            plugin_code = '''
def show_legacy_test_plugin(ui, args):
    ui.info("Legacy plugin")
    return args
'''
            plugin_file.write_text(plugin_code)

            # Discover plugins
            registry.discover_plugins(plugin_dir)

            # Should have discovered the legacy plugin
            assert "legacy_test" in registry.get_plugin_names()

    def test_skip_base_and_registry_files(self, registry):
        """Test that base.py and registry.py are skipped during discovery."""
        with tempfile.TemporaryDirectory() as tmpdir:
            plugin_dir = Path(tmpdir)

            # Create files that should be skipped
            (plugin_dir / "base.py").write_text("# base file")
            (plugin_dir / "registry.py").write_text("# registry file")
            (plugin_dir / "_private.py").write_text("# private file")

            # Discover plugins
            registry.discover_plugins(plugin_dir)

            # Should not have discovered any plugins
            assert len(registry.get_plugin_names()) == 0

    def test_ast_based_discovery_with_import_error(self, registry):
        """Test AST-based discovery when imports fail."""
        with tempfile.TemporaryDirectory() as tmpdir:
            plugin_dir = Path(tmpdir)

            # Create a plugin with missing dependency
            plugin_file = plugin_dir / "plugin_with_missing_dep.py"
            plugin_code = '''
import nonexistent_module  # This will cause import error
from percell.plugins.base import PerCellPlugin, PluginMetadata

METADATA = PluginMetadata(
    name="failing_plugin",
    version="1.0.0",
    description="Plugin with missing dependency",
    author="Test"
)

class FailingPlugin(PerCellPlugin):
    def execute(self, ui, args):
        return args
'''
            plugin_file.write_text(plugin_code)

            # Discover plugins - should not raise exception
            # AST-based discovery should attempt to find the plugin
            registry.discover_plugins(plugin_dir)

            # AST discovery logs but doesn't register without successful import
            # This is expected behavior - plugin is discovered but not registered


class TestLegacyPluginAdapter:
    """Test the legacy plugin adapter."""

    def test_adapter_wraps_function(self):
        """Test that adapter properly wraps a legacy function."""
        def legacy_func(ui, args):
            ui.info("Called legacy function")
            args.test_value = 42
            return args

        metadata = PluginMetadata(
            name="wrapped_legacy",
            version="1.0.0",
            description="Wrapped legacy plugin",
            author="Test"
        )

        adapter = LegacyPluginAdapter(metadata, legacy_func)

        assert adapter.name == "wrapped_legacy"
        assert adapter.metadata == metadata

        # Test execution
        mock_ui = Mock()
        args = argparse.Namespace()
        result = adapter.execute(mock_ui, args)

        mock_ui.info.assert_called_once_with("Called legacy function")
        assert result.test_value == 42


class TestGlobalRegistry:
    """Test the global registry singleton."""

    def test_get_plugin_registry_returns_singleton(self):
        """Test that get_plugin_registry returns the same instance."""
        from percell.plugins.registry import get_plugin_registry

        registry1 = get_plugin_registry()
        registry2 = get_plugin_registry()

        assert registry1 is registry2

    def test_register_plugin_helper(self):
        """Test the register_plugin helper function."""
        from percell.plugins.registry import register_plugin, get_plugin_registry

        metadata = PluginMetadata(
            name="helper_test_plugin",
            version="1.0.0",
            description="Test plugin via helper",
            author="Test"
        )

        class HelperTestPlugin(PerCellPlugin):
            def execute(self, ui, args):
                return args

        plugin = HelperTestPlugin(metadata)
        register_plugin(plugin)

        # Should be registered in global registry
        registry = get_plugin_registry()
        assert "helper_test_plugin" in registry.get_plugin_names()
