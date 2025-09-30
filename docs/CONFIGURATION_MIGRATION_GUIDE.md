# Configuration Migration Guide

**Migrating from `application.config_api.Config` to `domain.services.configuration_service.ConfigurationService`**

---

## Table of Contents

1. [Overview](#overview)
2. [Why Migrate?](#why-migrate)
3. [API Comparison](#api-comparison)
4. [Migration Steps](#migration-steps)
5. [Common Patterns](#common-patterns)
6. [Breaking Changes](#breaking-changes)
7. [Troubleshooting](#troubleshooting)
8. [Deprecation Timeline](#deprecation-timeline)

---

## Overview

The Percell project is consolidating configuration management into a single, well-architected service in the domain layer. This migration guide helps you transition from the legacy `Config` class to the new `ConfigurationService`.

### Current State (Before Migration)
- ❌ `application/config_api.Config` - Legacy, will be deprecated
- ❌ `application/configuration_manager.ConfigurationManager` - Duplicate, removed
- ✅ `domain/services/configuration_service.ConfigurationService` - **Use this!**
- 🔄 `application/configuration_service_compat.py` - Temporary compatibility layer

### Target State (After Migration)
- ✅ `domain/services/configuration_service.ConfigurationService` - Single source of truth
- 🔄 `application/configuration_service_compat.py` - Compatibility shims (temporary)

---

## Why Migrate?

### Benefits of `ConfigurationService`

1. **Better Architecture** ✅
   - Lives in domain layer (proper hexagonal architecture)
   - Separates business logic from infrastructure
   - Follows single responsibility principle

2. **Improved Error Handling** ✅
   - Uses domain exceptions (`ConfigurationError`)
   - Atomic file operations (prevents corruption)
   - Comprehensive logging

3. **Enhanced Features** ✅
   - Consistent dot-notation support
   - Better type safety with dataclasses
   - Path resolution helpers (`get_resolved_path`)
   - Defensive copying (`to_dict()`)

4. **Single Implementation** ✅
   - Eliminates duplicate code
   - Easier to maintain and test
   - Consistent behavior across codebase

---

## API Comparison

### Initialization

**Old Way** (`Config`):
```python
from percell.application.config_api import Config, ConfigError

# Constructor loads immediately, raises if not found
config = Config("percell/config/config.json")
```

**New Way** (`ConfigurationService`):
```python
from percell.domain.services.configuration_service import (
    ConfigurationService,
    create_configuration_service
)
from percell.domain.exceptions import ConfigurationError

# Option 1: Factory function (recommended)
config = create_configuration_service(
    "percell/config/config.json",
    create_if_missing=True  # Creates empty config if not found
)

# Option 2: Direct instantiation
config = ConfigurationService(path=Path("percell/config/config.json"))
config.load(create_if_missing=True)
```

### Core Methods - Side-by-Side

| Operation | Old (`Config`) | New (`ConfigurationService`) | Notes |
|-----------|----------------|------------------------------|-------|
| **Get value** | `config.get("key", default)` | `config.get("key", default)` | ✅ Same |
| **Get nested** | `config.get("paths.imagej")` | `config.get("paths.imagej")` | ✅ Same |
| **Set value** | `config.set("key", value)` | `config.set("key", value)` | ✅ Same |
| **Set nested** | `config.set("paths.imagej", value)` | `config.set("paths.imagej", value)` | ✅ Same |
| **Load** | `config.load()` | `config.load(create_if_missing=True)` | ⚠️ New parameter |
| **Save** | `config.save()` | `config.save()` | ✅ Same (but atomic) |
| **Update bulk** | `config.update(dict)` | `config.update(dict)` | ✅ Same |
| **To dict** | `config.to_dict()` | `config.to_dict()` | ✅ Same (but defensive copy) |
| **Check exists** | N/A | `config.has("key")` | ✨ New feature |
| **Delete key** | N/A | `config.delete("key")` | ✨ New feature |
| **Clear all** | N/A | `config.clear()` | ✨ New feature |
| **Resolve path** | N/A | `config.get_resolved_path("key", root)` | ✨ New feature |

### Exception Handling

**Old Way**:
```python
from percell.application.config_api import ConfigError

try:
    config = Config("config.json")
except ConfigError as e:
    print(f"Config error: {e}")
```

**New Way**:
```python
from percell.domain.exceptions import ConfigurationError

try:
    config = create_configuration_service("config.json", create_if_missing=False)
except ConfigurationError as e:
    print(f"Config error: {e}")
```

### Custom Methods Migration

The old `Config` class has several custom helper methods that need migration:

#### `validate()` → Use explicit validation

**Old Way**:
```python
config = Config("config.json")
config.validate()  # Checks for required keys
```

**New Way**:
```python
config = create_configuration_service("config.json")

# Manual validation (or create a domain service for validation)
required_keys = ["python_path"]
missing = [k for k in required_keys if not config.has(k)]
if missing:
    raise ConfigurationError(f"Missing required keys: {missing}")
```

#### `get_software_paths()` → Use get() with dot notation

**Old Way**:
```python
paths = config.get_software_paths()
# Returns: {"imagej": "...", "cellpose": "...", ...}
```

**New Way**:
```python
# Access individual paths directly
imagej_path = config.get("imagej_path", "")
cellpose_path = config.get("cellpose_path", "")
python_path = config.get("python_path", "")

# Or create a helper function if needed frequently
def get_software_paths(config: ConfigurationService) -> dict:
    return {
        "imagej": config.get("imagej_path", ""),
        "cellpose": config.get("cellpose_path", ""),
        "python": config.get("python_path", ""),
        "fiji": config.get("fiji_path", ""),
    }
```

#### `get_analysis_settings()` → Direct access

**Old Way**:
```python
settings = config.get_analysis_settings()
cell_diameter = settings["cell_diameter"]
```

**New Way**:
```python
# Access directly with dot notation
cell_diameter = config.get("analysis.cell_diameter", 100)
segmentation_model = config.get("analysis.segmentation_model", "cyto")
```

---

## Migration Steps

### Step 1: Update Imports

**Before**:
```python
from percell.application.config_api import Config, ConfigError, create_default_config
```

**After**:
```python
from percell.domain.services.configuration_service import (
    ConfigurationService,
    create_configuration_service
)
from percell.domain.exceptions import ConfigurationError
```

### Step 2: Update Initialization

**Before**:
```python
try:
    config = Config(config_path)
except ConfigError:
    print("Config not found, creating default...")
    config = create_default_config(config_path)
```

**After**:
```python
# The new service can create missing configs automatically
config = create_configuration_service(
    config_path,
    create_if_missing=True  # Creates empty config if missing
)

# If you need to populate defaults, do it explicitly:
if not config.get("python_path"):
    config.set("python_path", sys.executable)
    config.set("analysis.cell_diameter", 100)
    config.save()
```

### Step 3: Update Method Calls

**Before**:
```python
# Old Config class
config.load()
imagej_path = config.get("imagej_path", "")
config.set("output.compression", "lzw")
config.save()
data = config.to_dict()
```

**After**:
```python
# New ConfigurationService
config.load(create_if_missing=True)  # Note: new parameter
imagej_path = config.get("imagej_path", "")  # Same!
config.set("output.compression", "lzw")  # Same!
config.save()  # Same!
data = config.to_dict()  # Same (but returns defensive copy)
```

### Step 4: Handle Custom Methods

Replace helper methods with direct access or create your own helpers:

```python
# Create a helper module if needed
# application/config_helpers.py

from percell.domain.services.configuration_service import ConfigurationService
from typing import Dict, Any

def get_software_paths(config: ConfigurationService) -> Dict[str, str]:
    """Get all configured software paths."""
    return {
        "imagej": config.get("imagej_path", ""),
        "cellpose": config.get("cellpose_path", ""),
        "python": config.get("python_path", ""),
        "fiji": config.get("fiji_path", ""),
    }

def get_analysis_settings(config: ConfigurationService) -> Dict[str, Any]:
    """Get all analysis settings."""
    return {
        "default_bins": config.get("analysis.default_bins", 5),
        "segmentation_model": config.get("analysis.segmentation_model", "cyto"),
        "cell_diameter": config.get("analysis.cell_diameter", 100),
        "flow_threshold": config.get("analysis.flow_threshold", 0.4),
    }

def validate_config(config: ConfigurationService) -> None:
    """Validate required configuration keys."""
    required = ["python_path"]
    missing = [k for k in required if not config.has(k)]
    if missing:
        from percell.domain.exceptions import ConfigurationError
        raise ConfigurationError(f"Missing required keys: {missing}")
```

---

## Common Patterns

### Pattern 1: Configuration in Application Container

**Before**:
```python
from percell.application.config_api import Config

def build_container(config_path: Path):
    config = Config(str(config_path))
    # ... rest of container setup
```

**After**:
```python
from percell.domain.services.configuration_service import create_configuration_service

def build_container(config_path: Path):
    config = create_configuration_service(config_path, create_if_missing=True)
    # ... rest of container setup (same as before)
```

### Pattern 2: Configuration in Main Entry Point

**Before**:
```python
from percell.application.config_api import Config, ConfigError, create_default_config

try:
    config = Config(config_path)
except ConfigError:
    config = create_default_config(config_path)
```

**After**:
```python
from percell.domain.services.configuration_service import create_configuration_service
from percell.domain.exceptions import ConfigurationError

# Simplified - handles missing files automatically
config = create_configuration_service(config_path, create_if_missing=True)

# Optionally populate with defaults
if not config.has("python_path"):
    import sys
    config.set("python_path", sys.executable)
    # ... other defaults
    config.save()
```

### Pattern 3: Reading Nested Configuration

**Before & After** (No change needed!):
```python
# Both old and new support dot notation
imagej_path = config.get("paths.imagej", "/default/path")
cell_diameter = config.get("analysis.cell_diameter", 100)
compression = config.get("output.compression", "lzw")
```

### Pattern 4: Updating Multiple Values

**Before & After** (No change needed!):
```python
config.update({
    "analysis.cell_diameter": 150,
    "output.compression": "lzw"
})
config.save()
```

### Pattern 5: Path Resolution (New Feature!)

**New Capability**:
```python
from pathlib import Path

# Automatically resolve relative paths against project root
cellpose_path = config.get_resolved_path("cellpose_path", project_root)
# If config has "cellpose_venv/bin/python", returns: project_root / "cellpose_venv/bin/python"
```

---

## Breaking Changes

### 1. Constructor Behavior

**Old**: Constructor auto-loads and raises immediately if file missing
```python
config = Config("missing.json")  # Raises ConfigError immediately
```

**New**: Constructor doesn't load; use factory or explicit load
```python
# Option 1: Factory (recommended)
config = create_configuration_service("missing.json", create_if_missing=True)

# Option 2: Explicit load
config = ConfigurationService(Path("missing.json"))
config.load(create_if_missing=True)
```

### 2. Exception Types

**Old**: `from percell.application.config_api import ConfigError`

**New**: `from percell.domain.exceptions import ConfigurationError`

### 3. Data Access

**Old**: Direct access to `config.config_data` dict

**New**: Use `config.to_dict()` for a defensive copy
```python
# Old way (direct mutation possible)
data = config.config_data
data["key"] = "value"  # Mutates config!

# New way (defensive copy)
data = config.to_dict()
data["key"] = "value"  # Doesn't affect config
```

### 4. Custom Helper Methods Removed

These methods no longer exist on the config object:
- `validate()` → Implement manually or create helper
- `get_software_paths()` → Create helper or use direct access
- `get_analysis_settings()` → Use dot notation
- `get_output_settings()` → Use dot notation

See [Step 4: Handle Custom Methods](#step-4-handle-custom-methods) for migration.

---

## Troubleshooting

### Issue: Import Error

**Problem**:
```python
ImportError: cannot import name 'Config' from 'percell.application.config_api'
```

**Solution**: Update your imports to use the new service
```python
# Old
from percell.application.config_api import Config

# New
from percell.domain.services.configuration_service import create_configuration_service
```

### Issue: ConfigError vs ConfigurationError

**Problem**:
```python
NameError: name 'ConfigError' is not defined
```

**Solution**: Update exception imports
```python
# Old
from percell.application.config_api import ConfigError

# New
from percell.domain.exceptions import ConfigurationError
```

### Issue: Missing Helper Methods

**Problem**:
```python
AttributeError: 'ConfigurationService' object has no attribute 'get_software_paths'
```

**Solution**: Use direct access or create helpers (see [Pattern 4](#step-4-handle-custom-methods))
```python
# Instead of:
paths = config.get_software_paths()

# Do:
imagej = config.get("imagej_path", "")
cellpose = config.get("cellpose_path", "")
```

### Issue: File Not Found on Load

**Problem**:
```python
ConfigurationError: Configuration file not found: config.json
```

**Solution**: Use `create_if_missing=True`
```python
config = create_configuration_service(
    "config.json",
    create_if_missing=True  # Won't raise if missing
)
```

---

## Deprecation Timeline

### Current Release (v1.x)
- ✅ `ConfigurationService` available in domain layer
- ⚠️ `Config` deprecated but still functional
- 📝 Deprecation warnings added to old classes
- 🔄 Compatibility layer provides bridges

### Next Release (v2.0)
- ❌ `application/config_api.Config` removed
- ❌ `application/configuration_manager.py` removed
- 🔄 Compatibility layer remains for one more version
- 📚 All examples updated to new API

### Future Release (v2.1+)
- ❌ Compatibility layer removed
- ✅ Only `ConfigurationService` remains

---

## Quick Reference Card

### Import Changes
```python
# Before
from percell.application.config_api import Config, ConfigError

# After
from percell.domain.services.configuration_service import (
    create_configuration_service,
    ConfigurationService
)
from percell.domain.exceptions import ConfigurationError
```

### Initialization Changes
```python
# Before
config = Config("config.json")

# After
config = create_configuration_service("config.json", create_if_missing=True)
```

### Methods That Stay The Same ✅
- `config.get(key, default)`
- `config.set(key, value)`
- `config.load()`
- `config.save()`
- `config.update(dict)`
- `config.to_dict()`

### New Methods ✨
- `config.has(key)` - Check if key exists
- `config.delete(key)` - Remove a key
- `config.clear()` - Clear all data
- `config.get_resolved_path(key, root)` - Resolve relative paths

### Removed Methods ⚠️
- `config.validate()` - Implement manually
- `config.get_software_paths()` - Use direct access
- `config.get_analysis_settings()` - Use dot notation
- `config.get_output_settings()` - Use dot notation

---

## Need Help?

If you encounter issues during migration:

1. Check this guide's [Troubleshooting](#troubleshooting) section
2. Review [Common Patterns](#common-patterns) for your use case
3. Look at updated examples in `tests/unit/domain/test_configuration_service.py`
4. Review the [API Comparison](#api-comparison) table
5. Create an issue at https://github.com/marcusjoshm/percell/issues

---

**Generated**: 2025-09-30
**Last Updated**: 2025-09-30
**Version**: 1.0
