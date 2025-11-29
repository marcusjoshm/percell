# How Automatic Plugin Discovery Works

## Overview

PerCell's plugin system uses **lazy initialization** with **automatic discovery** - plugins are discovered and registered the first time the plugin registry is accessed, without any manual registration required.

## Discovery Flow

```
┌─────────────────────────────────────────────────────────────┐
│  Application Starts                                          │
│  (percell/main/main.py)                                     │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│  User Opens Plugins Menu                                    │
│  (menu_system.py: create_plugins_menu)                      │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│  get_plugin_registry() called                               │
│  (First time access - lazy initialization)                  │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│  PluginRegistry() created                                   │
│  - Empty dictionaries for plugins, classes, metadata         │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│  discover_plugins() called                                  │
│  - Scans percell/plugins/ directory                        │
└────────────────────┬────────────────────────────────────────┘
                     │
        ┌────────────┴────────────┐
        │                         │
        ▼                         ▼
┌───────────────┐        ┌──────────────────┐
│ Scan .py files│        │ Scan plugin.json │
│ in directory  │        │ files            │
└───────┬───────┘        └────────┬─────────┘
        │                         │
        ▼                         ▼
┌─────────────────────────────────────────────────────────────┐
│  For each .py file:                                          │
│  1. Skip: __init__.py, base.py, registry.py                │
│  2. Load module dynamically                                  │
│  3. Inspect module contents                                   │
└────────────────────┬────────────────────────────────────────┘
                     │
        ┌────────────┴────────────┐
        │                         │
        ▼                         ▼
┌──────────────────┐      ┌──────────────────────┐
│ Find Plugin      │      │ Find Legacy          │
│ Classes          │      │ Functions            │
│                  │      │                      │
│ - Inherit from   │      │ - Pattern:           │
│   PerCellPlugin  │      │   show_*_plugin      │
│ - Has METADATA   │      │ - Wrapped in adapter │
│   attribute      │      │                      │
└──────┬───────────┘      └──────────┬───────────┘
       │                              │
       └──────────────┬───────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────┐
│  Register Plugin                                              │
│  - Store in _plugin_classes (lazy) or _plugins (instantiated)│
│  - Store metadata in _metadata                               │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│  Return Registry                                             │
│  - Menu system gets list of plugins                          │
│  - Creates menu items dynamically                            │
└─────────────────────────────────────────────────────────────┘
```

## Step-by-Step Process

### 1. **Lazy Initialization**

The registry is created only when first accessed:

```python
# In registry.py
_registry: Optional[PluginRegistry] = None

def get_plugin_registry() -> PluginRegistry:
    global _registry
    if _registry is None:
        _registry = PluginRegistry()
        _registry.discover_plugins()  # Discovery happens here!
    return _registry
```

**When is this called?**
- When the Plugins menu is created (first time user opens it)
- Not at application startup (lazy loading)

### 2. **Directory Scanning**

The discovery process scans `percell/plugins/`:

```python
def discover_plugins(self, plugin_dir: Optional[Path] = None) -> None:
    if plugin_dir is None:
        plugin_dir = Path(__file__).parent  # percell/plugins/
    
    # Find all Python files
    for plugin_file in plugin_dir.glob("*.py"):
        if plugin_file.name.startswith("_") or plugin_file.name in ("base.py", "registry.py"):
            continue  # Skip internal files
        self._load_plugin_from_file(plugin_file)
    
    # Find plugin.json files
    for plugin_json in plugin_dir.glob("*/plugin.json"):
        self._load_plugin_from_json(plugin_json)
```

**What files are scanned?**
- ✅ `my_plugin.py` - Regular plugin files
- ✅ `auto_image_preprocessing.py` - Existing plugins
- ❌ `__init__.py` - Module initialization (skipped)
- ❌ `base.py` - Base classes (skipped)
- ❌ `registry.py` - Registry itself (skipped)

### 3. **Dynamic Module Loading**

Each Python file is loaded dynamically:

```python
def _load_plugin_from_file(self, plugin_file: Path) -> None:
    # Create module spec from file
    spec = importlib.util.spec_from_file_location(
        plugin_file.stem,  # Module name (filename without .py)
        plugin_file         # Full path
    )
    
    # Load the module
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    
    # Now inspect the module contents...
```

**Why dynamic loading?**
- Plugins can be added without modifying core code
- No need to import all plugins at startup
- Errors in one plugin don't break others

### 4. **Plugin Detection**

The system looks for three types of plugins:

#### A. **Class-Based Plugins** (New Architecture)

```python
# Look for classes that inherit from PerCellPlugin
for name, obj in inspect.getmembers(module):
    if (inspect.isclass(obj) and 
        issubclass(obj, PerCellPlugin) and 
        obj is not PerCellPlugin):  # Not the base class itself
        
        if hasattr(obj, 'METADATA'):
            # Class has METADATA attribute
            self.register_class(obj, obj.METADATA)
        else:
            # Try to instantiate to get metadata
            temp_metadata = PluginMetadata(...)
            instance = obj(temp_metadata)
            self.register(instance)
```

**Example:**
```python
# my_plugin.py
METADATA = PluginMetadata(name="my_plugin", ...)

class MyPlugin(PerCellPlugin):
    def __init__(self, metadata=None):
        super().__init__(metadata or METADATA)
```

#### B. **Legacy Function-Based Plugins**

