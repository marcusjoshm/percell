#!/usr/bin/env python3
"""Test script to see what find_mask_files returns."""

import os
import re
import glob
from pathlib import Path
from typing import Optional, List

def find_mask_files(
    input_dir: str | Path,
    regions: Optional[List[str]] = None,
    timepoints: Optional[List[str]] = None,
    max_files: int = 9999999999999,
) -> dict[str, List[str]]:
    import os, re, glob
    mask_files_by_dir: dict[str, List[str]] = {}
    target_regions: List[str] = []
    target_timepoints: List[str] = []
    total_files_collected = 0

    print(f"Input dir: {input_dir}")
    print(f"Regions filter: {regions}")
    print(f"Timepoints filter: {timepoints}")
    print()

    if regions:
        for r in regions:
            if isinstance(r, str) and " " in r:
                target_regions.extend([s.strip() for s in r.split()])
            else:
                target_regions.append(r)
    if timepoints:
        for t in timepoints:
            if isinstance(t, str) and " " in t:
                target_timepoints.extend([s.strip() for s in t.split()])
            else:
                target_timepoints.append(t)

    print(f"Target regions after processing: {target_regions}")
    print(f"Target timepoints after processing: {target_timepoints}")
    print()

    for extension in ["tif", "tiff"]:
        if total_files_collected >= max_files:
            break
        pattern = os.path.join(str(input_dir), "**", f"MASK_CELL*.{extension}")
        print(f"Searching with pattern: {pattern}")

        matches = glob.glob(pattern, recursive=True)
        print(f"Found {len(matches)} total MASK_CELL*.{extension} files")

        for mask_path in matches[:3]:  # Show first 3 for debugging
            print(f"  Processing: {mask_path}")
            parent_dir = os.path.dirname(mask_path)
            dir_name = os.path.basename(parent_dir)
            print(f"    Parent dir: {parent_dir}")
            print(f"    Dir name: {dir_name}")

            region = None
            timepoint = None
            m = re.match(r"(R_\d+)_(t\d+)", dir_name)
            if m:
                region = m.group(1)
                timepoint = m.group(2)
                print(f"    Matched pattern 1: region={region}, timepoint={timepoint}")
            elif "_" in dir_name:
                m2 = re.match(r"(.+?)_(t\d+)$", dir_name)
                if m2:
                    region = m2.group(1)
                    timepoint = m2.group(2)
                    print(f"    Matched pattern 2: region={region}, timepoint={timepoint}")
            if region is None or timepoint is None:
                tp = re.search(r"(t\d+)", dir_name)
                if tp:
                    timepoint = tp.group(1)
                    left = dir_name.split(timepoint)[0].strip("_")
                    region = left or None
                    print(f"    Matched fallback: region={region}, timepoint={timepoint}")

            if region is None or timepoint is None:
                print(f"    SKIPPED: Could not extract region/timepoint")
                continue

            if target_regions:
                match_found = any(region in tr or tr in region for tr in target_regions)
                print(f"    Region filter check: {match_found}")
                if not match_found:
                    print(f"    SKIPPED: Region '{region}' not in target regions {target_regions}")
                    continue

            if target_timepoints and timepoint not in target_timepoints:
                print(f"    SKIPPED: Timepoint '{timepoint}' not in target timepoints {target_timepoints}")
                continue

            # Check if we've reached the maximum number of files
            if total_files_collected >= max_files:
                break

            files = mask_files_by_dir.setdefault(parent_dir, [])
            files.append(mask_path)
            total_files_collected += 1
            print(f"    ADDED to group. Total files: {total_files_collected}")

    print()
    print(f"SUMMARY: Found {len(mask_files_by_dir)} groups with {total_files_collected} total files")
    for dir_path, files in mask_files_by_dir.items():
        print(f"  {dir_path}: {len(files)} files")

    return mask_files_by_dir


# Test with a sample path - MODIFY THIS PATH
test_dir = "/Volumes/KGW/ControlvsLSG1i_Biogenesis_Timelapses_10.20-23.2025/REP_3_control_analysis/masks"

if os.path.exists(test_dir):
    # Test with no filters first
    print("=" * 80)
    print("TEST 1: No filters")
    print("=" * 80)
    result = find_mask_files(test_dir)

    # Now test with some regions/timepoints - adjust these based on what you expect
    print("\n" + "=" * 80)
    print("TEST 2: With example filters")
    print("=" * 80)
    result2 = find_mask_files(
        test_dir,
        regions=["Ctrl_As_Treatment_60min_Merged"],
        timepoints=["t00", "t01"]
    )
else:
    print(f"ERROR: Test directory does not exist: {test_dir}")
    print("Please modify the test_dir variable in this script to point to your actual masks directory")
