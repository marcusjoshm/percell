# Percell Installation Guide for iMac (macOS Catalina 10.15.7)

This guide provides step-by-step instructions for installing and running percell on an iMac 27-inch (Late 2013) running macOS Catalina 10.15.7 with an existing conda cellpose installation.

## Overview

This installation approach leverages your existing conda-based cellpose installation while installing percell in a separate Python virtual environment. This allows percell to call cellpose from the global conda environment without version conflicts.

**Important Note**: This is a **minimal installation** that excludes GUI components (napari, PyQt5) which require Qt build tools not compatible with macOS Catalina. You'll have CLI-based workflow capabilities and can use cellpose GUI from the conda environment separately.

## Prerequisites

### Required Software

1. **macOS Catalina 10.15.7** (your current OS)
2. **Python 3.8 or higher** (Python 3.11+ recommended)
3. **Conda** (Miniconda or Anaconda)
4. **Cellpose installed in a conda environment** (already installed on your system)
5. **ImageJ/Fiji** (for image processing)

### Verify Your Existing Cellpose Installation

Before installing percell, verify that cellpose is working in your conda environment:

```bash
# List conda environments
conda env list

# Activate your cellpose environment (usually named 'cellpose_env')
conda activate cellpose_env

# Test cellpose
python -c "import cellpose; print(cellpose.__version__)"

# Deactivate when done testing
conda deactivate
```

## Installation Steps

### 1. Clone or Download Percell

If you haven't already, get the percell code:

```bash
cd ~/Documents  # or wherever you want to install
git clone https://github.com/yourusername/percell.git
cd percell
```

Or if you already have percell on the iMac, navigate to that directory:

```bash
cd /path/to/percell
```

### 2. Switch to the iMac Branch

Make sure you're on the branch with iMac support:

```bash
git checkout old_iMac_install
```

### 3. Run the Installation Script

The installation script will:
- Check for Python and conda
- Detect your cellpose conda environment
- Create a Python virtual environment for percell
- Install percell and its dependencies
- Configure percell to use your conda cellpose

```bash
./install_imac_catalina.sh
```

The script will guide you through the installation and report any issues.

### 4. Manual Configuration (if needed)

If the automatic installation didn't create a config file, or if you need to customize it:

```bash
# Create config directory
mkdir -p ~/.percell

# Copy the iMac template
cp percell/config/config.imac-catalina.template.json ~/.percell/config.json

# Edit the configuration
nano ~/.percell/config.json
```

Update these key settings:

```json
{
  "cellpose_type": "conda",
  "cellpose_conda_env": "cellpose_env",
  "conda_path": null,
  "imagej_path": "/Applications/Fiji.app/Contents/MacOS/ImageJ-macosx"
}
```

Configuration options:
- `cellpose_type`: Set to `"conda"` to use conda-based cellpose
- `cellpose_conda_env`: Name of your conda environment (default: `"cellpose_env"`)
- `conda_path`: Path to conda executable (leave as `null` to auto-detect)
- `imagej_path`: Path to your ImageJ/Fiji executable

## Usage

### Starting Percell

1. **Activate the virtual environment** (required each time):
   ```bash
   cd /path/to/percell
   source venv/bin/activate
   ```

2. **Run percell**:
   ```bash
   # Show help
   percell --help

   # Run GUI mode
   percell gui

   # Run workflow
   percell workflow --input /path/to/images --output /path/to/output
   ```

### How Cellpose is Called

When you run percell, it will automatically:
1. Detect that you're using conda-based cellpose (from your config)
2. Activate your cellpose conda environment behind the scenes
3. Run cellpose with the appropriate parameters
4. Deactivate the conda environment when done

**You do NOT need to manually activate the conda environment** - percell handles this automatically!

## Architecture Details

### Conda Adapter

Percell uses a special `CellposeCondaAdapter` that:
- Activates the conda environment before running cellpose
- Executes cellpose commands within that environment
- Properly handles environment cleanup

This is different from the standard `CellposeSubprocessAdapter` which expects a direct path to a Python interpreter with cellpose installed.

### File Locations

- **Percell installation**: Where you cloned/downloaded percell
- **Percell config**: `~/.percell/config.json`
- **Percell venv**: `<percell-dir>/venv/`
- **Cellpose conda env**: Managed by conda (use `conda env list` to see location)

## Troubleshooting

### "Cellpose environment not found"

Check your conda environments:
```bash
conda env list
```

Update your config with the correct environment name:
```json
{
  "cellpose_conda_env": "your_actual_env_name"
}
```

### "Conda not found"

Make sure conda is in your PATH:
```bash
# Add to ~/.bash_profile or ~/.zshrc
export PATH="$HOME/miniconda3/bin:$PATH"

# Then reload
source ~/.bash_profile  # or source ~/.zshrc
```

### Cellpose Fails to Run

Test cellpose directly:
```bash
# Activate conda environment
conda activate cellpose_env

# Try running cellpose
python -m cellpose --help

# If this works, cellpose is fine
# If not, reinstall cellpose:
pip install --upgrade cellpose

conda deactivate
```

### ImageJ/Fiji Not Found

Download and install Fiji:
1. Go to https://fiji.sc/
2. Download the macOS version
3. Extract to /Applications/
4. Update `imagej_path` in your config

Common ImageJ/Fiji paths:
- `/Applications/Fiji.app/Contents/MacOS/ImageJ-macosx`
- `/Applications/ImageJ.app/Contents/MacOS/ImageJ`
- `/Applications/ImageJ2.app/Contents/MacOS/ImageJ-macosx`

### Checking Logs

Percell creates detailed logs. Check them for errors:
```bash
# Run with verbose logging
percell --verbose workflow ...

# Or check recent logs
ls -lt ~/.percell/logs/
```

## Updating Percell

To update percell to the latest version:

```bash
cd /path/to/percell
git pull origin old_iMac_install

# Reactivate venv and reinstall
source venv/bin/activate
pip install -e .
```

## Performance Notes

Since your iMac is from 2013, keep these tips in mind:

1. **Use smaller batch sizes** when processing multiple images
2. **Close other applications** when running intensive analysis
3. **Process one condition/timepoint at a time** if memory is limited
4. **Use the binned images** for segmentation (4x4 binning reduces memory usage)

## Support

If you encounter issues:

1. Check the logs in `~/.percell/logs/`
2. Verify your conda cellpose installation works independently
3. Ensure all paths in the config are correct
4. Try running percell with `--verbose` flag for detailed output

## Example Workflow

Here's a complete example of running percell on the iMac:

```bash
# 1. Navigate to percell directory
cd ~/percell

# 2. Activate virtual environment
source venv/bin/activate

# 3. Check that everything is configured
percell --version
percell config --show

# 4. Run your workflow
percell workflow \
  --input /path/to/raw/images \
  --output /path/to/output \
  --conditions "Control,Treatment" \
  --channels "ch00,ch02"

# 5. When done, deactivate venv
deactivate
```

## Additional Resources

- Percell documentation: See README.md
- Cellpose documentation: https://cellpose.readthedocs.io/
- ImageJ/Fiji documentation: https://imagej.net/
