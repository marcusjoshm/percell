#!/bin/bash

# prepare_input_structure.sh
# This script prepares the input directory structure for the microscopy analysis workflow
# It handles three possible input structures:
# 1. .tif files directly in the input directory
# 2. One layer of subdirectories containing .tif files
# 3. Two layers of subdirectories containing .tif files (already properly formatted)

set -e  # Exit on any error

# ANSI color codes for better readability
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to display usage information
usage() {
    echo -e "${BLUE}Usage:${NC} $0 <input_directory>"
    echo "  <input_directory>: Path to the directory containing microscopy data"
}

# Check if input directory is provided
if [[ $# -ne 1 ]]; then
    echo -e "${RED}Error: Missing input directory${NC}"
    usage
    exit 1
fi

INPUT_DIR="$1"

# Check if input directory exists
if [[ ! -d "$INPUT_DIR" ]]; then
    echo -e "${RED}Error: Input directory does not exist: $INPUT_DIR${NC}"
    exit 1
fi

echo -e "${GREEN}Preparing input directory structure: $INPUT_DIR${NC}"

# Function to count .tif files in a directory
count_tif_files() {
    find "$1" -maxdepth 1 -name "*.tif" | wc -l
}

# Function to check if a directory contains subdirectories
has_subdirectories() {
    find "$1" -maxdepth 1 -type d -not -path "$1" | grep -q .
    return $?
}

# Function to check if a filename contains a timepoint pattern (tXX)
has_timepoint_pattern() {
    if [[ "$1" =~ t[0-9]+ ]]; then
        return 0  # Pattern found
    else
        return 1  # Pattern not found
    fi
}

# Function to check if a filename contains a channel pattern (chXX)
has_channel_pattern() {
    if [[ "$1" =~ ch[0-9]+ ]]; then
        return 0  # Pattern found
    else
        return 1  # Pattern not found
    fi
}

# Function to process files in a timepoint directory
# This creates symbolic links with required patterns rather than renaming files
process_timepoint_directory() {
    local timepoint_dir="$1"
    local region_counter=1
    
    echo -e "${BLUE}Processing files in: $timepoint_dir${NC}"
    for tif_file in "$timepoint_dir"/*.tif; do
        if [[ -f "$tif_file" ]]; then
            local filename=$(basename "$tif_file")
            local dirname=$(dirname "$tif_file")
            
            # Check if missing timepoint pattern
            if ! has_timepoint_pattern "$filename"; then
                echo -e "${YELLOW}File missing timepoint pattern: $filename${NC}"
                filename="${filename%.tif}_t00.tif"
                echo -e "${GREEN}Adding timepoint pattern: $filename${NC}"
                mv "$tif_file" "$dirname/$filename"
                tif_file="$dirname/$filename"
            fi
            
            # Check if missing channel pattern
            if ! has_channel_pattern "$filename"; then
                echo -e "${YELLOW}File missing channel pattern: $filename${NC}"
                filename="${filename%.tif}_ch00.tif"
                echo -e "${GREEN}Adding channel pattern: $filename${NC}"
                mv "$tif_file" "$dirname/$filename"
            fi
            
            # Each file is considered its own region
            echo -e "${GREEN}File will be treated as Region $region_counter: $filename${NC}"
            region_counter=$((region_counter + 1))
        fi
    done
}

# Remove all MetaData directories at any level
echo -e "${BLUE}Searching for and removing MetaData directories...${NC}"
find "$INPUT_DIR" -type d -name "MetaData" | while read -r metadata_dir; do
    echo -e "${YELLOW}Removing MetaData directory: $metadata_dir${NC}"
    rm -rf "$metadata_dir"
done

# Report how many were removed
metadata_count=$(find "$INPUT_DIR" -type d -name "MetaData" | wc -l)
if [[ "$metadata_count" -eq 0 ]]; then
    echo -e "${GREEN}No MetaData directories found or all have been successfully removed${NC}"
else
    echo -e "${RED}Warning: $metadata_count MetaData directories could not be removed${NC}"
fi

# Count .tif files directly in the input directory
TIF_COUNT=$(count_tif_files "$INPUT_DIR")

if [[ $TIF_COUNT -gt 0 ]]; then
    # Case 1: .tif files are directly in the input directory
    echo -e "${BLUE}Found $TIF_COUNT .tif files directly in the input directory${NC}"
    echo -e "${YELLOW}Creating condition_1/timepoint_1/ structure and moving files${NC}"
    
    # Create the directory structure
    mkdir -p "$INPUT_DIR/condition_1/timepoint_1"
    
    # Move all .tif files into the new structure
    find "$INPUT_DIR" -maxdepth 1 -name "*.tif" -exec mv {} "$INPUT_DIR/condition_1/timepoint_1/" \;
    
    # Process files in the timepoint directory
    process_timepoint_directory "$INPUT_DIR/condition_1/timepoint_1"
    
    echo -e "${GREEN}Successfully reorganized .tif files into condition_1/timepoint_1/${NC}"
else
    # Check for subdirectories in the input dir
    if has_subdirectories "$INPUT_DIR"; then
        echo -e "${BLUE}Found subdirectories in the input directory${NC}"
        
        # Iterate through each subdirectory
        for SUBDIR in "$INPUT_DIR"/*; do
            if [[ -d "$SUBDIR" ]] && [[ "$(basename "$SUBDIR")" != "MetaData" ]]; then
                # Count .tif files in this subdirectory
                SUBDIR_TIF_COUNT=$(count_tif_files "$SUBDIR")
                
                if [[ $SUBDIR_TIF_COUNT -gt 0 ]]; then
                    # Case 2: One layer of subdirectories with .tif files
                    CONDITION_NAME=$(basename "$SUBDIR")
                    echo -e "${BLUE}Found $SUBDIR_TIF_COUNT .tif files in subdirectory: $CONDITION_NAME${NC}"
                    echo -e "${YELLOW}Creating timepoint_1/ under $CONDITION_NAME and moving files${NC}"
                    
                    # Create timepoint directory
                    mkdir -p "$SUBDIR/timepoint_1"
                    
                    # Move all .tif files into the timepoint directory
                    find "$SUBDIR" -maxdepth 1 -name "*.tif" -exec mv {} "$SUBDIR/timepoint_1/" \;
                    
                    # Process files in the timepoint directory
                    process_timepoint_directory "$SUBDIR/timepoint_1"
                    
                    echo -e "${GREEN}Successfully reorganized .tif files into $CONDITION_NAME/timepoint_1/${NC}"
                else
                    # Check if this might be a condition directory with timepoint subdirectories
                    if has_subdirectories "$SUBDIR"; then
                        CONDITION_NAME=$(basename "$SUBDIR")
                        echo -e "${BLUE}Subdirectory $CONDITION_NAME has its own subdirectories${NC}"
                        
                        # Check if any of those subdirectories have .tif files
                        TIF_FILES_FOUND=0
                        for TIMEPOINT_DIR in "$SUBDIR"/*; do
                            if [[ -d "$TIMEPOINT_DIR" ]]; then
                                TP_TIF_COUNT=$(count_tif_files "$TIMEPOINT_DIR")
                                if [[ $TP_TIF_COUNT -gt 0 ]]; then
                                    TIF_FILES_FOUND=1
                                    TP_DIR_NAME=$(basename "$TIMEPOINT_DIR")
                                    echo -e "${BLUE}Found $TP_TIF_COUNT .tif files in $TP_DIR_NAME${NC}"
                                    
                                    # Process files in the timepoint directory
                                    process_timepoint_directory "$TIMEPOINT_DIR"
                                fi
                            fi
                        done
                        
                        if [[ $TIF_FILES_FOUND -eq 1 ]]; then
                            # Case 3: Two layers of subdirectories with .tif files
                            echo -e "${GREEN}Directory structure for $CONDITION_NAME already correct (has timepoint directories)${NC}"
                        else
                            echo -e "${YELLOW}No .tif files found in timepoint directories for $CONDITION_NAME${NC}"
                        fi
                    else
                        echo -e "${YELLOW}No .tif files or subdirectories found in $CONDITION_NAME${NC}"
                    fi
                fi
            fi
        done
    else
        echo -e "${YELLOW}No .tif files or subdirectories found in the input directory${NC}"
    fi
fi

echo -e "${GREEN}Input directory preparation completed${NC}"

# Print final directory structure for verification
echo -e "${BLUE}Final directory structure:${NC}"
find "$INPUT_DIR" -type d | sort | while read -r dir; do
    # Calculate the relative depth
    depth=$(($(echo "$dir" | tr -cd '/' | wc -c) - $(echo "$INPUT_DIR" | tr -cd '/' | wc -c)))
    indent=$(printf "%$(($depth * 2))s" "")
    echo "${indent}$(basename "$dir")/"
done

# Print final TIFF files for verification
echo -e "${BLUE}Final .tif files:${NC}"
find "$INPUT_DIR" -name "*.tif" | sort | while read -r tif; do
    rel_path="${tif#$INPUT_DIR/}"
    echo "  $rel_path"
done

exit 0 