#!/bin/bash

# setup_output_structure.sh
# This script sets up the output directory structure for the microscopy analysis workflow
# It creates all the necessary directories but does NOT copy files yet
# Files will be copied later after data selection is complete

set -e  # Exit on any error

# ANSI color codes for better readability
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to display usage information
usage() {
    echo -e "${BLUE}Usage:${NC} $0 <input_directory> <output_directory>"
    echo "  <input_directory>: Path to the directory containing microscopy data"
    echo "  <output_directory>: Path to the output directory for analysis"
}

# Check if both directories are provided
if [ $# -ne 2 ]; then
    echo -e "${RED}Error: Missing required arguments${NC}"
    usage
    exit 1
fi

INPUT_DIR="$1"
OUTPUT_DIR="$2"

# Check if input directory exists
if [ ! -d "$INPUT_DIR" ]; then
    echo -e "${RED}Error: Input directory does not exist: $INPUT_DIR${NC}"
    exit 1
fi

echo -e "${GREEN}Setting up output directory structure: $OUTPUT_DIR${NC}"

# Create the main output directories
echo -e "${BLUE}Creating main output directories...${NC}"
mkdir -p "$OUTPUT_DIR"/{analysis,cells,combined_masks,grouped_cells,grouped_masks,masks,raw_data,ROIs,preprocessed}

echo -e "${GREEN}Base directory structure created${NC}"

# Create raw_data subdirectories based on input structure (but don't copy files yet)
echo -e "${BLUE}Creating raw_data subdirectories...${NC}"

condition_count=0
for condition_dir in "$INPUT_DIR"/*; do
    if [ -d "$condition_dir" ]; then
        condition_name=$(basename "$condition_dir")
        echo -e "${BLUE}Creating directory for condition: $condition_name${NC}"
        
        # Create condition directory in raw_data
        mkdir -p "$OUTPUT_DIR/raw_data/$condition_name"
        
        # Create subdirectories for timepoints if they exist
        for timepoint_dir in "$condition_dir"/*; do
            if [ -d "$timepoint_dir" ]; then
                timepoint_name=$(basename "$timepoint_dir")
                mkdir -p "$OUTPUT_DIR/raw_data/$condition_name/$timepoint_name"
                echo -e "${GREEN}  Created subdirectory: $condition_name/$timepoint_name${NC}"
            fi
        done
        
        condition_count=$((condition_count + 1))
    fi
done

echo -e "${GREEN}Output directory structure setup completed (created $condition_count condition directories)${NC}"

# Print final directory structure for verification
echo -e "${BLUE}Final output directory structure:${NC}"
find "$OUTPUT_DIR" -type d -maxdepth 3 | sort | while read -r dir; do
    # Calculate the relative depth
    depth=$(($(echo "$dir" | tr -cd '/' | wc -c) - $(echo "$OUTPUT_DIR" | tr -cd '/' | wc -c)))
    indent=$(printf "%$(($depth * 2))s" "")
    echo "${indent}$(basename "$dir")/"
done

echo -e "${GREEN}Setup complete!${NC}"
echo -e "${YELLOW}Note: Directory structure created. Files will be copied after data selection.${NC}"
exit 0 