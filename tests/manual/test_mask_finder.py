#!/usr/bin/env python3
"""Test script to diagnose why find_mask_files isn't finding masks."""

import re

# Test the regex patterns from find_mask_files
dir_name = "Ctrl_As_Treatment_60min_Merged_ch00_t00"

print(f"Testing directory name: {dir_name}")
print()

# Pattern 1: R_\d+_t\d+
m1 = re.match(r"(R_\d+)_(t\d+)", dir_name)
print(f"Pattern 1 - r'(R_\\d+)_(t\\d+)': {m1}")

# Pattern 2: (.+?)_(t\d+)$
m2 = re.match(r"(.+?)_(t\d+)$", dir_name)
print(f"Pattern 2 - r'(.+?)_(t\\d+)$': {m2}")
if m2:
    print(f"  Region: '{m2.group(1)}'")
    print(f"  Timepoint: '{m2.group(2)}'")

# Fallback pattern: search for t\d+
tp = re.search(r"(t\d+)", dir_name)
print(f"Fallback - r'(t\\d+)': {tp}")
if tp:
    print(f"  Timepoint: '{tp.group(1)}'")
    left = dir_name.split(tp.group(1))[0].strip("_")
    print(f"  Region: '{left}'")
