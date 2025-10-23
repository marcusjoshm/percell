# iMac Setup Summary

This document provides a quick reference for the iMac Catalina installation modifications.

## What Was Created

### 1. New Adapter for Conda-based Cellpose
**File**: `percell/adapters/cellpose_conda_adapter.py`

A new adapter that can invoke cellpose from a conda environment by:
- Auto-detecting conda installation
- Activating the specified conda environment
- Running cellpose commands within that environment
- Properly cleaning up after execution

**Key Features**:
- Supports custom conda environment names
- Auto-detects conda path or accepts explicit path
- Uses bash scripts to handle conda activation
- Maintains same interface as subprocess adapter

### 2. Updated Container
**File**: `percell/application/container.py`

Modified to support both adapter types:
- Reads `cellpose_type` from configuration
- Instantiates appropriate adapter based on config
- Falls back to subprocess adapter by default (backward compatible)

**Configuration Options**:
```json
{
  "cellpose_type": "conda",              // New: "conda" or "subprocess"
  "cellpose_conda_env": "cellpose_env",  // New: conda environment name
  "conda_path": null                     // New: optional conda path
}
```

### 3. iMac Configuration Template
**File**: `percell/config/config.imac-catalina.template.json`

Pre-configured template for macOS Catalina with:
- `cellpose_type` set to `"conda"`
- Default conda environment name
- Standard macOS Fiji path
- All standard workflow steps

### 4. Installation Script
**File**: `install_imac_catalina.sh`

Automated installation script that:
- Checks Python version (requires 3.8+)
- Verifies conda installation
- Detects cellpose conda environment
- Creates Python venv for percell
- Installs percell in development mode
- Creates configuration file
- Validates ImageJ/Fiji installation

### 5. Comprehensive Documentation
**File**: `INSTALL_IMAC_CATALINA.md`

Complete installation guide including:
- Prerequisites and verification steps
- Step-by-step installation instructions
- Configuration details
- Usage examples
- Troubleshooting guide
- Performance tips for older hardware

**File**: `README_IMAC_BRANCH.md`

Branch-specific documentation covering:
- Architecture overview
- What's different from main branch
- Use cases and benefits
- Compatibility information
- Development notes
- Testing checklist

## Installation on iMac

### Quick Installation

1. Clone/navigate to percell directory
2. Checkout this branch: `git checkout old_iMac_install`
3. Run: `./install_imac_catalina.sh`
4. Activate venv: `source venv/bin/activate`
5. Use percell: `percell --help`

### Manual Installation

If you prefer manual setup or need to customize:

1. Create Python venv:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

2. Install percell:
   ```bash
   pip install -e .
   ```

3. Create config:
   ```bash
   mkdir -p ~/.percell
   cp percell/config/config.imac-catalina.template.json ~/.percell/config.json
   ```

4. Edit config to match your setup:
   ```bash
   nano ~/.percell/config.json
   ```

## How It Works

### Call Flow

```
User runs percell
    ↓
Container reads config
    ↓
Detects cellpose_type: "conda"
    ↓
Creates CellposeCondaAdapter
    ↓
When segmentation needed:
    ↓
Adapter creates bash command:
    eval "$(conda shell.bash hook)"
    conda activate cellpose_env
    python -m cellpose [args]
    ↓
Executes command via subprocess
    ↓
Returns results to percell
```

### Key Design Decisions

1. **Separate Environments**: Percell in Python venv, cellpose in conda env
   - Avoids dependency conflicts
   - Leverages existing cellpose installation
   - Each can be updated independently

2. **Bash Script Wrapper**: Uses bash to activate conda
   - Required because conda needs shell integration
   - Works on macOS and Linux
   - Handles environment activation/deactivation

3. **Backward Compatible**: Default behavior unchanged
   - Existing configs work without modification
   - Subprocess adapter still default
   - Conda adapter is opt-in via configuration

## File Structure

```
percell/
├── install_imac_catalina.sh           # Installation script
├── INSTALL_IMAC_CATALINA.md           # Installation guide
├── README_IMAC_BRANCH.md              # Branch documentation
├── IMAC_SETUP_SUMMARY.md              # This file
├── percell/
│   ├── adapters/
│   │   ├── cellpose_subprocess_adapter.py  # Original adapter
│   │   └── cellpose_conda_adapter.py       # New conda adapter
│   ├── application/
│   │   └── container.py                    # Modified to support both
│   └── config/
│       ├── config.template.json            # Original template
│       └── config.imac-catalina.template.json  # iMac template
```

## Testing Checklist

Before using on iMac:

- [ ] Verify Python 3.8+ installed
- [ ] Verify conda installed and in PATH
- [ ] Verify cellpose conda environment exists
- [ ] Run `./install_imac_catalina.sh`
- [ ] Check config created at `~/.percell/config.json`
- [ ] Activate venv: `source venv/bin/activate`
- [ ] Test import: `python -c "import percell; print(percell.__version__)"`
- [ ] Test cellpose: `percell gui` (should launch cellpose)
- [ ] Verify ImageJ/Fiji path in config

## Configuration Reference

### Conda Mode (iMac)
```json
{
  "cellpose_type": "conda",
  "cellpose_conda_env": "cellpose_env",
  "conda_path": null,
  "imagej_path": "/Applications/Fiji.app/Contents/MacOS/ImageJ-macosx"
}
```

### Subprocess Mode (Original)
```json
{
  "cellpose_type": "subprocess",
  "cellpose_path": "/path/to/venv/bin/python",
  "imagej_path": "/Applications/Fiji.app/Contents/MacOS/ImageJ-macosx"
}
```

### Auto-detection (Default)
If `cellpose_type` is not specified, percell uses subprocess mode.

## Troubleshooting Quick Reference

| Issue | Solution |
|-------|----------|
| "conda not found" | Add conda to PATH in ~/.bash_profile or ~/.zshrc |
| "cellpose_env not found" | Update `cellpose_conda_env` in config with actual name |
| Cellpose fails to run | Test: `conda activate cellpose_env && python -m cellpose --help` |
| ImageJ not found | Update `imagej_path` in config |
| Import errors | Make sure venv is activated: `source venv/bin/activate` |

## Next Steps

### To Use on iMac

1. Transfer this branch to your iMac:
   ```bash
   # On iMac
   git clone <your-repo-url>
   cd percell
   git checkout old_iMac_install
   ```

2. Run installation:
   ```bash
   ./install_imac_catalina.sh
   ```

3. Start using:
   ```bash
   source venv/bin/activate
   percell workflow --input <data> --output <results>
   ```

### To Merge to Main

This branch is designed to be merged to main when ready:
- All changes are backward compatible
- New adapter is additive (doesn't modify existing code)
- Default behavior unchanged
- Existing configs continue to work

Before merging:
1. Test on systems without conda
2. Add unit tests for conda adapter
3. Update main README with conda instructions
4. Consider broader use cases beyond iMac

## Support

For questions or issues:
1. See [INSTALL_IMAC_CATALINA.md](INSTALL_IMAC_CATALINA.md) for detailed troubleshooting
2. Check that conda cellpose works: `conda activate cellpose_env && python -m cellpose --help`
3. Verify config: `cat ~/.percell/config.json`
4. Check logs: `~/.percell/logs/`

## Version Information

- **Branch**: old_iMac_install
- **Target Hardware**: iMac 27-inch, Late 2013
- **Target OS**: macOS Catalina 10.15.7
- **Python**: 3.8+ (3.11+ recommended)
- **Cellpose**: 4.0.4+ (in conda environment)
- **Percell**: 1.0.0
