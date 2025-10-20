# Migration Guide: Flexible Data Selection

This guide helps you migrate to the new flexible data selection system in PerCell.

## What Changed?

### Before (Legacy Mode)
- Required specific directory structure:
  ```
  root/
  ├── condition1/
  │   ├── timepoint1/
  │   │   └── files.tif
  │   └── timepoint2/
  │       └── files.tif
  └── condition2/
      └── timepoint1/
          └── files.tif
  ```
- Expected specific filename patterns with underscores
- Made assumptions about what "condition" means (always first-level directories)
- Required manual reorganization of microscope exports

### After (Flexible Mode - Now Default)
- Works with **any** directory structure
- Only requires project folders at first level (can be nested beyond that)
- Discovers dimensions from filenames automatically
- User defines what "condition" means (project folder, region, timepoint, etc.)
- Handles multiple filename conventions (spaces, underscores, mixed case)
- Works with microscope export formats directly (Leica, Zeiss, Nikon, etc.)

## Do I Need to Migrate?

**No!** Legacy mode still works perfectly. You should consider flexible mode if:

✅ You want to use microscope export formats directly (no reorganization)
✅ You need more flexible organization (nested directories, non-standard structures)
✅ You want to define custom groupings (use region or timepoint as condition)
✅ Your filenames have spaces or mixed naming conventions
✅ You're starting a new project

**Keep legacy mode** if:
- Your current workflow works and you don't need changes
- Your data is already organized in the legacy format
- You have automation scripts that depend on the legacy structure

## Migration Steps

### Step 1: Understand Your Current Setup

Check your current configuration:

```bash
# Look at your config file
cat config.json
```

If you see:
```json
{
  "data_selection": {
    "use_flexible_selection": false
  }
}
```

You're in legacy mode. **Flexible mode is now the default**, but your configuration overrides it.

### Step 2: Backup Your Config

Always backup before making changes:

```bash
cp config.json config.json.backup
```

### Step 3: Enable Flexible Mode

**Option A**: Remove the legacy flag (use default)
```json
{
  "data_selection": {
    // Remove or delete the line:
    // "use_flexible_selection": false
  }
}
```

**Option B**: Explicitly enable flexible mode
```json
{
  "data_selection": {
    "use_flexible_selection": true
  }
}
```

### Step 4: Test with Sample Data

Run data selection on a small test dataset first:

```bash
# Interactive mode
percell

# Or command line
python -m percell --input /path/to/sample --output /path/to/test_output
```

During the workflow, you'll see the new prompts:
```
Discovering files and dimensions...
Discovered 10 files with the following dimensions:
  project_folder: 2 unique values - ProjectA, ProjectB
  region: 3 unique values - region1, region2, region3
  channel: 2 unique values - ch00, ch01
  timepoint: 2 unique values - t0, t1
  z_index: 1 unique values - z00
```

### Step 5: Verify Results

Check that:
- ✅ All expected files were discovered
- ✅ Dimensions were correctly extracted from filenames
- ✅ Output directory structure matches expectations
- ✅ Config was saved with your selections

Example output structure:
```
output/
├── raw_data/
│   ├── ProjectA/
│   │   ├── region1_t0_ch00_z00.tif
│   │   └── region1_t0_ch01_z00.tif
│   └── ProjectB/
│       └── region1_t0_ch00_z00.tif
└── config.json
```

### Step 6: Update Your Workflow (If Needed)

If you have custom scripts that read the configuration, be aware that flexible mode saves both formats:

**Legacy format** (backward compatible):
```json
{
  "data_selection": {
    "selected_conditions": ["ProjectA", "ProjectB"],
    "selected_timepoints": ["t0", "t1"],
    "selected_regions": ["region1"],
    "analysis_channels": ["ch00", "ch01"],
    "segmentation_channel": "ch00"
  }
}
```

**Flexible format** (new):
```json
{
  "data_selection": {
    "condition_dimension": "project_folder",
    "dimension_filters": {
      "project_folder": ["ProjectA", "ProjectB"],
      "timepoint": ["t0", "t1"],
      "region": ["region1"],
      "channel": ["ch00", "ch01"]
    },
    "available_dimensions": {
      "project_folder": ["ProjectA", "ProjectB"],
      "region": ["region1", "region2", "region3"],
      "channel": ["ch00", "ch01"],
      "timepoint": ["t0", "t1"],
      "z_index": ["z00"]
    }
  }
}
```

**Both formats are saved**, so existing scripts continue to work!

## Common Migration Scenarios

### Scenario 1: Simple Legacy Structure

**Before**:
```
experiment/
├── Control/
│   ├── t0/
│   │   └── region1_ch0.tif
│   └── t1/
│       └── region1_ch0.tif
└── Treatment/
    └── t0/
        └── region1_ch0.tif
```

**After (Flexible)**: Same structure works! But now you can also:
- Flatten the structure (no timepoint directories needed)
- Use spaces in folder names
- Nest deeper if needed

**Workflow change**: None required if you keep the same structure. But you can now also put files directly in Control/Treatment folders without timepoint subdirectories.

