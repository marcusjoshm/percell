# PerCell Plugin System Guide

Complete guide to developing and using PerCell plugins.

## Table of Contents

1. [Quick Start](#quick-start)
2. [Plugin Architecture](#plugin-architecture)
3. [Creating Plugins](#creating-plugins)
4. [Plugin Discovery](#plugin-discovery)
5. [Converting Scripts](#converting-scripts)
6. [Best Practices](#best-practices)
7. [API Reference](#api-reference)

---

## Quick Start

### Using Existing Plugins

1. Open PerCell application
2. Navigate to "Plugins Menu"
3. Select a plugin by number
4. Follow the prompts

### Creating a New Plugin

**Option 1: Use the Template Generator**

```bash
python -m percell.plugins.template_generator MyPlugin \
    --description "My awesome plugin" \
    --author "Your Name"
```

This creates `percell/plugins/my_plugin.py` with a complete template.

**Option 2: Convert an Existing Script**

```bash
python -m percell.plugins.converter my_script.py --name my_plugin
```

This analyzes your script and generates a plugin structure.

---

## Plugin Architecture

### Core Components

1. **PerCellPlugin (Base Class)** - All plugins inherit from this
2. **PluginMetadata** - Describes plugin properties
3. **PluginRegistry** - Discovers and manages plugins
4. **Menu Integration** - Automatic menu generation

### Plugin Lifecycle

```
1. Discovery  → Registry scans percell/plugins/
2. Registration → Plugin classes are registered
3. Instantiation → Lazy - only when needed
4. Validation → Requirements checked before execution
5. Execution → Plugin logic runs
```

### Architecture Diagram

```
┌─────────────────────────────────────┐
│      Plugin Registry                 │
│  - Auto-discovery                    │
│  - Lazy instantiation                │
│  - Metadata management               │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│      PerCellPlugin (Base)            │
│  - Service access (config, adapters) │
│  - Validation logic                  │
│  - Abstract execute() method         │
└──────────────┬──────────────────────┘
               │
       ┌───────┴───────┐
       │               │
       ▼               ▼
┌─────────────┐  ┌──────────────┐
│   Custom    │  │   Legacy     │
│   Plugins   │  │   Adapter    │
└─────────────┘  └──────────────┘
```

---

## Creating Plugins

### Basic Plugin Structure

```python
from percell.plugins.base import PerCellPlugin, PluginMetadata
from percell.ports.driving.user_interface_port import UserInterfacePort
import argparse

# Define metadata
METADATA = PluginMetadata(
    name="my_plugin",
    version="1.0.0",
    description="My plugin description",
    author="Your Name",
    requires_input_dir=True,
    requires_output_dir=False,
    requires_config=False,
    category="custom"
)

# Create plugin class
class MyPlugin(PerCellPlugin):
    def __init__(self):
        super().__init__(METADATA)

    def execute(self, ui: UserInterfacePort, args: argparse.Namespace):
        """Execute plugin logic."""
        ui.info("Hello from my plugin!")

        # Access services
        config = self.config
        imagej = self.get_imagej()

        # Do work...

        ui.prompt("Press Enter to continue...")
        return args
```

### Plugin Metadata Fields

| Field | Type | Description |
|-------|------|-------------|
| `name` | str | Unique plugin identifier (snake_case) |
| `version` | str | Version string (semantic versioning) |
| `description` | str | Brief description |
| `author` | str | Author name |
| `author_email` | str (optional) | Author email |
| `dependencies` | list (optional) | Required Python packages |
| `requires_config` | bool | Need configuration service? |
| `requires_input_dir` | bool | Need input directory? |
| `requires_output_dir` | bool | Need output directory? |
| `category` | str | Plugin category |
| `menu_title` | str (optional) | Menu display name |
| `menu_description` | str (optional) | Menu description |

### Accessing PerCell Services

```python
class MyPlugin(PerCellPlugin):
    def execute(self, ui, args):
        # Configuration service
        config = self.config
        setting = config.get("some.setting")

        # ImageJ adapter
        imagej = self.get_imagej()
        if imagej:
            imagej.run_macro("my_macro.ijm")

        # Filesystem adapter
        fs = self.get_filesystem()
        if fs:
            files = fs.list_files(Path("/some/path"))

        # Image processor
        imgproc = self.get_image_processor()

        # Cellpose adapter
        cellpose = self.get_cellpose()

        return args
```

### Custom Validation

```python
class MyPlugin(PerCellPlugin):
    def validate(self, ui, args):
        # Call parent validation first
        if not super().validate(ui, args):
            return False

        # Add custom validation
        if not hasattr(args, 'required_field'):
            ui.error("Missing required field")
            return False

        return True
```

---

## Plugin Discovery

### How Discovery Works

The plugin registry automatically scans `percell/plugins/` for plugins:

1. **Python Files**: Scans `*.py` files for:
   - Classes inheriting from `PerCellPlugin`
   - Functions matching `show_*_plugin` pattern (legacy)

2. **Metadata Files**: Reads `*/plugin.json` for plugin metadata

3. **AST Fallback**: If imports fail, uses AST parsing to still discover plugins

### Discovery Process

```
Start
  │
  ▼
Scan percell/plugins/*.py
  │
  ├─► Skip: base.py, registry.py, _*.py
  │
  ├─► Try to import module
  │   │
  │   ├─► Success → Inspect for plugin classes
  │   │              └─► Register discovered plugins
  │   │
  │   └─► Fail → AST-based discovery
  │                └─► Log plugin class (can't instantiate)
  │
  ▼
Scan percell/plugins/*/plugin.json
  │
  └─► Load metadata and corresponding .py file
      └─► Register plugin class
```

### Plugin File Locations

```
percell/plugins/
├── __init__.py
├── base.py                    # Base classes (skipped)
├── registry.py                # Registry (skipped)
├── my_plugin.py               # ✅ Discovered
├── another_plugin.py          # ✅ Discovered
├── _helper.py                 # ❌ Skipped (starts with _)
└── complex_plugin/
    ├── __init__.py
    ├── plugin.json            # ✅ Metadata file
    └── complex_plugin.py      # ✅ Discovered
```

### Lazy Instantiation

Plugins are only instantiated when needed:

```python
# Registration (startup) - No instantiation
registry.register_class(MyPlugin, metadata)

# Later, when user selects plugin
plugin = registry.get_plugin("my_plugin")  # ← Instantiated here
```

This improves startup performance and reduces memory usage.

---

## Converting Scripts

### Using the Converter

```bash
python -m percell.plugins.converter script.py [--name PLUGIN_NAME] [--output DIR]
```

### What the Converter Does

1. **Analyzes Script Structure**
   - Detects imports and dependencies
   - Identifies main functions
   - Recognizes file operation patterns
   - Infers directory requirements

2. **Generates Plugin Code**
   - Creates plugin class skeleton
   - Wraps original logic
   - Adds UI integration points
   - Includes error handling

3. **Creates Metadata**
   - Infers requirements
   - Lists dependencies
   - Generates `plugin.json`

### Conversion Example

**Before (script.py):**
```python
import numpy as np

def analyze_data(input_dir, output_dir):
    print(f"Processing {input_dir}")
    # ... analysis logic ...
    print("Done!")

if __name__ == "__main__":
    analyze_data("/path/to/input", "/path/to/output")
```

**After (data_analyzer_plugin.py):**
```python
from percell.plugins.base import PerCellPlugin, PluginMetadata

METADATA = PluginMetadata(
    name="data_analyzer",
    version="1.0.0",
    description="Auto-generated from script.py",
    author="Auto-generated",
    requires_input_dir=True,
    requires_output_dir=True,
    dependencies=["numpy"]
)

class DataAnalyzerPlugin(PerCellPlugin):
    def execute(self, ui, args):
        try:
            import numpy as np  # Lazy import

            # Get directories
            input_dir = getattr(args, 'input', None) or ui.prompt("Input dir: ")
            output_dir = getattr(args, 'output', None) or ui.prompt("Output dir: ")

            # Original logic
            ui.info(f"Processing {input_dir}")
            # ... analysis logic ...
            ui.info("Done!")

            return args
        except Exception as e:
            ui.error(f"Error: {e}")
            return args
```

### Manual Integration Tips

After conversion, you may need to:

1. Replace `print()` with `ui.info()`
2. Replace `input()` with `ui.prompt()`
3. Add progress reporting for long operations
4. Integrate with PerCell services (ImageJ, filesystem, etc.)
5. Test thoroughly

---

## Best Practices

### 1. Error Handling

Always wrap plugin logic in try/except:

```python
def execute(self, ui, args):
    try:
        # Your logic here
        pass
    except Exception as e:
        ui.error(f"Error: {e}")
        import traceback
        ui.error(traceback.format_exc())
        ui.prompt("Press Enter to continue...")
        return args
```

### 2. User Feedback

Use the UI port for all user interaction:

```python
ui.info("Processing...")           # Information
ui.error("Error occurred")         # Errors
response = ui.prompt("Continue?")  # User input
```

### 3. Validation

Validate inputs before processing:

```python
def validate(self, ui, args):
    if not super().validate(ui, args):
        return False

    # Custom validation
    input_dir = Path(getattr(args, 'input', ''))
    if not input_dir.exists():
        ui.error(f"Directory not found: {input_dir}")
        return False

    return True
```

### 4. Progress Reporting

For long operations, report progress:

```python
def execute(self, ui, args):
    files = list(input_dir.glob("*.tif"))
    total = len(files)

    for i, file in enumerate(files, 1):
        ui.info(f"Processing {i}/{total}: {file.name}")
        # Process file...
```

### 5. Lazy Imports

Import heavy dependencies only when needed:

```python
def execute(self, ui, args):
    try:
        import numpy as np
        import pandas as pd
    except ImportError as e:
        ui.error(f"Missing dependency: {e}")
        ui.error("Run: pip install numpy pandas")
        return args

    # Use numpy and pandas...
```

### 6. Testing

Test your plugin before distribution:

```python
# tests/unit/plugins/test_my_plugin.py
def test_my_plugin_execution():
    plugin = MyPlugin()
    mock_ui = Mock()
    args = argparse.Namespace(input="/test/path")

    result = plugin.execute(mock_ui, args)

    assert result is not None
    mock_ui.info.assert_called()
```

---

## API Reference

### PerCellPlugin

```python
class PerCellPlugin(ABC):
    """Base class for all PerCell plugins."""

    def __init__(self, metadata: PluginMetadata):
        """Initialize with metadata."""

    @abstractmethod
    def execute(self, ui: UserInterfacePort, args: argparse.Namespace) -> Optional[argparse.Namespace]:
        """Execute plugin logic. Must be implemented by subclasses."""

    def validate(self, ui: UserInterfacePort, args: argparse.Namespace) -> bool:
        """Validate plugin requirements. Override to add custom validation."""

    def set_config(self, config: Any) -> None:
        """Set configuration service."""

    def set_container(self, container: Any) -> None:
        """Set dependency injection container."""

    # Service accessors
    def get_imagej(self) -> Optional[Any]:
        """Get ImageJ adapter."""

    def get_filesystem(self) -> Optional[Any]:
        """Get filesystem adapter."""

    def get_image_processor(self) -> Optional[Any]:
        """Get image processing adapter."""

    def get_cellpose(self) -> Optional[Any]:
        """Get Cellpose adapter."""

    # Menu helpers
    def get_menu_title(self) -> str:
        """Get display title for menu."""

    def get_menu_description(self) -> str:
        """Get description for menu."""
```

### PluginMetadata

```python
@dataclass
class PluginMetadata:
    """Plugin metadata descriptor."""

    name: str
    version: str
    description: str
    author: str
    author_email: Optional[str] = None
    dependencies: List[str] = field(default_factory=list)
    requires_config: bool = False
    requires_input_dir: bool = False
    requires_output_dir: bool = False
    category: str = "general"
    menu_title: Optional[str] = None
    menu_description: Optional[str] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> PluginMetadata:
        """Create from dictionary."""

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
```

### PluginRegistry

```python
class PluginRegistry:
    """Registry for managing plugins."""

    def register(self, plugin: PerCellPlugin, metadata: Optional[PluginMetadata] = None) -> None:
        """Register a plugin instance."""

    def register_class(self, plugin_class: Type[PerCellPlugin], metadata: Optional[PluginMetadata] = None) -> None:
        """Register a plugin class (lazy instantiation)."""

    def register_legacy_function(self, function: Callable, metadata: PluginMetadata) -> None:
        """Register a legacy plugin function."""

    def get_plugin(self, name: str) -> Optional[PerCellPlugin]:
        """Get plugin instance by name."""

    def get_all_plugins(self) -> List[PerCellPlugin]:
        """Get all registered plugins."""

    def get_plugin_names(self) -> List[str]:
        """Get names of all registered plugins."""

    def get_metadata(self, name: str) -> Optional[PluginMetadata]:
        """Get metadata for a plugin."""

    def discover_plugins(self, plugin_dir: Optional[Path] = None) -> None:
        """Discover and register plugins from directory."""
```

### Global Functions

```python
def get_plugin_registry() -> PluginRegistry:
    """Get the global plugin registry instance."""

def register_plugin(plugin: PerCellPlugin) -> None:
    """Register a plugin with the global registry."""
```

---

## Troubleshooting

### Plugin Not Appearing in Menu

1. Check plugin is in `percell/plugins/` directory
2. Verify class inherits from `PerCellPlugin`
3. Check for import errors in logs
4. Ensure `METADATA` is defined

### Plugin Execution Errors

1. Check validation passes
2. Verify required directories exist
3. Ensure dependencies are installed
4. Review error messages and stack traces

### Import Errors

If your plugin has missing dependencies:

```bash
pip install package_name
```

Or add lazy imports in your plugin.

---

## Example Plugins

See the following examples in `percell/plugins/`:

- `auto_image_preprocessing_plugin.py` - Legacy wrapper example
- `intensity_analysis_plugin.py` - Full conversion example

---

## Additional Resources

- **Quick Reference**: See `PLUGIN_SYSTEM_README.md`
- **Feature Summary**: See `FEATURE_SUMMARY.md`
- **Conversion Guide**: See `CONVERSION_SUMMARY.md`

---

*For questions or issues, please file a GitHub issue.*
