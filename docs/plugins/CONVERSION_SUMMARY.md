# Script to Plugin Conversion Summary

## What Was Done

Successfully converted `analyze_intensity_with_bs.py` to a PerCell plugin!

### Created Files

1. **`percell/plugins/intensity_analysis_plugin.py`**
   - Full plugin implementation
   - Integrates with PerCell's UI system
   - Uses lazy imports for dependencies
   - All original functionality preserved

### Improvements Made

1. **Plugin Architecture Integration**
   - Inherits from `PerCellPlugin`
   - Uses `UserInterfacePort` for all user interaction
   - Replaced `print()` with `ui.info()`
   - Replaced `input()` with `ui.prompt()`

2. **Dependency Handling**
   - Lazy imports (dependencies loaded only when needed)
   - Clear error messages if dependencies are missing
   - Plugin can be discovered even if dependencies aren't installed

3. **Registry Improvements**
   - Added AST-based discovery for plugins with missing dependencies
   - Better error handling during plugin discovery
   - Plugins are discovered even if imports fail

### Plugin Details

- **Name**: `intensity_analysis_bs`
- **Menu Title**: "Intensity Analysis with Background Subtraction"
- **Category**: analysis
- **Requires**: Input directory (prompts if not provided)
- **Dependencies**: numpy, scipy, matplotlib, roifile, pillow, tifffile, scikit-image

### How to Use

1. **Restart PerCell** (if already running)
2. **Open Plugins Menu**
3. **Select "Intensity Analysis with Background Subtraction"**
4. **Follow the prompts** to:
   - Select base directory
   - Configure analysis parameters
   - Run the analysis

### Original Script Location

The original script `analyze_intensity_with_bs.py` is still in `percell/plugins/` but is now redundant. You can:
- Keep it as a backup
- Remove it (the plugin version replaces it)
- Move it elsewhere

### Next Steps

1. **Install missing dependencies** (if needed):
   ```bash
   pip install roifile scikit-image
   ```

2. **Test the plugin**:
   - Run PerCell
   - Open Plugins menu
   - Select the intensity analysis plugin
   - Test with your data

3. **Customize if needed**:
   - Edit `percell/plugins/intensity_analysis_plugin.py`
   - Modify analysis configurations
   - Adjust UI messages

### Architecture Improvements

The plugin system now supports:
- ✅ Discovery of plugins with missing dependencies (via AST parsing)
- ✅ Lazy loading of dependencies
- ✅ Better error messages
- ✅ Graceful degradation

This means you can add plugins even if some dependencies aren't installed yet - they'll be discovered and show a helpful error when executed.

