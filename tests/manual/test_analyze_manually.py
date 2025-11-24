#!/usr/bin/env python3
"""Manually test the analyze_masks function with logging."""

import sys
import logging
sys.path.insert(0, '/Users/leelab/percell')

# Set up detailed logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(levelname)s - %(name)s - %(message)s'
)

from pathlib import Path
from percell.application.imagej_tasks import analyze_masks

# Test parameters
input_dir = "/Volumes/KGW/ControlvsLSG1i_Biogenesis_Timelapses_10.20-23.2025/REP_3_control_analysis/masks"
output_dir = "/Volumes/KGW/ControlvsLSG1i_Biogenesis_Timelapses_10.20-23.2025/REP_3_control_analysis/analysis"
imagej_path = "/Applications/Fiji.app/Contents/MacOS/ImageJ-macosx"  # Adjust this path
macro_path = "/Users/leelab/percell/percell/macros/analyze_cell_masks.ijm"

print("=" * 80)
print("Testing analyze_masks manually")
print("=" * 80)
print(f"Input dir: {input_dir}")
print(f"Output dir: {output_dir}")
print(f"ImageJ path: {imagej_path}")
print(f"Macro path: {macro_path}")
print()

# Test with first group only (limit to 1 file for quick testing)
result = analyze_masks(
    input_dir=input_dir,
    output_dir=output_dir,
    imagej_path=imagej_path,
    macro_path=macro_path,
    regions=None,
    timepoints=["t00"],  # Just test first timepoint
    max_files=50,  # Limit to 50 files for faster testing
    auto_close=True,
)

print()
print("=" * 80)
print(f"Result: {result}")
print("=" * 80)

if result:
    print("SUCCESS: analyze_masks returned True")
    # Check if CSV was created
    csv_files = list(Path(output_dir).glob("*_particle_analysis.csv"))
    print(f"Found {len(csv_files)} particle_analysis CSV files")
    for csv in csv_files:
        print(f"  - {csv.name}")
else:
    print("FAILURE: analyze_masks returned False")
