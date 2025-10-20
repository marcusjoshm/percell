# Flexible Data Selection

PerCell now supports flexible file organization! You no longer need to organize your microscopy data in a specific directory structure.

## Requirements

The only hard requirement is:
- **Root directory contains project folders** (first level subdirectories)
- **Files follow basic naming conventions** with identifiable channels, timepoints, and z-slices

## Supported Naming Conventions

PerCell automatically recognizes these patterns in filenames:

### Channels
- `ch00`, `ch01`, `ch02`, ... (case insensitive)
- `_ch0`, `_ch1`, `_ch2`, ...
- Can appear anywhere in the filename
- Examples: `data_ch00.tif`, `sample ch01.tif`, `experimentCH00.tif`

### Timepoints
- `t0`, `t1`, `t2`, ... (case insensitive)
- `_t0`, `_t1`, `_t2`, ...
- Can appear anywhere in the filename
- Examples: `data_t0.tif`, `sample t1.tif`, `experimentT00.tif`

### Z-slices
- `z00`, `z01`, `z02`, ... (case insensitive)
- `_z0`, `_z1`, `_z2`, ...
- Can appear anywhere in the filename
- Examples: `data_z00.tif`, `sample z01.tif`, `experimentZ00.tif`

### Region Names
- Any text not matching channel/timepoint/z-slice patterns becomes the region name
- Supports spaces, hyphens, and underscores
- Examples:
  - `18h dTAG13_Merged_z00_ch00.tif` → region: "18h dTAG13_Merged"
  - `region1_t0_ch0.tif` → region: "region1"
  - `My Experiment_ch00.tif` → region: "My Experiment"

## Example Directory Structures

### Leica Export Style
```
my_experiment/
├── Project A/
│   ├── 18h treatment_Merged_z00_ch00.tif
│   ├── 18h treatment_Merged_z00_ch01.tif
│   ├── 3h treatment_Merged_z00_ch00.tif
│   └── 3h treatment_Merged_z00_ch01.tif
└── Project B/
    ├── 18h treatment_Merged_z00_ch00.tif
    └── 18h treatment_Merged_z00_ch01.tif
```

### Standard Naming
```
my_experiment/
├── Control/
│   ├── region1_t0_ch0_z0.tif
│   ├── region1_t0_ch1_z0.tif
│   └── region1_t1_ch0_z0.tif
└── Treatment/
    ├── region1_t0_ch0_z0.tif
    └── region1_t0_ch1_z0.tif
```

### Nested Structure
```
my_experiment/
├── Experiment1/
│   ├── Replicate1/
│   │   ├── data_t0_ch0.tif
│   │   └── data_t0_ch1.tif
│   └── Replicate2/
│       └── data_t0_ch0.tif
└── Experiment2/
    └── data_t0_ch0.tif
```

All three structures work without any reorganization!

## How It Works

1. **File Discovery**: PerCell scans your root directory recursively for all `.tif` and `.tiff` files

2. **Metadata Extraction**: For each file, PerCell extracts:
   - Project folder (first directory level)
   - Region/dataset name (base filename without ch/t/z markers)
   - Channel, timepoint, and z-slice from filename patterns

3. **Dimension Discovery**: PerCell identifies all unique values for each dimension:
   - Project folders
   - Regions (unique base filenames)
   - Channels
   - Timepoints
   - Z-slices

4. **Interactive Selection**: You choose:
   - Which dimension represents your "conditions" (usually project folders)
   - Which conditions to analyze
   - Which channels, timepoints, and regions to include

5. **Smart Filtering**: Files are filtered and copied based on your selections

## Interactive Workflow

When you run data selection, you'll be guided through these steps:

### Step 1: File Discovery
PerCell scans your input directory and displays what it found:
```
Discovering files and dimensions...
Discovered 8 files with the following dimensions:
  project_folder: 2 unique values - ProjectA, ProjectB
  region: 4 unique values - 18h treatment_Merged, 3h treatment_Merged, No treatment_Merged
  channel: 2 unique values - ch00, ch01
  timepoint: none found
  z_index: 1 unique values - z00
```

### Step 2: Define Conditions
Choose which dimension represents your experimental conditions:
```
Which dimension represents your experimental conditions?

Available dimensions:
1. project_folder: 2 unique values - ProjectA, ProjectB
2. region: 4 unique values - 18h treatment_Merged, 3h treatment_Merged, ...
3. channel: 2 unique values - ch00, ch01

Enter dimension number or name (default: project_folder): 1
```

**Tip**: Usually project folders represent your conditions, but you can choose any dimension!

### Step 3: Select Conditions
Choose which condition values to analyze:
```
Select project_folders to analyze:
1. ProjectA
2. ProjectB

Enter selection (numbers, names, or 'all'): all
```

**Selection formats**:
- Numbers: `1,2` or `1-3`
- Names: `ProjectA,ProjectB`
- All: `all`

### Step 4: Select Channels
Choose segmentation and analysis channels:
```
Select the channel for SEGMENTATION:
1. ch00
2. ch01

Enter selection: 1

Select channels for ANALYSIS (can include multiple):
1. ch00
2. ch01

Enter selection: all
```

**Note**: The segmentation channel is used to create cell masks. Analysis channels are the channels you want to measure.

### Step 5: Select Timepoints (if applicable)
If your data has timepoints, choose which to include:
```
Available timepoints: t0, t1, t2

Enter selection (or 'all' for all timepoints, 'none' to skip): all
```

If no timepoints are found, this step is skipped automatically.

