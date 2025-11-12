#!/bin/bash
# This script launches both Cellpose and ImageJ for interactive segmentation work

# Get the script's directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
WORKSPACE_DIR="$(dirname "$(dirname "$SCRIPT_DIR")")"

# Path to Cellpose virtual environment
CELLPOSE_ENV="$WORKSPACE_DIR/cellpose_venv"
# Path to FIJI/ImageJ executable
IMAGEJ_PATH="/Applications/Fiji.app/Contents/MacOS/ImageJ-macosx"
# Preprocessed images directory
PREPROCESSED_DIR="$1"

echo "Launching segmentation tools for interactive cell segmentation..."
echo "Preprocessed images directory: $PREPROCESSED_DIR"

# Function to handle errors
handle_error() {
    echo "Error: $1"
    exit 1
}

# Launch ImageJ in the background
echo "Starting ImageJ..."
"$IMAGEJ_PATH" &
IMAGEJ_PID=$!

# Check if ImageJ started successfully
if [ $? -ne 0 ]; then
    handle_error "Failed to start ImageJ"
fi

# Change to the workspace directory
cd "$WORKSPACE_DIR" || handle_error "Could not change to workspace directory"

# Activate the Cellpose virtual environment
if [ ! -f "$CELLPOSE_ENV/bin/activate" ]; then
    handle_error "Cellpose virtual environment not found at $CELLPOSE_ENV"
fi

# Source the activate script
source "$CELLPOSE_ENV/bin/activate"

# Verify we're using the correct Python interpreter
PYTHON_PATH=$(which python)
if [[ ! "$PYTHON_PATH" == *"cellpose_venv"* ]]; then
    handle_error "Not using Python from Cellpose virtual environment. Current Python: $PYTHON_PATH"
fi

# Check if numpy is installed
if ! python -c "import numpy" 2>/dev/null; then
    echo "Installing numpy..."
    pip install numpy
fi

# Check if cellpose is installed
if ! python -c "import cellpose" 2>/dev/null; then
    # Check if the error is just a NumPy compatibility warning
    if python -c "import cellpose" 2>&1 | grep -q "numpy.*compatibility"; then
        echo "Cellpose detected with NumPy compatibility warning - this is normal"
    else
        echo "Installing cellpose version 4.0.7..."
        pip install "cellpose==4.0.7"
    fi
fi

# Start Cellpose GUI in the background
echo "Starting Cellpose GUI..."
python -m cellpose &
CELLPOSE_PID=$!

# Check if Cellpose started successfully
if [ $? -ne 0 ]; then
    # Kill ImageJ if Cellpose fails to start
    kill $IMAGEJ_PID 2>/dev/null
    deactivate
    handle_error "Failed to start Cellpose"
fi

echo -e "\n===========================================================================\n"
echo "Cellpose and FIJI are now running. Please follow these steps:"
echo ""
echo "In Cellpose:"
echo "1. Navigate to: $PREPROCESSED_DIR"
echo "2. Open and segment your images"
echo "3. Save segmentations as .zip files in the same directory"
echo ""
echo "In FIJI:"
echo "1. Open the same images for comparison if needed"
echo "2. Use the ROI Manager to view and adjust segmentations"
echo "3. Save any modified ROIs"
echo ""
echo "When finished with both applications, press Enter to continue the workflow..."
echo -e "\n===========================================================================\n"

# Wait for user to press Enter
read

# Kill background processes if they're still running
echo "Closing Cellpose and FIJI..."
kill $CELLPOSE_PID 2>/dev/null
kill $IMAGEJ_PID 2>/dev/null

# Deactivate the Cellpose environment
deactivate

echo "Segmentation tools closed. Continuing workflow..."
exit 0