# Quick Start Guide

## Installation

```bash
# Clone and install
git clone https://github.com/marcusjoshm/percell.git
cd percell
./install
```

## Usage

After installation, you can run Percell from **any directory**:

```bash
# Run from anywhere
percell

# Run with specific options
percell --help
percell --interactive
percell --input /path/to/data --output /path/to/output --complete-workflow
```

## Interactive Menu

When you run `percell`, you'll see the interactive menu:

```
         ███████╗ ████████╗███████╗ ███████╗████████╗██╗      ██╗
         ██╔═══██╗██╔═════╝██╔═══██╗██╔════╝██╔═════╝██║      ██║
         ███████╔╝███████╗ ███████╔╝██║     ███████╗ ██║      ██║
         ██╔════╝ ██╔════╝ ██╔═══██╗██║     ██╔════╝ ██║      ██║
         ██║      ████████╗██║   ██║███████╗████████╗████████╗████████╗
         ╚═╝      ╚═══════╝╚═╝   ╚═╝╚══════╝╚═══════╝╚═══════╝╚═══════╝

  🔬 Welcome single-cell microscopy analysis user! 🔬

MENU:
1. Set Input/Output Directories
2. Run Complete Workflow
3. Data Selection (conditions, regions, timepoints, channels)
4. Single-cell Segmentation (Cellpose)
5. Process Single-cell Data (tracking, resizing, extraction, grouping)
6. Threshold Grouped Cells (interactive ImageJ thresholding)
7. Measure Cell Area (measure areas from single-cell ROIs)
8. Analysis (combine masks, create cell masks, export results)
9. Exit
```

## Recommended Workflow

For new users, we recommend:

1. **Option 2: Run Complete Workflow** - This runs all steps automatically
2. Follow the prompts for data selection
3. Complete the interactive segmentation step
4. Wait for processing to complete

## Data Requirements

Your input directory should be organized as:

```
input_directory/
├── condition_1/
│   ├── timepoint_1/
│   │   ├── region_1/
│   │   │   ├── channel_1.tif
│   │   │   ├── channel_2.tif
│   │   │   └── channel_3.tif
│   │   └── region_2/
│   │       ├── channel_1.tif
│   │       ├── channel_2.tif
│   │       └── channel_3.tif
│   └── timepoint_2/
└── condition_2/
```

## Troubleshooting

- **Command not found**: Run `./install` again
- **Permission errors**: Make sure `/usr/local/bin` is writable
- **Path issues**: The app now handles paths automatically

## More Information

- [Full Documentation](DOCUMENTATION.md)
- [Global Installation Guide](GLOBAL_INSTALLATION.md)
- [Centralized Path System](CENTRALIZED_PATHS.md)
