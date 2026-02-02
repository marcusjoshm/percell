#!/bin/bash

# Percell Global Launcher Script
# This script allows running percell from anywhere without activating the venv manually

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Path to the virtual environment
VENV_PATH="$SCRIPT_DIR/venv"

# Check if virtual environment exists
if [[ ! -d "$VENV_PATH" ]]; then
    echo "Error: Virtual environment not found at $VENV_PATH"
    echo "Please ensure the virtual environment is set up correctly."
    exit 1
fi

# Activate the virtual environment and run percell
source "$VENV_PATH/bin/activate"
exec python -m percell.main.main "$@"