```python
# Look for functions matching show_*_plugin pattern
for name, obj in inspect.getmembers(module):
    if (inspect.isfunction(obj) and 
        name.startswith("show_") and 
        name.endswith("_plugin")):
        
        plugin_name = name.replace("show_", "").replace("_plugin", "")
        metadata = PluginMetadata(name=plugin_name, ...)
        self.register_legacy_function(obj, metadata)
```

**Example:**
```python
# auto_image_preprocessing.py
def show_auto_image_preprocessing_plugin(ui, args):
    # Legacy plugin function
    pass
```

#### C. **JSON Metadata Plugins**

```python
# Find plugin.json files
for plugin_json in plugin_dir.glob("*/plugin.json"):
    with open(plugin_json, 'r') as f:
        data = json.load(f)
    metadata = PluginMetadata.from_dict(data)
    
    # Load corresponding .py file
    plugin_file = plugin_dir / f"{metadata.name}.py"
    # ... load and register
```

**Example:**
```
my_plugin/
├── plugin.json  # Metadata
└── my_plugin.py # Implementation
```

### 5. **Registration**

Plugins are registered in the registry:

```python
def register_class(self, plugin_class, metadata):
    self._plugin_classes[metadata.name] = plugin_class  # Lazy instantiation
    self._metadata[metadata.name] = metadata

def register(self, plugin):
    self._plugins[metadata.name] = plugin  # Instantiated
    self._metadata[metadata.name] = metadata
```

**Lazy vs Eager:**
- **Class registration**: Plugin class stored, instantiated when needed
- **Instance registration**: Plugin already instantiated

### 6. **Menu Integration**

When the menu is created, it queries the registry:

```python
def create_plugins_menu(ui):
    registry = get_plugin_registry()  # Triggers discovery if first time
    plugin_names = registry.get_plugin_names()
    
    items = []
    for plugin_name in sorted(plugin_names):
        plugin = registry.get_plugin(plugin_name)  # Lazy instantiation
        items.append(MenuItem(...))
```

## Key Features

### 1. **No Manual Registration**

Plugins are discovered automatically - just add a file to `percell/plugins/`:

```python
# percell/plugins/my_new_plugin.py
class MyNewPlugin(PerCellPlugin):
    # Automatically discovered!
    pass
```

### 2. **Error Isolation**

If one plugin fails to load, others still work:

```python
try:
    self._load_plugin_from_file(plugin_file)
except Exception as e:
    logger.warning(f"Failed to load plugin from {plugin_file}: {e}")
    # Continue with other plugins
```

### 3. **Lazy Instantiation**

Plugins are instantiated only when needed:

```python
def get_plugin(self, name: str):
    # Check if already instantiated
    if name in self._plugins:
        return self._plugins[name]
    
    # Instantiate from class
    if name in self._plugin_classes:
        plugin_class = self._plugin_classes[name]
        metadata = self._metadata[name]
        plugin = plugin_class(metadata)  # Created here!
        self._plugins[name] = plugin
        return plugin
```

### 4. **Multiple Discovery Methods**

The system supports:
- ✅ Class-based plugins (new architecture)
- ✅ Function-based plugins (legacy support)
- ✅ JSON metadata files (structured plugins)

## Example Discovery Session

Let's trace what happens when you have these files:

```
percell/plugins/
├── __init__.py                    # Skipped
├── base.py                        # Skipped
├── registry.py                    # Skipped
├── auto_image_preprocessing.py    # Scanned
├── my_plugin.py                   # Scanned
└── advanced_plugin/
    ├── plugin.json                # Scanned
    └── advanced_plugin.py         # Loaded via JSON
```

**Discovery log:**
```
1. Scanning percell/plugins/*.py
   - Found: auto_image_preprocessing.py
     → Inspecting module...
     → Found function: show_auto_image_preprocessing_plugin
     → Registered as: auto_image_preprocessing (legacy)
   
   - Found: my_plugin.py
     → Inspecting module...
     → Found class: MyPlugin (inherits from PerCellPlugin)
     → Has METADATA attribute
     → Registered as: my_plugin (class)

2. Scanning percell/plugins/*/plugin.json
   - Found: advanced_plugin/plugin.json
     → Loading metadata...
     → Loading advanced_plugin.py
     → Found class: AdvancedPlugin
     → Registered as: advanced_plugin (class)

3. Total plugins discovered: 3
```

## Performance Considerations

### First Access
- **Cost**: Scans directory, loads modules, inspects classes
- **When**: First time Plugins menu is opened
- **Typical time**: < 100ms for 10 plugins

### Subsequent Access
- **Cost**: Just dictionary lookup
- **When**: Every time menu is created
- **Typical time**: < 1ms

### Plugin Instantiation
- **Cost**: Creating plugin instance, setting up services
- **When**: Plugin is actually executed
- **Typical time**: < 10ms per plugin

## Debugging Discovery

To see what's being discovered:

```python
from percell.plugins.registry import get_plugin_registry
import logging

logging.basicConfig(level=logging.INFO)
registry = get_plugin_registry()
print(f"Plugins: {registry.get_plugin_names()}")
```

This will show:
- Discovery log messages
- Registration confirmations
- Any warnings for failed plugins

## Summary

Automatic discovery works by:

1. **Lazy initialization** - Registry created on first access
2. **Directory scanning** - Finds all `.py` files and `plugin.json` files
3. **Dynamic loading** - Loads modules without importing them
4. **Inspection** - Uses Python's `inspect` module to find plugin classes/functions
5. **Registration** - Stores plugins for later use
6. **Menu integration** - Automatically creates menu items

**No configuration needed** - just add your plugin file and it's discovered automatically!

