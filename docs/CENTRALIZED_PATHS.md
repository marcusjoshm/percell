# Centralized Path Configuration System

This document explains the centralized path configuration system that was implemented to solve the global installation issues with the `percell` application.

## Problem Solved

Previously, the application had hardcoded paths throughout the codebase like:
- `"percell/bash/setup_output_structure.sh"`
- `"percell/config/config.json"`
- `"percell/modules/bin_images.py"`

When the application was installed globally and run from anywhere, these relative paths would fail because the current working directory was not the project root.

## Solution: Centralized Path Management

The solution implements a centralized path configuration system that:

1. **Automatically discovers the package root** regardless of where the command is run from
2. **Centralizes all file paths** in a single configuration
3. **Provides easy access** to any file in the package
4. **Makes the codebase more maintainable** by removing hardcoded paths

## How It Works

### 1. Path Configuration Class

The `PathConfig` class in `percell/core/paths.py` manages all file paths:

```python
from percell.core.paths import get_path, get_path_str, path_exists

# Get a path as a Path object
script_path = get_path("setup_output_structure_script")

# Get a path as a string
config_path = get_path_str("config_default")

# Check if a path exists
if path_exists("bin_images_module"):
    # Use the module
```

### 2. Package Root Discovery

The system automatically finds the package root by:

1. **Module location**: Uses the location of `paths.py` to find the package root
2. **Python path search**: Searches `sys.path` for the percell package
3. **Working directory search**: Looks in current and parent directories
4. **Fallback**: Uses a default path if all else fails

### 3. Centralized Path Definitions

All paths are defined in the `_initialize_paths()` method:

```python
paths = {
    # Bash scripts
    'setup_output_structure_script': self._package_root / 'bash' / 'setup_output_structure.sh',
    'prepare_input_structure_script': self._package_root / 'bash' / 'prepare_input_structure.sh',
    'launch_segmentation_tools_script': self._package_root / 'bash' / 'launch_segmentation_tools.sh',
    
    # Python modules
    'bin_images_module': self._package_root / 'modules' / 'bin_images.py',
    'analyze_cell_masks_module': self._package_root / 'modules' / 'analyze_cell_masks.py',
    
    # Configuration files
    'config_default': self._package_root / 'config' / 'config.json',
    'config_template': self._package_root / 'config' / 'config.template.json',
    
    # ImageJ macros
    'create_cell_masks_macro': self._package_root / 'macros' / 'create_cell_masks.ijm',
    'threshold_grouped_cells_macro': self._package_root / 'macros' / 'threshold_grouped_cells.ijm',
    
    # ... and many more
}
```

## Available Path Names

### Bash Scripts
- `setup_output_structure_script`
- `prepare_input_structure_script`
- `launch_segmentation_tools_script`

### Python Modules
- `bin_images_module`
- `analyze_cell_masks_module`
- `combine_masks_module`
- `create_cell_masks_module`
- `directory_setup_module`
- `duplicate_rois_for_channels_module`
- `extract_cells_module`
- `group_cells_module`
- `include_group_metadata_module`
- `measure_roi_area_module`
- `otsu_threshold_grouped_cells_module`
- `resize_rois_module`
- `set_directories_module`
- `stage_classes_module`
- `stage_registry_module`
- `track_rois_module`

### Configuration Files
- `config_default`
- `config_template`

### ImageJ Macros
- `analyze_cell_masks_macro`
- `create_cell_masks_macro`
- `extract_cells_macro`
- `measure_roi_area_macro`
- `resize_rois_macro`
- `threshold_grouped_cells_macro`

### Directories
- `package_root`
- `core`
- `modules`
- `main`
- `config_dir`
- `bash_dir`
- `macros_dir`
- `art_dir`
- `setup_dir`

### Setup Files
- `requirements_file`
- `requirements_cellpose_file`
- `install_script`

## Usage Examples

### Basic Usage

```python
from percell.core.paths import get_path, get_path_str, path_exists

# Get a script path
script_path = get_path("setup_output_structure_script")
print(f"Script location: {script_path}")

# Check if a file exists
if path_exists("config_default"):
    config_path = get_path_str("config_default")
    print(f"Config file: {config_path}")
```

### Making Files Executable

```python
from percell.core.paths import ensure_executable_path

# Make a bash script executable
ensure_executable_path("setup_output_structure_script")
```

### Running Scripts

```python
import subprocess
from percell.core.paths import get_path

# Run a bash script
script_path = get_path("setup_output_structure_script")
result = subprocess.run([str(script_path), input_dir, output_dir])

# Run a Python module
module_path = get_path("bin_images_module")
result = subprocess.run([sys.executable, str(module_path), "--help"])
```

### Listing All Paths

```python
from percell.core.paths import list_all_paths

# Get all available paths
all_paths = list_all_paths()
for name, path_str in all_paths.items():
    print(f"{name}: {path_str}")
```

## Migration from Old System

### Before (Hardcoded Paths)

```python
# Old way - hardcoded paths
script_path = Path("percell/bash/setup_output_structure.sh")
if not script_path.exists():
    raise FileNotFoundError(f"Script not found: {script_path}")

# Make executable
script_path.chmod(0o755)

# Run script
subprocess.run([str(script_path), input_dir, output_dir])
```

### After (Centralized Paths)

```python
# New way - centralized paths
from percell.core.paths import get_path, ensure_executable_path

script_path = get_path("setup_output_structure_script")
ensure_executable_path("setup_output_structure_script")

# Run script
subprocess.run([str(script_path), input_dir, output_dir])
```

## Benefits

1. **Global Installation**: Works from any directory
2. **Maintainability**: All paths in one place
3. **Reliability**: Automatic package discovery
4. **Flexibility**: Easy to add new paths
5. **Consistency**: Standardized path access
6. **Error Handling**: Better error messages for missing files

## Testing

You can test the path system using the provided test script:

```bash
python test_paths.py
```

This will show:
- Package root location
- All available paths
- Whether each path exists
- Complete path listing

## Adding New Paths

To add a new path to the system:

1. **Add to `_initialize_paths()`** in `percell/core/paths.py`:
   ```python
   'new_file_path': self._package_root / 'path' / 'to' / 'file.ext',
   ```

2. **Use in your code**:
   ```python
   from percell.core.paths import get_path
   file_path = get_path("new_file_path")
   ```

## Troubleshooting

### Path Not Found Errors

If you get a `KeyError` for a path name:

1. Check the available paths:
   ```python
   from percell.core.paths import list_all_paths
   print(list_all_paths().keys())
   ```

2. Verify the path exists in `_initialize_paths()`

3. Make sure the file actually exists in the package

### Package Root Discovery Issues

If the package root is not found correctly:

1. Check that the expected directories exist:
   - `bash/`
   - `config/`
   - `macros/`
   - `core/`
   - `modules/`

2. Verify the package structure is correct

3. Check if the package is installed correctly

## Future Enhancements

Potential improvements to the path system:

1. **Environment-specific paths**: Different paths for development vs production
2. **User-configurable paths**: Allow users to override default paths
3. **Path validation**: Validate that all required files exist at startup
4. **Caching**: Cache path lookups for better performance
5. **Path templates**: Support for path patterns and substitutions
