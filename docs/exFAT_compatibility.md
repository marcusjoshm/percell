# exFAT Filesystem Compatibility

## Overview

This document explains how Percell handles compatibility issues when running on macOS with exFAT-formatted external drives.

## The Problem

When macOS writes files to non-native filesystems like exFAT (commonly used for external hard drives that need to work with both macOS and Windows), it automatically creates hidden metadata files with a `._` prefix for every file and directory. These metadata files store:

- Extended file attributes
- Resource forks
- Other macOS-specific metadata

### Example

If you have a file named `mydata.tif` on an exFAT drive, macOS will automatically create:
- `mydata.tif` (the actual file)
- `._mydata.tif` (the hidden metadata file)

Similarly, for directories named `condition_1`, macOS creates:
- `condition_1/` (the actual directory)
- `._condition_1/` (the hidden metadata directory)

## Impact on Percell

Without filtering, these `._ ` files cause several problems in the analysis pipeline:

1. **Duplicate File Processing**: The pipeline would try to process both the real file and the metadata file
2. **File Matching Errors**: When matching ROI files to image files, the metadata files create incorrect matches
3. **Invalid File Format Errors**: Trying to open `._myfile.tif` as an image fails because it's not actually an image file
4. **Spurious Output Files**: The pipeline would create output files like `._result.csv` that shouldn't exist

## The Solution

Percell now includes a centralized filtering system to automatically ignore these files throughout the pipeline:

### Utility Module

Located at `percell/domain/utils/filesystem_filters.py`, this module provides:

- `is_exfat_metadata_file(path)` - Checks if a file has the `._` prefix
- `is_system_hidden_file(path)` - Comprehensive check for all system metadata files
- `filter_system_files(paths)` - Filters a list of paths

### Applied Throughout the Pipeline

The filtering is applied at all file discovery points:

1. **Data Selection Stage** (`data_selection_stage.py`)
   - Filters directory listings when scanning conditions and timepoints
   - Filters files during copy operations

2. **ImageJ Tasks** (`imagej_tasks.py`)
   - Filters ROI zip files
   - Filters image files during matching
   - Filters mask files

3. **Image Processing** (`image_processing_tasks.py`)
   - Filters mask files during combine operations
   - Filters cell image files during grouping
   - Filters CSV files during analysis

4. **Measurement Stage** (`measure_roi_area_stage.py`)
   - Filters CSV output files

## For Developers

### When Adding New File Operations

When writing code that discovers or lists files, always apply filtering:

```python
from percell.domain.utils.filesystem_filters import is_system_hidden_file

# Bad - will include ._ files
files = list(directory.glob("*.tif"))

# Good - filters out ._ files
files = [f for f in directory.glob("*.tif") if not is_system_hidden_file(f)]
```

### When Checking Directories

Also filter when iterating over directories:

```python
# Bad
for subdir in parent_dir.iterdir():
    if subdir.is_dir():
        process(subdir)

# Good
for subdir in parent_dir.iterdir():
    if subdir.is_dir() and not is_system_hidden_file(subdir):
        process(subdir)
```

## Testing

When testing on exFAT drives, you can manually verify the filtering works by:

1. Check the log output - you should not see any `._` files mentioned
2. Check output directories - you should not see any `._` files created
3. Run the full pipeline - it should complete without file format errors

## Other Metadata Files

The filtering system also handles:

- `__MACOSX/` directories (created by macOS when creating zip files)
- Other system-specific metadata patterns (can be extended in `filesystem_filters.py`)

## References

- [Apple Technical Note on ._AppleDouble Files](https://support.apple.com/en-us/HT1629)
- [exFAT Specification](https://docs.microsoft.com/en-us/windows/win32/fileio/exfat-specification)
