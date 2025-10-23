# Percell - iMac Catalina Branch

This branch (`old_iMac_install`) contains modifications to support running percell on older Mac hardware with existing conda-based cellpose installations.

## What's Different in This Branch?

### New Features

1. **Conda Cellpose Adapter** - A new adapter that calls cellpose from a conda environment
2. **Flexible Configuration** - Support for both subprocess and conda-based cellpose installations
3. **iMac-Specific Templates** - Pre-configured templates for macOS Catalina compatibility
4. **Automated Installation** - Installation script that detects and configures conda environments

### New Files

- `percell/adapters/cellpose_conda_adapter.py` - Adapter for conda-based cellpose
- `percell/config/config.imac-catalina.template.json` - Configuration template for iMac
- `install_imac_catalina.sh` - Automated installation script
- `INSTALL_IMAC_CATALINA.md` - Comprehensive installation guide

### Modified Files

- `percell/application/container.py` - Updated to support both adapter types
  - Now accepts `cellpose_type` configuration option
  - Automatically selects appropriate adapter based on config

## How It Works

### Architecture

```
┌─────────────────────────────────────────┐
│         Percell Application             │
│  (Python venv with percell installed)   │
└────────────────┬────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────┐
│      CellposeCondaAdapter               │
│  (Handles conda activation/deactivation)│
└────────────────┬────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────┐
│      Conda Environment Activation       │
│    eval "$(conda shell.bash hook)"      │
│    conda activate cellpose_env          │
└────────────────┬────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────┐
│     Cellpose in Conda Environment       │
│   (Global/system cellpose installation) │
└─────────────────────────────────────────┘
```

### Configuration Options

The configuration file (`~/.percell/config.json`) now supports:

```json
{
  "cellpose_type": "conda",           // "conda" or "subprocess" (default)
  "cellpose_conda_env": "cellpose_env", // Name of conda environment
  "conda_path": null                   // Path to conda (null = auto-detect)
}
```

**For subprocess mode** (original behavior):
```json
{
  "cellpose_type": "subprocess",      // or omit this field
  "cellpose_path": "/path/to/venv/bin/python"
}
```

## Use Cases

### Primary Use Case: iMac with Existing Cellpose

**Scenario**: You have an older Mac (macOS Catalina) with cellpose already installed via conda for other projects.

**Solution**: Use this branch to install percell alongside your existing cellpose without conflicts.

**Benefits**:
- No need to reinstall cellpose
- Leverages your tested, working cellpose installation
- Isolates percell dependencies in a separate venv
- Compatible with older macOS versions

### Secondary Use Case: Shared Cellpose Installation

**Scenario**: Multiple projects on the same machine need to use the same cellpose installation.

**Solution**: Install cellpose once in a conda environment, configure each project to use the conda adapter.

**Benefits**:
- Saves disk space
- Easier to update cellpose (update once, all projects benefit)
- Consistent cellpose version across projects

## Compatibility

### Tested On
- **Hardware**: iMac 27-inch, Late 2013
- **OS**: macOS Catalina 10.15.7
- **Python**: 3.11.13
- **Cellpose**: 4.0.4 (in conda environment)

### Should Work On
- macOS Catalina 10.15.x
- macOS Big Sur and later
- Any Mac with conda and cellpose installed
- Linux systems with conda (untested but should work)

### Requirements
- Python 3.8+ (for percell)
- Conda (Miniconda or Anaconda)
- Cellpose installed in a conda environment
- ImageJ/Fiji

## Installation

See [INSTALL_IMAC_CATALINA.md](INSTALL_IMAC_CATALINA.md) for detailed installation instructions.

**Quick Start**:
```bash
git checkout old_iMac_install
./install_imac_catalina.sh
```

## Merging to Main

This branch introduces backward-compatible changes. To merge to main:

1. The new `CellposeCondaAdapter` is additive (doesn't break existing functionality)
2. The container modification supports both adapter types
3. Default behavior remains unchanged (subprocess adapter)
4. New configuration options are optional

### Before Merging

- [ ] Test on systems without conda (should fall back to subprocess adapter)
- [ ] Test on newer macOS versions
- [ ] Add unit tests for `CellposeCondaAdapter`
- [ ] Update main README with conda adapter information
- [ ] Consider renaming branch to something more descriptive of the feature

## Development Notes

### Why Two Adapters?

The `CellposeSubprocessAdapter` expects a direct path to a Python interpreter with cellpose installed. This works great for:
- Virtual environments with cellpose installed
- Systems where you control the entire Python environment

The `CellposeCondaAdapter` is needed when:
- Cellpose is in a conda environment that needs activation
- You want to use a system/global cellpose installation
- Multiple projects share the same cellpose installation

### Bash Script Approach

The conda adapter uses bash scripts to activate the environment because:
1. `conda activate` requires shell integration
2. Python's `subprocess` can't directly activate conda environments
3. This approach works across macOS and Linux

### Future Improvements

Potential enhancements:
1. **Auto-detection**: Automatically detect conda environments and suggest configuration
2. **Environment creation**: Option to create a dedicated cellpose environment during setup
3. **Version checking**: Verify cellpose version compatibility before running
4. **Better error messages**: More helpful messages when conda environment issues occur
5. **Windows support**: Test and document Windows compatibility

## Testing

### Manual Testing Checklist

- [ ] Installation script runs successfully
- [ ] Config file is created with correct settings
- [ ] Percell can launch cellpose GUI
- [ ] Percell can run cellpose segmentation
- [ ] Output masks are generated correctly
- [ ] Errors are handled gracefully

### Test Cases

```bash
# Test 1: Check installation
source venv/bin/activate
percell --version

# Test 2: Verify configuration
percell config --show

# Test 3: Launch cellpose GUI
percell gui

# Test 4: Run segmentation on test images
percell workflow --input test_data/ --output test_output/
```

## Known Issues

1. **First Run Delay**: The first time cellpose runs, there may be a delay while conda initializes
2. **Path Escaping**: Paths with spaces require special handling in the bash script
3. **Conda Detection**: Auto-detection may fail if conda is installed in a non-standard location

## Contributing

If you're working on this branch:

1. Test on your iMac before committing
2. Update documentation for any new features
3. Keep commits focused and descriptive
4. Test backward compatibility with subprocess adapter

## Support

For issues specific to this branch:
- Check [INSTALL_IMAC_CATALINA.md](INSTALL_IMAC_CATALINA.md) troubleshooting section
- Verify conda and cellpose work independently
- Check logs in `~/.percell/logs/`
- Ensure configuration is correct

## License

Same as main percell project - MIT License
