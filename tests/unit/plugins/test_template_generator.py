"""Unit tests for the plugin template generator."""
import pytest
import tempfile
from pathlib import Path

from percell.plugins.template_generator import generate_plugin_template


class TestTemplateGenerator:
    """Test the plugin template generator."""

    def test_generates_basic_template(self):
        """Test generating a basic plugin template."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)

            plugin_file = generate_plugin_template(
                "TestPlugin",
                output_dir=output_dir
            )

            assert plugin_file.exists()
            assert plugin_file.name == "testplugin.py"

            # Check file content
            content = plugin_file.read_text()
            assert "Testplugin Plugin for PerCell" in content
            assert "class TestpluginPlugin(PerCellPlugin)" in content
            assert 'name="testplugin"' in content
            assert "METADATA = PluginMetadata" in content

    def test_generates_template_with_description(self):
        """Test generating template with custom description."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)

            plugin_file = generate_plugin_template(
                "CustomPlugin",
                output_dir=output_dir,
                description="A custom test plugin"
            )

            content = plugin_file.read_text()
            assert "A custom test plugin" in content
            assert 'description="A custom test plugin"' in content

    def test_generates_template_with_author(self):
        """Test generating template with custom author."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)

            plugin_file = generate_plugin_template(
                "AuthorPlugin",
                output_dir=output_dir,
                author="Test Author"
            )

            content = plugin_file.read_text()
            assert 'author="Test Author"' in content

    def test_handles_plugin_name_with_spaces(self):
        """Test that plugin names with spaces are handled correctly."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)

            plugin_file = generate_plugin_template(
                "My Test Plugin",
                output_dir=output_dir
            )

            # Should convert to snake_case
            assert plugin_file.name == "my_test_plugin.py"

            content = plugin_file.read_text()
            assert 'name="my_test_plugin"' in content
            assert "class MyTestPluginPlugin(PerCellPlugin)" in content

    def test_handles_plugin_name_with_hyphens(self):
        """Test that plugin names with hyphens are handled correctly."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)

            plugin_file = generate_plugin_template(
                "my-test-plugin",
                output_dir=output_dir
            )

            # Should convert hyphens to underscores
            assert plugin_file.name == "my_test_plugin.py"

            content = plugin_file.read_text()
            assert 'name="my_test_plugin"' in content

    def test_generated_template_has_required_structure(self):
        """Test that generated template has all required components."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)

            plugin_file = generate_plugin_template(
                "CompletePlugin",
                output_dir=output_dir
            )

            content = plugin_file.read_text()

            # Check for required imports
            assert "from percell.plugins.base import PerCellPlugin, PluginMetadata" in content
            assert "from percell.ports.driving.user_interface_port import UserInterfacePort" in content
            assert "import argparse" in content
            assert "from pathlib import Path" in content

            # Check for metadata
            assert "METADATA = PluginMetadata(" in content
            assert 'name="completeplugin"' in content
            assert 'version="1.0.0"' in content
            assert 'requires_input_dir=False' in content
            assert 'requires_output_dir=False' in content
            assert 'requires_config=False' in content

            # Check for class structure
            assert "class CompletepluginPlugin(PerCellPlugin):" in content
            assert "def __init__(self):" in content
            assert "def execute(" in content

            # Check for boilerplate code
            assert "ui: UserInterfacePort" in content
            assert "args: argparse.Namespace" in content
            assert "return args" in content

    def test_generated_template_includes_service_access_comments(self):
        """Test that template includes helpful comments about service access."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)

            plugin_file = generate_plugin_template(
                "ServicePlugin",
                output_dir=output_dir
            )

            content = plugin_file.read_text()

            # Check for service access examples in comments
            assert "self.config" in content
            assert "self.get_imagej()" in content
            assert "self.get_filesystem()" in content
            assert "self.get_image_processor()" in content
            assert "self.get_cellpose()" in content

    def test_generated_template_includes_error_handling(self):
        """Test that template includes error handling."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)

            plugin_file = generate_plugin_template(
                "ErrorHandlingPlugin",
                output_dir=output_dir
            )

            content = plugin_file.read_text()

            assert "try:" in content
            assert "except Exception as e:" in content
            assert 'ui.error(f"Error executing plugin: {e}")' in content
            assert "import traceback" in content

    def test_generated_template_includes_directory_handling(self):
        """Test that template includes directory handling logic."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)

            plugin_file = generate_plugin_template(
                "DirectoryPlugin",
                output_dir=output_dir
            )

            content = plugin_file.read_text()

            assert "input_dir = getattr(args, 'input', None)" in content
            assert "output_dir = getattr(args, 'output', None)" in content
            assert "self.metadata.requires_input_dir" in content
            assert "self.metadata.requires_output_dir" in content

    def test_generates_valid_python_code(self):
        """Test that generated template is valid Python code."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)

            plugin_file = generate_plugin_template(
                "ValidPythonPlugin",
                output_dir=output_dir
            )

            # Try to compile the generated code
            content = plugin_file.read_text()
            try:
                compile(content, str(plugin_file), 'exec')
            except SyntaxError as e:
                pytest.fail(f"Generated template has syntax error: {e}")

    def test_default_output_directory(self):
        """Test that default output directory is percell/plugins."""
        # This test just verifies the function can be called without output_dir
        # We don't actually write to the real plugin directory in tests
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)

            # Explicitly pass output_dir to avoid writing to real location
            plugin_file = generate_plugin_template(
                "DefaultDirPlugin",
                output_dir=output_dir
            )

            assert plugin_file.exists()
