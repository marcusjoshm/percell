# PerCell Plugin System

## Overview

A comprehensive plugin system for PerCell that allows seamless integration of custom functionality. The system provides:

- **Automatic Discovery**: Plugins are automatically discovered and registered
- **Service Integration**: Access to all PerCell services (ImageJ, filesystem, image processing, Cellpose)
- **Easy Creation**: Template generator and script converter tools
- **Backward Compatible**: Legacy plugins continue to work

## Quick Start

### Generate a New Plugin

```bash
python -m percell.plugins.template_generator MyPlugin --description "My awesome plugin" --author "Your Name"
```

This creates `percell/plugins/my_plugin.py` with a complete template.

### Convert Existing Script

```bash
python -m percell.plugins.converter my_script.py --name my_plugin
```

This analyzes your script and generates a plugin structure.

## Architecture

### Components

1. **Base Plugin Interface** (`percell/plugins/base.py`)
   - `PerCellPlugin`: Base class for all plugins
   - `PluginMetadata`: Plugin metadata structure
   - `LegacyPluginAdapter`: Adapter for legacy plugin functions

2. **Plugin Registry** (`percell/plugins/registry.py`)
   - Automatic discovery from `percell/plugins/` directory
   - Supports both class-based and function-based plugins
   - Lazy instantiation for performance

3. **Menu Integration** (`percell/application/menu/menu_system.py`)
   - Automatic menu generation from discovered plugins
   - Dynamic plugin loading
   - Error handling and validation

### Plugin Discovery

Plugins are discovered from:
- `percell/plugins/*.py` - Python files with plugin classes
- `percell/plugins/*/plugin.json` - Plugins with metadata files

The registry looks for:
- Classes inheriting from `PerCellPlugin`
- Functions matching `show_*_plugin` pattern (legacy support)
- Classes with `METADATA` attribute

## Usage Examples

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

### Example 2: Using PerCell Services

```python
class MyPlugin(PerCellPlugin):
    def execute(self, ui, args):
        # Access configuration
        config = self.config
        value = config.get("some.setting")
        
        # Access ImageJ adapter
        imagej = self.get_imagej()
        if imagej:
            imagej.run_macro("my_macro.ijm")
        
        # Access filesystem adapter
        fs = self.get_filesystem()
        if fs:
            files = fs.list_files(Path("/some/path"))
        
        return args
```

## Tools

### Template Generator

```bash
python -m percell.plugins.template_generator PluginName [options]
```

Options:
- `--description`: Plugin description
- `--author`: Author name
- `--output`: Output directory (defaults to percell/plugins)

### Script Converter

```bash
python -m percell.plugins.converter script.py [options]
```

Options:
- `--name`: Plugin name (defaults to script filename)
- `--output`: Output directory (defaults to percell/plugins)

The converter:
- Analyzes script structure
- Detects dependencies
- Identifies input/output requirements
- Generates plugin skeleton
- Creates metadata file

## Plugin Metadata

```python
METADATA = PluginMetadata(
    name="my_plugin",              # Unique identifier
    version="1.0.0",                # Version string
    description="Plugin description",
    author="Your Name",
    author_email="email@example.com",  # Optional
    dependencies=["numpy", "pandas"],  # Optional
    requires_config=False,          # Need config service?
    requires_input_dir=True,         # Need input directory?
    requires_output_dir=True,        # Need output directory?
    category="custom",               # Plugin category
    menu_title="My Plugin",         # Menu display name
    menu_description="Does something"  # Menu description
)
```

## Integration Points

### Accessing Services

Plugins have access to:
- **Configuration Service**: `self.config`
- **ImageJ Adapter**: `self.get_imagej()`
- **Filesystem Adapter**: `self.get_filesystem()`
- **Image Processor**: `self.get_image_processor()`
- **Cellpose Adapter**: `self.get_cellpose()`

### Validation

Override `validate()` to add custom validation:

```python
def validate(self, ui, args):
    if not super().validate(ui, args):
        return False
    
    # Custom validation
    if some_condition:
        ui.error("Validation failed")
        return False
    
    return True
```

## File Structure

```
percell/plugins/
├── __init__.py                    # Module exports
├── base.py                        # Base plugin classes
├── registry.py                    # Plugin registry
├── converter.py                   # Script converter tool
├── template_generator.py          # Template generator
├── auto_image_preprocessing.py    # Existing plugin (legacy)
├── auto_image_preprocessing_plugin.py  # New architecture wrapper
└── my_plugin.py                   # Your plugins here
```

## Migration from Legacy Plugins

Legacy plugins (functions matching `show_*_plugin`) are automatically detected and wrapped. To migrate:

1. Create a plugin class inheriting from `PerCellPlugin`
2. Move logic to `execute()` method
3. Replace `print()` with `ui.info()`
4. Replace `input()` with `ui.prompt()`
5. Update metadata

## Best Practices

1. **Error Handling**: Always wrap logic in try/except
2. **User Feedback**: Use UI port for all interactions
3. **Validation**: Validate inputs before processing
4. **Progress**: Report progress for long operations
5. **Metadata**: Keep metadata up to date
6. **Testing**: Test plugins before distribution

## Documentation

- [Plugin Development Guide](docs/PLUGIN_DEVELOPMENT.md) - Comprehensive guide
- [Architecture Documentation](docs/Architecture.md) - System architecture
- [API Reference](docs/api.md) - API documentation

## Troubleshooting

### Plugin Not Appearing

1. Check plugin is in `percell/plugins/` directory
2. Verify class inherits from `PerCellPlugin`
3. Check for import errors
4. Review application logs

### Plugin Execution Errors

1. Verify validation passes
2. Check required directories exist
3. Ensure dependencies installed
4. Review error messages

## Contributing

When adding plugins:

1. Follow the plugin template structure
2. Include comprehensive metadata
3. Add error handling
4. Test thoroughly
5. Update documentation

## Status

✅ Plugin base architecture  
✅ Plugin registry and discovery  
✅ Menu integration  
✅ Template generator  
✅ Script converter  
✅ Legacy plugin support  
✅ Service integration  
✅ Documentation  

The plugin system is ready for use!