### Scenario 2: Leica Export

**Before**: Had to manually reorganize:
```
# Microscope export (doesn't work in legacy)
leica_export/
├── Clone 1/
│   ├── 18h dTAG13_Merged_z00_ch00.tif
│   └── 18h dTAG13_Merged_z00_ch01.tif
└── Clone 2/
    └── 18h dTAG13_Merged_z00_ch00.tif

# You had to reorganize to:
reorganized/
├── Clone_1/
│   └── t0/
│       ├── 18h_dTAG13_Merged_z00_ch00.tif
│       └── 18h_dTAG13_Merged_z00_ch01.tif
└── Clone_2/
    └── t0/
        └── 18h_dTAG13_Merged_z00_ch00.tif
```

**After (Flexible)**: Use the export directly!
```
# Just point PerCell at the export directory
leica_export/
├── Clone 1/
│   ├── 18h dTAG13_Merged_z00_ch00.tif
│   └── 18h dTAG13_Merged_z00_ch01.tif
└── Clone 2/
    └── 18h dTAG13_Merged_z00_ch00.tif
```

No reorganization needed! Flexible mode handles:
- Spaces in directory names ("Clone 1")
- Spaces in filenames ("18h dTAG13")
- No timepoint directories
- Merged regions

**Workflow change**: Skip the reorganization step. Point PerCell directly at the microscope export.

### Scenario 3: Complex Nested Structure

**Before**: Not supported, had to flatten manually

**After (Flexible)**: Fully supported!
```
experiment/
├── Batch1/
│   ├── Replicate1/
│   │   ├── Controls/
│   │   │   ├── sample1_t0_ch0.tif
│   │   │   └── sample1_t0_ch1.tif
│   │   └── Treated/
│   │       └── sample1_t0_ch0.tif
│   └── Replicate2/
│       └── Controls/
│           └── sample2_t0_ch0.tif
└── Batch2/
    └── Replicate1/
        └── Controls/
            └── sample3_t0_ch0.tif
```

PerCell discovers:
- `project_folder`: Batch1, Batch2
- `region`: sample1, sample2, sample3
- `channel`: ch0, ch1
- `timepoint`: t0

You choose what "condition" means:
- Option A: Use `project_folder` (compare Batch1 vs Batch2)
- Option B: Use `region` (compare sample1 vs sample2 vs sample3)

**Workflow change**: No reorganization needed. Choose your comparison dimension interactively.

## Configuration Compatibility

### Reading Configurations

If your scripts read configuration values, they continue to work:

```python
# Legacy code (still works)
conditions = config.get('data_selection.selected_conditions')
timepoints = config.get('data_selection.selected_timepoints')
channels = config.get('data_selection.analysis_channels')

# New code (more flexible)
condition_dim = config.get('data_selection.condition_dimension', 'project_folder')
filters = config.get('data_selection.dimension_filters', {})
available = config.get('data_selection.available_dimensions', {})
```

### Writing Configurations

Flexible mode saves **both formats** automatically, so you don't need to change anything:

```python
# Old way (still works)
config.set('data_selection.selected_conditions', ['Control', 'Treatment'])

# New way (additional information)
config.set('data_selection.condition_dimension', 'project_folder')
config.set('data_selection.dimension_filters', {
    'project_folder': ['Control', 'Treatment'],
    'channel': ['ch00', 'ch01']
})
```

Both are saved, ensuring backward compatibility.

## Rollback Plan

If you encounter issues, you can easily rollback:

### Option 1: Disable Flexible Mode
```json
{
  "data_selection": {
    "use_flexible_selection": false
  }
}
```

### Option 2: Restore Backup
```bash
cp config.json.backup config.json
```

### Option 3: Reorganize Data for Legacy

If you need to go back to legacy mode permanently, reorganize your data:

```bash
# Example reorganization script
# From: project/condition1/file_t0_ch0.tif
# To: project/condition1/t0/file_ch0.tif

# Create timepoint directories
mkdir -p condition1/t0
mkdir -p condition1/t1

# Move files
mv condition1/*_t0_*.tif condition1/t0/
mv condition1/*_t1_*.tif condition1/t1/
```

Then set `use_flexible_selection: false` in your config.

## Troubleshooting

### Issue: No files discovered

**Symptoms**: PerCell reports 0 files found.

**Solutions**:
1. Verify your input directory contains `.tif` or `.tiff` files
2. Check that files are not in a directory named "raw_data" (reserved for output)
3. Ensure file extensions are `.tif` or `.tiff` (case-sensitive on some systems)
4. Verify file permissions (PerCell needs read access)

### Issue: Wrong dimensions extracted

**Symptoms**: Channels show as "ch" instead of "ch00", or timepoints missing.

**Solutions**:
1. Check filename patterns - ensure they include `ch00`, `t0`, `z00` markers
2. Verify markers use standard formats: `ch##`, `t##`, `z##` (with or without underscore)
3. Use underscores or spaces to separate: `sample_ch00.tif` not `samplech00.tif`
4. Check for mixed case - PerCell handles case-insensitive matching