### Step 6: Select Regions (optional)
Choose specific regions/datasets to include:
```
Available regions:
1. 18h treatment_Merged
2. 3h treatment_Merged
3. No treatment_Merged

Enter selection (or 'all' for all regions): all
```

### Step 7: File Processing
PerCell creates output directories and copies filtered files:
```
Creating output directory structure...
Created: /path/to/output/raw_data/ProjectA
Created: /path/to/output/raw_data/ProjectB

Copying filtered files...
Copied 100 files (logging every 50 files)...
Done! Files copied to raw_data directories.
```

## Configuration

Flexible data selection is **enabled by default**. Your selections are saved in the configuration file for future runs.

### Switching to Legacy Mode

If you need the old behavior (hardcoded directory structure), you can disable flexible mode:

```python
# In your config file or via API
config.set('data_selection.use_flexible_selection', False)
```

Or via command line:
```bash
# Edit your config.json
{
  "data_selection": {
    "use_flexible_selection": false
  }
}
```

### Configuration Storage

After data selection, your choices are saved in two formats:

**Legacy format** (backward compatible):
```json
{
  "data_selection": {
    "selected_conditions": ["ProjectA", "ProjectB"],
    "selected_timepoints": [],
    "selected_regions": ["18h treatment_Merged", "3h treatment_Merged"],
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
      "channel": ["ch00", "ch01"],
      "region": ["18h treatment_Merged", "3h treatment_Merged"]
    },
    "available_dimensions": {
      "project_folder": ["ProjectA", "ProjectB"],
      "region": ["18h treatment_Merged", "3h treatment_Merged", "No treatment_Merged"],
      "channel": ["ch00", "ch01"],
      "z_index": ["z00"]
    }
  }
}
```

Both formats are saved to ensure backward compatibility.

## Troubleshooting

### No files discovered
**Problem**: PerCell reports 0 files discovered.

**Solutions**:
- Verify your input directory contains `.tif` or `.tiff` files
- Check that files are not in a subdirectory named exactly "raw_data" (which is reserved for output)
- Ensure file extensions are lowercase `.tif` or `.tiff` (or use case-insensitive filesystem)

### Wrong region names extracted
**Problem**: Region names include channel/timepoint markers.

**Solutions**:
- Ensure channel markers use standard patterns: `ch00`, `_ch0`, etc.
- Ensure timepoint markers use standard patterns: `t0`, `_t0`, etc.
- Use underscores or spaces to separate metadata: `region_ch00.tif` not `regionch00.tif`

### Files not copied
**Problem**: Some files weren't copied during data selection.

**Solutions**:
- Check that files match your selected filters (channels, timepoints, regions)
- Look at the console output showing how many files matched your criteria
- Verify the files exist in the input directory

### Wrong dimension as condition
**Problem**: PerCell defaulted to the wrong dimension for experimental conditions.

**Solutions**:
- When prompted "Which dimension represents your experimental conditions?", choose the correct dimension
- The default is `project_folder`, but you can select any dimension (region, channel, etc.)
- Your choice is saved in the config for future runs

## Advanced Usage

### Programmatic Selection

You can configure data selection programmatically without interactive prompts:

```python
from percell.application.stages.data_selection_stage import DataSelectionStage
from percell.domain.services.configuration_service import ConfigurationService
import logging

# Setup
config = ConfigurationService(Path("config.json"))
config.load(create_if_missing=True)
config.set('data_selection.use_flexible_selection', True)
logger = logging.getLogger(__name__)

# Create stage
stage = DataSelectionStage(config, logger)
stage.input_dir = Path("/path/to/microscopy/export")
stage.output_dir = Path("/path/to/output")

# Discover files
stage._discover_files_and_dimensions()

# Make programmatic selections
stage.condition_dimension = 'project_folder'
stage.selected_conditions = ['ProjectA', 'ProjectB']
stage.analysis_channels = ['ch00', 'ch01']
stage.segmentation_channel = 'ch00'
stage.selected_timepoints = []  # Empty = all or none
stage.selected_regions = []  # Empty = all

# Execute
stage._create_flexible_output_directories()
stage._copy_filtered_files()
stage._save_flexible_selections_to_config()
```

### Custom Dimension as Condition

You can use any dimension as your "condition" dimension:

**Example 1**: Use regions as conditions (if you have multiple experiments in one project folder)
```
Which dimension represents your experimental conditions?
Enter dimension number or name (default: project_folder): region
```

**Example 2**: Use timepoints as conditions (for time-series analysis)
```
Which dimension represents your experimental conditions?
Enter dimension number or name (default: project_folder): timepoint
```

This flexibility allows you to analyze your data however it's organized!

## Migration from Legacy Mode

See [MIGRATION_FLEXIBLE_SELECTION.md](MIGRATION_FLEXIBLE_SELECTION.md) for detailed migration instructions.

## Benefits

✅ **No reorganization required**: Work with Leica, Zeiss, Nikon exports as-is
✅ **Flexible naming**: Handles spaces, underscores, mixed case
✅ **Nested structures**: Scans recursively, finds files anywhere
✅ **User-defined grouping**: You choose what represents "conditions"
✅ **Backward compatible**: Legacy mode still available if needed
✅ **Saved preferences**: Your selections are remembered in the config

## Questions?

- Check [MIGRATION_FLEXIBLE_SELECTION.md](MIGRATION_FLEXIBLE_SELECTION.md) for migration help
- Review the example directory structures above
- Run PerCell and follow the interactive prompts - they're designed to guide you!
