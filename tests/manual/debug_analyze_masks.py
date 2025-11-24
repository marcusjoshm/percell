#!/usr/bin/env python3
"""Debug script to test analyze_masks with actual parameters."""

import sys
sys.path.insert(0, '/Users/leelab/percell')

from pathlib import Path
from percell.application.imagej_tasks import find_mask_files

# Test with the actual directory
input_dir = "/Volumes/KGW/ControlvsLSG1i_Biogenesis_Timelapses_10.20-23.2025/REP_3_control_analysis/masks"

print("=" * 80)
print("Testing find_mask_files with NO filters (should find all)")
print("=" * 80)

groups = find_mask_files(input_dir, regions=None, timepoints=None)

print(f"\nFound {len(groups)} groups:")
for dir_path, mask_list in groups.items():
    print(f"  {Path(dir_path).name}: {len(mask_list)} masks")

print(f"\nTotal masks across all groups: {sum(len(v) for v in groups.values())}")

if not groups:
    print("\nERROR: No groups found! This is the problem.")
    print("The analyze_masks function will return False because groups is empty.")
else:
    print("\nSUCCESS: Groups found, so the issue must be with ImageJ execution or macro creation.")

# Now test with some potential filter values
print("\n" + "=" * 80)
print("Testing with potential filter values")
print("=" * 80)

# Try with common region patterns
test_regions = [
    None,
    ["Ctrl_As_Treatment_60min_Merged"],
    ["Ctrl_As_Treatment_60min_Merged_ch00"],
]

test_timepoints = [
    None,
    ["t00", "t01", "t02"],
]

for regions in test_regions:
    for timepoints in test_timepoints:
        groups = find_mask_files(input_dir, regions=regions, timepoints=timepoints)
        total = sum(len(v) for v in groups.values())
        print(f"regions={regions}, timepoints={timepoints}: {len(groups)} groups, {total} total masks")
