#!/bin/bash
# Installation script for percell on iMac running macOS Catalina 10.15.7
# This script installs percell to work with an existing conda cellpose installation

set -e  # Exit on error

echo "=========================================="
echo "Percell Installation for iMac Catalina"
echo "=========================================="
echo ""

# Color codes for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[✓]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[!]${NC} $1"
}

print_error() {
    echo -e "${RED}[✗]${NC} $1"
}

# Check Python version
echo "Checking Python version..."
PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
PYTHON_MAJOR=$(echo $PYTHON_VERSION | cut -d. -f1)
PYTHON_MINOR=$(echo $PYTHON_VERSION | cut -d. -f2)

if [ "$PYTHON_MAJOR" -lt 3 ] || ([ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -lt 8 ]); then
    print_error "Python 3.8 or higher is required. Found: $PYTHON_VERSION"
    exit 1
fi
print_status "Python version: $PYTHON_VERSION"

# Check if conda is available
echo ""
echo "Checking for conda installation..."
if command -v conda &> /dev/null; then
    CONDA_VERSION=$(conda --version 2>&1)
    print_status "Found conda: $CONDA_VERSION"
else
    print_error "Conda not found. Please install Miniconda or Anaconda first."
    echo "You can download Miniconda from: https://docs.conda.io/en/latest/miniconda.html"
    exit 1
fi

# Check if cellpose conda environment exists
echo ""
echo "Checking for cellpose conda environment..."
if conda env list | grep -q "cellpose_env"; then
    print_status "Found cellpose_env conda environment"
    CELLPOSE_ENV_NAME="cellpose_env"
else
    print_warning "cellpose_env not found. Checking for other cellpose environments..."

    # Try to find any environment with cellpose in the name
    CELLPOSE_ENVS=$(conda env list | grep -i cellpose | awk '{print $1}' || true)

    if [ -z "$CELLPOSE_ENVS" ]; then
        print_error "No cellpose environment found."
        echo ""
        echo "Please create a conda environment with cellpose installed:"
        echo "  conda create -n cellpose_env python=3.11"
        echo "  conda activate cellpose_env"
        echo "  pip install cellpose"
        exit 1
    else
        # Use the first cellpose environment found
        CELLPOSE_ENV_NAME=$(echo "$CELLPOSE_ENVS" | head -n1)
        print_status "Found cellpose environment: $CELLPOSE_ENV_NAME"
    fi
fi

# Verify cellpose is installed in the environment
echo ""
echo "Verifying cellpose installation in $CELLPOSE_ENV_NAME..."
if conda run -n "$CELLPOSE_ENV_NAME" python -c "import cellpose" 2>/dev/null; then
    CELLPOSE_VERSION=$(conda run -n "$CELLPOSE_ENV_NAME" python -c "import cellpose; print(cellpose.__version__)" 2>/dev/null)
    print_status "Cellpose is installed (version: $CELLPOSE_VERSION)"
else
    print_error "Cellpose is not installed in the $CELLPOSE_ENV_NAME environment."
    echo ""
    echo "Please install cellpose in the conda environment:"
    echo "  conda activate $CELLPOSE_ENV_NAME"
    echo "  pip install cellpose"
    exit 1
fi

# Create virtual environment for percell
echo ""
echo "Creating Python virtual environment for percell..."
if [ -d "venv" ]; then
    print_warning "Virtual environment already exists. Skipping creation."
else
    python3 -m venv venv
    print_status "Created virtual environment"
fi

# Activate virtual environment
echo ""
echo "Activating virtual environment..."
source venv/bin/activate
print_status "Virtual environment activated"

# Upgrade pip
echo ""
echo "Upgrading pip..."
python -m pip install --upgrade pip --quiet
print_status "Pip upgraded"

# Install percell in development mode
echo ""
echo "Installing percell and dependencies..."
pip install -e . --quiet
print_status "Percell installed in development mode"

# Create config directory if it doesn't exist
echo ""
echo "Setting up configuration..."
if [ ! -f "$HOME/.percell/config.json" ]; then
    mkdir -p "$HOME/.percell"

    # Copy the iMac-specific config template
    if [ -f "percell/config/config.imac-catalina.template.json" ]; then
        cp percell/config/config.imac-catalina.template.json "$HOME/.percell/config.json"

        # Update the config with the detected cellpose environment
        python3 << EOF
import json
config_path = "$HOME/.percell/config.json"
with open(config_path, 'r') as f:
    config = json.load(f)
config['cellpose_conda_env'] = '$CELLPOSE_ENV_NAME'
with open(config_path, 'w') as f:
    json.dump(config, f, indent=2)
EOF
        print_status "Created configuration file at $HOME/.percell/config.json"
        print_status "Using cellpose conda environment: $CELLPOSE_ENV_NAME"
    else
        print_warning "Template config not found, you'll need to configure manually"
    fi
else
    print_warning "Configuration file already exists at $HOME/.percell/config.json"
    echo "To use the conda cellpose adapter, ensure your config contains:"
    echo '  "cellpose_type": "conda",'
    echo '  "cellpose_conda_env": "'$CELLPOSE_ENV_NAME'",'
fi

# Check for ImageJ/Fiji
echo ""
echo "Checking for ImageJ/Fiji..."
IMAGEJ_PATHS=(
    "/Applications/Fiji.app/Contents/MacOS/ImageJ-macosx"
    "/Applications/ImageJ.app/Contents/MacOS/ImageJ"
    "/Applications/ImageJ2.app/Contents/MacOS/ImageJ-macosx"
)

FOUND_IMAGEJ=false
for IMAGEJ_PATH in "${IMAGEJ_PATHS[@]}"; do
    if [ -f "$IMAGEJ_PATH" ]; then
        print_status "Found ImageJ/Fiji at: $IMAGEJ_PATH"
        FOUND_IMAGEJ=true
        break
    fi
done

if [ "$FOUND_IMAGEJ" = false ]; then
    print_warning "ImageJ/Fiji not found in standard locations"
    echo "Please install Fiji from: https://fiji.sc/"
    echo "After installation, update imagej_path in your config file"
fi

# Print installation summary
echo ""
echo "=========================================="
echo "Installation Complete!"
echo "=========================================="
echo ""
print_status "Percell has been installed successfully"
echo ""
echo "Configuration:"
echo "  - Cellpose environment: $CELLPOSE_ENV_NAME"
echo "  - Config file: $HOME/.percell/config.json"
echo ""
echo "To use percell:"
echo "  1. Activate the virtual environment:"
echo "     source venv/bin/activate"
echo ""
echo "  2. Run percell:"
echo "     percell --help"
echo ""
echo "  3. For GUI mode:"
echo "     percell gui"
echo ""
echo "Note: Cellpose will be called from the conda environment '$CELLPOSE_ENV_NAME'"
echo "      You do NOT need to activate the conda environment manually."
echo ""
