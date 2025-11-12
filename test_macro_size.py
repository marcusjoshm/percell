#!/usr/bin/env python3
"""Test to see how large the generated macro file would be."""

import sys
sys.path.insert(0, '/Users/leelab/percell')

from pathlib import Path
from percell.application.imagej_tasks import find_mask_files, _normalize_path_for_imagej

# Find all mask files
input_dir = "/Volumes/KGW/ControlvsLSG1i_Biogenesis_Timelapses_10.20-23.2025/REP_3_control_analysis/masks"
groups = find_mask_files(input_dir, regions=None, timepoints=None)

for dir_path, mask_paths in list(groups.items())[:1]:  # Just check first group
    print(f"Group: {Path(dir_path).name}")
    print(f"Number of masks: {len(mask_paths)}")

    # Simulate what the macro creation does
    norm_masks = [_normalize_path_for_imagej(p) for p in mask_paths]
    masks_list = ";".join(norm_masks)

    print(f"\nMask list string length: {len(masks_list):,} characters")
    print(f"First mask path: {norm_masks[0]}")
    print(f"Average path length: {len(masks_list) / len(norm_masks):.1f} characters")

    # Check if this might be too long
    if len(masks_list) > 100000:
        print(f"\n⚠️  WARNING: Mask list is very long ({len(masks_list):,} chars)")
        print("This might cause issues with macro parameter passing")

    # Show what the full macro parameter section would look like
    csv_file = "/some/output/path.csv"
    params = (
        "// Parameters embedded from application helper\n"
        f"mask_files_list = \"{masks_list}\";\n"
        f"csv_file = \"{csv_file}\";\n"
        f"auto_close = true;\n"
    )

    print(f"\nFull parameter section length: {len(params):,} characters")
    print(f"\nFirst 500 characters of parameters:")
    print(params[:500])
    print("...")