Example fixes:
```bash
# Bad: markers not clear
region1ch0t0.tif → region1_ch0_t0.tif

# Bad: non-standard markers
region1_c0_time0.tif → region1_ch0_t0.tif

# Good: various valid formats
region1_ch00_t0.tif ✓
region1 ch00 t0.tif ✓
region1_CH00_T0.tif ✓
region1 Merged_z00_ch00.tif ✓
```

### Issue: Files not copied

**Symptoms**: Some files weren't copied to output directory.

**Solutions**:
1. Check the console output showing how many files matched your filters
2. Verify files match your selected dimensions (channel, timepoint, region)
3. Look for the "Copied X files" message to see actual count
4. Check the filters you selected during interactive workflow
5. Verify output directory has write permissions

Example debugging:
```
# Console output shows:
Discovered 100 files
Selected filters: project_folder=['ProjectA'], channel=['ch00']
Copied 25 files  # Expected: 50 files

# Diagnosis: Only ch00 files were copied (25), but you expected both ch00 and ch01 (50)
# Solution: Rerun and select both channels when prompted
```

### Issue: Wrong condition dimension

**Symptoms**: PerCell grouped by project folders but you wanted to group by regions.

**Solutions**:
1. When prompted "Which dimension represents your experimental conditions?", select the correct one
2. The default is `project_folder`, but you can choose any dimension
3. Your choice is saved in the config - delete the config line to be prompted again
4. Rerun data selection and choose the correct dimension

Example:
```
# Prompt:
Which dimension represents your experimental conditions?
1. project_folder: 2 unique values
2. region: 5 unique values
3. timepoint: 3 unique values

# Type: 2 (for region) or type: region
```

### Issue: Configuration not saved

**Symptoms**: Selections aren't saved to config file.

**Solutions**:
1. Verify output directory has write permissions
2. Check that config file isn't read-only
3. Ensure the data selection stage completed successfully
4. Look for error messages during the save step

### Issue: Legacy scripts broken

**Symptoms**: Custom scripts that read config values fail.

**Solutions**:
1. Use the legacy format fields - they're still saved for backward compatibility
2. Update scripts to handle both formats:
   ```python
   # Try new format first, fall back to legacy
   conditions = config.get('data_selection.dimension_filters', {}).get('project_folder')
   if not conditions:
       conditions = config.get('data_selection.selected_conditions')
   ```
3. Or disable flexible mode and use legacy mode exclusively

## FAQ

### Can I mix flexible and legacy mode?

No. Choose one mode per project. However, you can switch between modes at any time by changing the `use_flexible_selection` flag.

### Will flexible mode break my existing pipelines?

No. Flexible mode saves both the legacy and flexible configuration formats, ensuring backward compatibility. Existing scripts that read the legacy format continue to work.

### Can I use flexible mode with the CLI?

Yes! Flexible mode works in both interactive and CLI modes. The CLI prompts you for selections just like before, but with more flexibility in what you can select.

### Do I need to reorganize my data?

No! That's the whole point of flexible mode. It works with your data as-is, whether it's a Leica export, nested structure, or the old legacy format.

### What if I have multiple experiments with different structures?

Flexible mode handles this automatically. Each experiment can have a different directory structure - PerCell discovers the dimensions from each dataset independently.

### Can I still use programmatic/non-interactive selection?

Yes! Flexible mode supports programmatic selection. See the "Advanced Usage" section in [flexible_data_selection.md](flexible_data_selection.md).

### What happens to my old configs?

Old configs continue to work. Legacy format fields are read and used if present. New selections are saved in both formats.

### Is flexible mode slower?

Slightly, but negligibly. The initial file discovery scans recursively, which takes a few seconds longer for large datasets. However, the overall workflow time is comparable.

### Can I preview what will be selected before running?

Yes! During the interactive workflow, PerCell shows you:
1. How many files were discovered
2. All available dimension values
3. Your selections before processing

You can cancel and rerun if the preview doesn't match expectations.

## Getting Help

- Read the full documentation: [flexible_data_selection.md](flexible_data_selection.md)
- Check the example structures in the docs
- Run PerCell interactively and follow the prompts
- If you encounter issues, you can always rollback to legacy mode

## Summary

**Key Points**:
✅ Legacy mode still works - no migration required
✅ Flexible mode is now the default for new projects
✅ Both configuration formats are saved (backward compatible)
✅ No data reorganization needed with flexible mode
✅ Easy to switch between modes via configuration flag
✅ Rollback is simple - just change the config flag

**Recommendation**:
- **New projects**: Use flexible mode (it's the default)
- **Existing projects**: Keep using legacy mode unless you need flexibility
- **Microscope exports**: Definitely use flexible mode to avoid reorganization

**Next Steps**:
1. Read [flexible_data_selection.md](flexible_data_selection.md) for detailed usage
2. Test flexible mode on a sample dataset
3. Migrate your workflow if beneficial
4. Report any issues or questions to the development team
