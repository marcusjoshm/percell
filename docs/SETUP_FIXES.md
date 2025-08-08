# Setup Script Fixes

## Overview
This document describes the fixes made to the `setup_workflow.py` script and related files to resolve NumPy compatibility issues and ensure proper version management.

## Issues Fixed

### 1. NumPy Compatibility Issues
**Problem**: Cellpose was compiled with NumPy 1.x but the system had NumPy 2.x, causing compatibility warnings that were being treated as errors.

**Solution**: 
- Updated `percell/python/setup/path_detection.py` to use subprocess calls instead of direct `import cellpose`
- Updated `percell/python/core/config.py` to handle NumPy compatibility warnings gracefully
- Added user-friendly messages about NumPy compatibility warnings in `setup_workflow.py`

### 2. Cellpose Version Management
**Problem**: The setup was trying to install the latest Cellpose version instead of the specific version 4.0.4 that you wanted.

**Solution**:
- Ensured all installation scripts use `requirements_cellpose.txt` which specifies `cellpose[gui]==4.0.4`
- Removed redundant cellpose installation commands
- Updated `percell/setup/requirements.txt` to not include Cellpose (since it should only be in the dedicated environment)

## Requirements Files Usage

### `percell/setup/requirements.txt`
- **Purpose**: Main workflow dependencies (excluding Cellpose)
- **Used by**: Main workflow environment (`venv`)
- **Installed via**: `setup_workflow.py` and `install.sh`

### `requirements_cellpose.txt`
- **Purpose**: Cellpose and its dependencies (version 4.0.4)
- **Used by**: Cellpose virtual environment (`cellpose_venv`)
- **Installed via**: `setup_workflow.py`, `install.sh`, and `percell/python/setup/path_detection.py`

## Installation Flow

1. **Main Environment Setup**:
   ```bash
   python3.11 -m venv venv
   source venv/bin/activate
   pip install -r percell/setup/requirements.txt
   ```

2. **Cellpose Environment Setup**:
   ```bash
   python3.11 -m venv cellpose_venv
   source cellpose_venv/bin/activate
   pip install -r percell/setup/requirements_cellpose.txt
   ```

## Files Modified

1. **`setup_workflow.py`**:
   - Added NumPy compatibility warning messages
   - Added `install_main_requirements()` method
   - Updated to use `requirements_cellpose.txt` for Cellpose installation

2. **`percell/python/setup/path_detection.py`**:
   - Updated `detect_cellpose()` to use subprocess for Cellpose import
   - Updated `_validate_cellpose_in_env()` to handle NumPy warnings
   - Updated to use `requirements_cellpose.txt` for installation

3. **`percell/python/core/config.py`**:
   - Updated `detect_software_paths()` to use subprocess for Cellpose detection

4. **`install.sh`**:
   - Removed redundant Cellpose installation
   - Added NumPy compatibility warning handling

5. **`percell/bash/launch_segmentation_tools.sh`**:
   - Updated Cellpose installation to use version 4.0.4
   - Added NumPy compatibility warning handling

6. **`percell/setup/requirements.txt`**:
   - Removed Cellpose dependency (now only in `requirements_cellpose.txt`)

## Testing

To test the fixes:

1. **Clean installation**:
   ```bash
   rm -rf venv cellpose_venv
   ./install.sh
   ```

2. **Setup script test**:
   ```bash
   # Default behavior: creates configuration automatically
   python setup_workflow.py
   
   # Only check requirements without creating config
   python setup_workflow.py --check-only
   
   # Create configuration with force overwrite
   python setup_workflow.py --force
   ```

3. **Verify Cellpose version**:
   ```bash
   source cellpose_venv/bin/activate
   python -c "import cellpose; print(cellpose.__version__)"
   # Should output: 4.0.4
   ```

## Expected Behavior

- Setup script should complete without errors
- NumPy compatibility warnings should be displayed but not treated as errors
- Cellpose version 4.0.4 should be installed in the dedicated environment
- Main workflow should function correctly with the main environment
- Cellpose should function correctly with its dedicated environment 