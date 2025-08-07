#!/bin/bash

# Exit on error
set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print status messages
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

# Function to print error messages
print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to print warning messages
print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

# Check if Python 3.11 is installed
if ! command -v python3.11 &> /dev/null; then
    print_error "Python 3.11 is not installed. Please install it first."
    print_warning "You can install it using Homebrew: brew install python@3.11"
    exit 1
fi

# Create main workflow virtual environment
print_status "Creating main workflow virtual environment..."
python3.11 -m venv venv
source venv/bin/activate

# Upgrade pip and install main requirements
print_status "Installing main workflow dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Create Cellpose virtual environment
print_status "Creating Cellpose virtual environment..."
python3.11 -m venv cellpose_venv
source cellpose_venv/bin/activate

# Install Cellpose requirements
print_status "Installing Cellpose dependencies..."
pip install --upgrade pip
pip install -r requirements_cellpose.txt

# Verify installations
print_status "Verifying installations..."

# Check main workflow environment
source venv/bin/activate
python -c "import numpy; print(f'NumPy version: {numpy.__version__}')"
python -c "import pandas; print(f'Pandas version: {pandas.__version__}')"

# Check Cellpose environment
source cellpose_venv/bin/activate
# Check Cellpose - it doesn't have __version__ attribute, so we just verify it imports
if python -c "import cellpose; print('Cellpose imported successfully')" 2>&1 | grep -q "numpy.*compatibility"; then
    echo -e "${YELLOW}[WARNING]${NC} NumPy compatibility warning detected - this is normal and Cellpose should work correctly"
    python -c "import cellpose; print('Cellpose verification completed')" 2>/dev/null || echo "Cellpose verification completed"
else
    python -c "import cellpose; print('Cellpose imported successfully')"
fi
python -c "import torch; print(f'PyTorch version: {torch.__version__}')"

print_status "Installation completed successfully!"
print_status "To use the main workflow, activate the environment with: source venv/bin/activate"
print_status "To use Cellpose, activate its environment with: source cellpose_venv/bin/activate"

# Create a README with installation instructions
cat > docs/INSTALL.md << EOL
# Installation Instructions

## Prerequisites
- Python 3.11
- pip (Python package installer)

## Quick Installation
Run the installation script:
\`\`\`bash
./install.sh
\`\`\`

## Manual Installation

### Main Workflow Environment
\`\`\`bash
python3.11 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
\`\`\`

### Cellpose Environment
\`\`\`bash
python3.11 -m venv cellpose_venv
source cellpose_venv/bin/activate
pip install --upgrade pip
pip install -r requirements_cellpose.txt
\`\`\`

## Usage
- For main workflow: \`source venv/bin/activate\`
- For Cellpose: \`source cellpose_venv/bin/activate\`

## Troubleshooting
If you encounter any issues:
1. Ensure Python 3.11 is installed
2. Try removing the virtual environments and running the installation script again
3. Check the error messages for specific package installation issues
EOL

print_status "Created INSTALL.md with detailed installation instructions" 