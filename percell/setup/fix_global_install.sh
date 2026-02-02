#!/bin/bash

# Fix Global Percell Installation
# This script fixes the issue where percell is installed but not globally accessible

echo "Fixing Percell Global Installation"
echo "=================================="

# Get the project root (two levels up from setup directory)
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
VENV_PERCELL="$PROJECT_ROOT/venv/bin/percell"
GLOBAL_PERCELL="/usr/local/bin/percell"

echo "Project root: $PROJECT_ROOT"
echo "Virtual environment percell: $VENV_PERCELL"
echo "Global percell: $GLOBAL_PERCELL"

# Check if the virtual environment percell exists
if [[ ! -f "$VENV_PERCELL" ]]; then
    echo "Error: Percell not found in virtual environment at $VENV_PERCELL"
    echo "Please ensure the package is installed:"
    echo "  source venv/bin/activate"
    echo "  pip install -e ."
    exit 1
fi

echo "✅ Found percell in virtual environment"

# Remove existing global link if it exists
if [[ -L "$GLOBAL_PERCELL" ]]; then
    echo "Removing existing global link..."
    sudo rm "$GLOBAL_PERCELL"
fi

# Create the global symbolic link
echo "Creating global symbolic link..."
sudo ln -sf "$VENV_PERCELL" "$GLOBAL_PERCELL"

# Verify the installation
if [[ -L "$GLOBAL_PERCELL" ]]; then
    echo "✅ Global percell link created successfully"
    echo "Testing global command..."
    if command -v percell >/dev/null 2>&1; then
        echo "✅ Global percell command is working!"
        echo ""
        echo "You can now run 'percell' from any directory."
        echo "Try: percell --help"
    else
        echo "❌ Global percell command not found in PATH"
        echo "Please check your PATH environment variable"
    fi
else
    echo "❌ Failed to create global link"
    echo "You may need to run this script with sudo"
fi 