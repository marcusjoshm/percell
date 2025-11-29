# Plugin Development Guide for PerCell

This guide explains how to create, convert, and integrate plugins with PerCell.

## Table of Contents

1. [Overview](#overview)
2. [Quick Start](#quick-start)
3. [Plugin Architecture](#plugin-architecture)
4. [Creating Plugins](#creating-plugins)
5. [Converting Existing Scripts](#converting-existing-scripts)
6. [Plugin Integration](#plugin-integration)
7. [Best Practices](#best-practices)

## Overview

PerCell's plugin system allows you to extend functionality seamlessly. Plugins can:

- Access PerCell's services (ImageJ, filesystem, image processing, Cellpose)
- Use the configuration service
- Integrate with the menu system automatically
- Validate requirements before execution
- Provide user-friendly interfaces

## Quick Start

### Generate a Plugin Template

```bash
python -m percell.plugins.template_generator MyPlugin --description "My awesome plugin" --author "Your Name"
```

This creates `percell/plugins/my_plugin.py` with a template you can fill in.

### Convert an Existing Script

```bash
python -m percell.plugins.converter my_script.py --name my_plugin
```

This analyzes your script and generates a plugin structure.

## Plugin Architecture

### Base Classes

All plugins inherit from `PerCellPlugin`:

```python
from percell.plugins.base import PerCellPlugin, PluginMetadata

METADATA = PluginMetadata(
    name="my_plugin",
    version="1.0.0",
    description="My plugin description",
    author="Your Name",
    requires_input_dir=True,
    requires_output_dir=True,
    requires_config=False,
    category="custom",
    menu_title="My Plugin",
    menu_description="Does something awesome"
)

class MyPlugin(PerCellPlugin):
    def __init__(self):
        super().__init__(METADATA)
    
    def execute(self, ui, args):
        # Your plugin logic here
        pass
```

### Plugin Metadata

The `PluginMetadata` class describes your plugin:

- **name**: Unique plugin identifier (lowercase, underscores)
- **version**: Plugin version (semantic versioning recommended)
- **description**: Brief description
- **author**: Author name
- **author_email**: Optional email
- **dependencies**: List of required Python packages
- **requires_config**: Whether plugin needs configuration service
- **requires_input_dir**: Whether plugin needs input directory
- **requires_output_dir**: Whether plugin needs output directory
- **category**: Plugin category (e.g., "custom", "analysis", "preprocessing")
- **menu_title**: Display name in menu
- **menu_description**: Menu item description

### Plugin Discovery

Plugins are automatically discovered from:

1. `percell/plugins/*.py` - Python files with plugin classes
2. `percell/plugins/*/plugin.json` - Plugins with metadata files

The registry looks for:
- Classes inheriting from `PerCellPlugin`
- Functions matching `show_*_plugin` pattern (legacy support)

## Creating Plugins

### Method 1: From Template

1. Generate template:
   ```bash
   python -m percell.plugins.template_generator MyPlugin
   ```

2. Edit the generated file:
   ```python
   # percell/plugins/my_plugin.py
   class MyPlugin(PerCellPlugin):
       def execute(self, ui, args):
           # Your logic here
           ui.info("Hello from my plugin!")
           return args
   ```

3. The plugin will appear in the Plugins menu automatically.

### Method 2: Manual Creation

Create a file in `percell/plugins/`:

```python
from percell.plugins.base import PerCellPlugin, PluginMetadata
from percell.ports.driving.user_interface_port import UserInterfacePort
import argparse

METADATA = PluginMetadata(
    name="my_plugin",
    version="1.0.0",
    description="My custom plugin",
    author="Your Name",
    requires_input_dir=True,
    requires_output_dir=True
)

class MyPlugin(PerCellPlugin):
    def __init__(self):
        super().__init__(METADATA)
    
    def execute(self, ui: UserInterfacePort, args: argparse.Namespace):
        input_dir = getattr(args, 'input', None)
        output_dir = getattr(args, 'output', None)
        
        # Your plugin logic
        ui.info(f"Processing {input_dir} -> {output_dir}")
        
        return args
```

### Accessing PerCell Services

Plugins have access to PerCell's services through the container:

```python
def execute(self, ui, args):
    # Configuration service
    config = self.config
    value = config.get("some.setting")
    
    # ImageJ adapter
    imagej = self.get_imagej()
    if imagej:
        imagej.run_macro("some_macro.ijm")
    
    # Filesystem adapter
    fs = self.get_filesystem()
    if fs:
        files = fs.list_files(Path("/some/path"))
    
    # Image processing adapter
    imgproc = self.get_image_processor()
    if imgproc:
        img = imgproc.load_image(Path("image.tif"))
    
    # Cellpose adapter
    cellpose = self.get_cellpose()
    if cellpose:
        # Use Cellpose
        pass
```

## Converting Existing Scripts

The converter tool analyzes your script and generates a plugin structure:

```bash
python -m percell.plugins.converter my_script.py --name my_plugin
```

### What the Converter Does

1. **Analyzes the script**:
   - Detects imports and dependencies
   - Finds main functions
   - Identifies file operations
   - Detects input/output directory usage

2. **Generates plugin structure**:
   - Creates plugin class
   - Generates metadata
   - Sets up validation
   - Creates menu integration

3. **Creates files**:
   - `percell/plugins/my_plugin.py` - Plugin class
   - `percell/plugins/my_plugin/plugin.json` - Metadata

### Manual Integration

After conversion, you'll need to manually integrate your script logic:

```python
def execute(self, ui, args):
    # Get directories
    input_dir = getattr(args, 'input', None) or Path(ui.prompt("Input: "))
    output_dir = getattr(args, 'output', None) or Path(ui.prompt("Output: "))
    
    # Copy your original script logic here
    # Replace print() with ui.info()
    # Replace input() with ui.prompt()
    # Replace file operations with adapter methods if needed
    
    return args
```

## Plugin Integration

### Automatic Registration

Plugins are automatically discovered and registered when PerCell starts. No manual registration needed!

### Menu Integration

Plugins appear in the Plugins menu automatically. The menu title and description come from your metadata.

### Validation

Plugins can validate requirements before execution:

```python
def validate(self, ui, args):
    if not super().validate(ui, args):
        return False
    
    # Custom validation
    if some_condition:
        ui.error("Custom validation failed")
        return False
    
    return True
```

## Best Practices

### 1. Error Handling

Always handle errors gracefully:

```python
def execute(self, ui, args):
    try:
        # Your logic
        pass
    except Exception as e:
        ui.error(f"Error: {e}")
        import traceback
        ui.error(traceback.format_exc())
        return args
```

### 2. User Feedback

Use the UI port for all user interaction:

```python
ui.info("Processing...")
ui.error("Something went wrong")
ui.prompt("Press Enter to continue...")
```

### 3. Directory Validation

Always validate directories:

```python
input_dir = Path(getattr(args, 'input', None) or ui.prompt("Input: "))
if not input_dir.exists():
    ui.error(f"Directory not found: {input_dir}")
    return args
```

### 4. Progress Reporting

For long operations, provide progress feedback:

```python
from tqdm import tqdm

files = list(input_dir.glob("*.tif"))
for file in tqdm(files, desc="Processing"):
    # Process file
    pass
```

### 5. Metadata

Keep metadata up to date:

```python
METADATA = PluginMetadata(
    name="my_plugin",
    version="1.2.0",  # Update version
    description="Updated description",
    dependencies=["numpy>=1.20", "pandas>=1.3"],  # List dependencies
    # ...
)
```

### 6. Testing

Test your plugin:

```python
# Test script
from percell.plugins.registry import get_plugin_registry
from percell.adapters.cli_user_interface_adapter import CLIUserInterfaceAdapter
import argparse

registry = get_plugin_registry()
plugin = registry.get_plugin("my_plugin")
ui = CLIUserInterfaceAdapter()
args = argparse.Namespace(input="/path/to/input", output="/path/to/output")

plugin.execute(ui, args)
```

## Examples

### Example 1: Simple Plugin

```python
from percell.plugins.base import PerCellPlugin, PluginMetadata
from percell.ports.driving.user_interface_port import UserInterfacePort
import argparse

METADATA = PluginMetadata(
    name="hello_world",
    version="1.0.0",
    description="A simple hello world plugin",
    author="Your Name"
)

class HelloWorldPlugin(PerCellPlugin):
    def __init__(self):
        super().__init__(METADATA)
    
    def execute(self, ui, args):
        ui.info("Hello, World!")
        ui.prompt("Press Enter to continue...")
        return args
```

### Example 2: File Processing Plugin

```python
from percell.plugins.base import PerCellPlugin, PluginMetadata
from percell.ports.driving.user_interface_port import UserInterfacePort
from pathlib import Path
import argparse

METADATA = PluginMetadata(
    name="file_counter",
    version="1.0.0",
    description="Counts files in a directory",
    author="Your Name",
    requires_input_dir=True
)

class FileCounterPlugin(PerCellPlugin):
    def __init__(self):
        super().__init__(METADATA)
    
    def execute(self, ui, args):
        input_dir = Path(getattr(args, 'input', None) or ui.prompt("Input directory: "))
        
        if not input_dir.exists():
            ui.error(f"Directory not found: {input_dir}")
            return args
        
        files = list(input_dir.rglob("*.tif"))
        ui.info(f"Found {len(files)} TIFF files")
        
        ui.prompt("Press Enter to continue...")
        return args
```

## Troubleshooting

### Plugin Not Appearing in Menu

1. Check plugin is in `percell/plugins/` directory
2. Verify class inherits from `PerCellPlugin`
3. Check for import errors in plugin file
4. Review logs for discovery errors

### Plugin Execution Errors

1. Check plugin validates correctly
2. Verify required directories exist
3. Ensure dependencies are installed
4. Review error messages in UI

### Service Access Issues

1. Verify container is set: `plugin.set_container(container)`
2. Check service exists in container
3. Handle None cases for optional services

## Further Reading

- [Plugin API Reference](api.md)
- [Architecture Documentation](Architecture.md)
- [Service Documentation](api.md)

