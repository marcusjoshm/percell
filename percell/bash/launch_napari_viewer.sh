#!/bin/bash
# This script launches Napari for interactive image visualization and analysis

# Get the script's directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
WORKSPACE_DIR="$(dirname "$(dirname "$SCRIPT_DIR")")"

# Path to main virtual environment with Napari
NAPARI_ENV="$WORKSPACE_DIR/venv"
# Images directory (optional first argument)
IMAGES_DIR="$1"

echo "Launching Napari for interactive image visualization..."
if [[ -n "$IMAGES_DIR" ]]; then
    echo "Images directory: $IMAGES_DIR"
fi

# Function to handle errors
handle_error() {
    echo "Error: $1"
    exit 1
}

# Change to the workspace directory
cd "$WORKSPACE_DIR" || handle_error "Could not change to workspace directory"

# Activate the virtual environment
if [[ ! -f "$NAPARI_ENV/bin/activate" ]]; then
    handle_error "Virtual environment not found at $NAPARI_ENV"
fi

# Source the activate script
source "$NAPARI_ENV/bin/activate"

# Verify we're using the correct Python interpreter
PYTHON_PATH=$(which python)
if [[ ! "$PYTHON_PATH" == *"venv"* ]]; then
    handle_error "Not using Python from virtual environment. Current Python: $PYTHON_PATH"
fi

# Check if napari is installed
if ! python -c "import napari" 2>/dev/null; then
    echo "Installing napari..."
    pip install "napari[all]"
fi

# Start Napari viewer
echo "Starting Napari viewer..."
if [[ -n "$IMAGES_DIR" ]] && [[ -d "$IMAGES_DIR" ]]; then
    # Launch napari with the images directory
    cd "$IMAGES_DIR" || handle_error "Could not change to images directory"
    python -m napari "$IMAGES_DIR"
else
    # Launch napari without specific directory
    python -m napari
fi

# Check if Napari started successfully
if [[ $? -ne 0 ]]; then
    deactivate
    handle_error "Failed to start Napari"
fi

echo -e "\n===========================================================================\n"
echo "Napari is now running for interactive image visualization and analysis."
echo ""
echo "Key features:"
echo "1. Load images: File > Open Files or drag and drop"
echo "2. View multi-dimensional data with layer controls"
echo "3. Overlay labels/masks for segmentation analysis"
echo "4. Use plugins for specialized analysis workflows"
echo "5. Interactive measurements and annotations"
echo ""
echo "When finished with visualization, close the Napari window to continue..."
echo -e "\n===========================================================================\n"

# Wait for Napari to close (it runs in foreground by default)
wait

# Deactivate the virtual environment
deactivate

echo "Napari viewer closed. Continuing workflow..."
exit 0