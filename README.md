# PerCell

<img src="percell/art/percell_terminal_window.png?v=3" width="900" title="Percell Terminal Interface" alt="Percell Terminal Interface" align="center">

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![repo size](https://img.shields.io/github/repo-size/marcusjoshm/percell)](https://github.com/marcusjoshm/percell/)
[![License: MIT](https://img.shields.io/github/license/marcusjoshm/percell)](https://github.com/marcusjoshm/percell/blob/main/LICENSE)
[![Contributors](https://img.shields.io/github/contributors-anon/marcusjoshm/percell)](https://github.com/marcusjoshm/percell/graphs/contributors)

**A comprehensive single-cell microscopy analysis tool** that integrates Cellpose segmentation with ImageJ macros into a unified command-line interface. Built with clean hexagonal architecture for reliability and extensibility.

## Table of Contents

1. [Quick Start](#quick-start)
2. [Typical Use Case](#typical-use-case)
3. [Workflow Flexibility and Reanalysis](#workflow-flexibility-and-reanalysis)
4. [Installation](#installation)
5. [Running PerCell](#running-percell)
6. [Input Directory Structure](#input-directory-structure)
7. [Using the Interactive Menu](#using-the-interactive-menu)
8. [Complete Workflow (Option 2)](#complete-workflow-option-2)
9. [Individual Menu Options](#individual-menu-options)
10. [Advanced Workflow Builder (Option 10)](#advanced-workflow-builder-option-10)
11. [Troubleshooting](#troubleshooting)
12. [Architecture](#architecture)

## Quick Start

1. **Install PerCell**:
   ```bash
   git clone https://github.com/marcusjoshm/percell.git
   cd percell
   ./install
   ```

2. **Run from anywhere**:
   ```bash
   percell
   ```

3. **Set Input/Output directories for your dataset** (Configuration → I/O):
   - Input: Point to your microscope-exported .tif files
   - Output: Specify path for new analysis directory (PerCell creates it)
   - Required for each new experiment/dataset

4. **Run complete analysis** (Workflows → Default Workflow):
   - Comprehensive workflow for most datasets
   - Best starting point for new datasets

## Typical Use Case

**Scenario**: You've performed fluorescence microscopy and want to analyze a specific cellular feature.

### 1. **Data Preparation**
- Export your data from the microscope as **.tif files**
- Organize directory structure to match PerCell requirements:
  ```
  your_experiment/
  ├── condition_1/
  │   └── timepoint_1/
  │       └── region_1/
  │           ├── DAPI.tif      # Nuclear stain
  │           ├── GFP.tif       # Feature of interest
  │           └── RFP.tif       # Additional channel
  ```
- Remove spaces and special characters from all file/folder names

### 2. **Start Analysis**
- Run `percell` from any terminal
- **Configuration → I/O**: Set directories
  - Input: Point to your organized microscope data
  - Output: Specify path for new analysis directory
- **Workflows → Default Workflow**: Run Complete Workflow

### 3. **Data Selection Phase**
You'll be prompted to select:
- **Experimental conditions** first layer, typically the experimental condition
- **Time points** for datasets with multiple timepoints for a given condition or time-lapse microscopy datasets
- **Regions/fields** technical replicates for a given condition and timepoint
- **Segmentation channel** (e.g., DAPI for nuclear segmentation)
- **Analysis channel** (e.g., GFP for your feature of interest)

### 4. **Interactive Analysis**

**First Interactive Step - Cell Segmentation:**
- Cellpose GUI opens automatically
- Use the SAM model for automated segmentation or use the manual ROI drawing tool
- PerCell uses your segmentation to extract single cells
- Cells are automatically grouped by expression intensity for enhanced intensity-based autothresholding. This is particularly useful for datasets with high variability in intensity from cell to cell

**Second Interactive Step - Feature Thresholding:**
- ImageJ opens with your grouped cell images
- **Draw circular ROI** around your feature of interest to guide auto-thresholding
- PerCell applies automated intensity-based thresholding
- Creates binary masks for quantitative analysis

### 5. **Results**
- Individual cell masks and measurements
- Combined analysis across all cells
- CSV files with quantitative data
- Preserved metadata for reproducibility

## Workflow Flexibility and Reanalysis

**If you need to pause and resume**: Use individual menu options through their respective categories to continue from where you left off, allowing you to work on long analyses across multiple sessions.

**If you need to correct or refine your analysis**:
- **Refine thresholding results?** → Use Analysis → Threshold Grouped Cells + Analysis → Particle Analysis
- **Analyze different data subsets?** → Use Configuration → Analysis Parameters + subsequent steps
- **Custom analysis sequence needed?** → Use Workflows → Advanced Workflow Builder

**Example Reanalysis Scenarios**:
```
# Refine thresholding with different ROI selection:
Analysis → Threshold Grouped Cells → Analysis → Particle Analysis

# Reanalyze with different data subset or parameters:
Configuration → Analysis Parameters → Segmentation → Cellpose → Processing → Single-Cell Data Processing → Analysis → Threshold Grouped Cells → Analysis → Particle Analysis

# Custom reanalysis sequence using Advanced Workflow:
Workflows → Advanced Workflow Builder → Select: threshold_grouped_cells → analysis
```

## Installation

### Automatic Installation (Recommended)

```bash
# Clone the repository
git clone https://github.com/marcusjoshm/percell.git
cd percell

# Single command installation
./install
```

**What the installer does:**
- ✅ Creates Python virtual environments (main + Cellpose)
- ✅ Installs all dependencies (NumPy, SciPy, tifffile, etc.)
- ✅ Installs package in development mode
- ✅ Detects ImageJ/Fiji installation paths
- ✅ Creates configuration files
- ✅ Sets up global `percell` command
- ✅ Verifies installation

### Troubleshooting Installation

If `percell` command is not found after installation:

```bash
# From the project directory
./percell/setup/fix_global_install.sh
```

**Common issues:**
- **Permission denied**: Installation script needs permission to create symlink in `/usr/local/bin`
- **Command not found**: Virtual environment path may not be correctly linked
- **Dependencies missing**: Run `pip install -e .` from project directory

## Running PerCell

Once installed, **run PerCell from any directory**:

```bash
# Interactive menu (recommended)
percell

# Get help
percell --help

# Direct command line usage
percell --input /path/to/data --output /path/to/results --complete-workflow
```

**Global Command Benefits:**
- ✅ Works from any terminal location
- ✅ No need to navigate to project folder
- ✅ No manual virtual environment activation
- ✅ Consistent across different sessions

## Input Directory Structure

PerCell is designed to analyze **microscope-exported .tif files** and requires a specific hierarchical directory structure for your data:

### Multi-timepoint Experiments
```
input_directory/
├── condition_1/              # Experimental conditions
│   ├── timepoint_1/           # Time points
│   │   ├── region_1/          # Regions/fields
│   │   │   ├── channel_1.tif  # Individual channels
│   │   │   ├── channel_2.tif
│   │   │   └── channel_3.tif
│   │   └── region_2/
│   │       ├── channel_1.tif
│   │       ├── channel_2.tif
│   │       └── channel_3.tif
│   └── timepoint_2/
│       └── region_1/
│           ├── channel_1.tif
│           ├── channel_2.tif
│           └── channel_3.tif
└── condition_2/
    ├── timepoint_1/
    │   └── region_1/
    │       ├── channel_1.tif
    │       ├── channel_2.tif
    │       └── channel_3.tif
    └── timepoint_2/
        └── region_1/
            ├── channel_1.tif
            ├── channel_2.tif
            └── channel_3.tif
```

### Single-timepoint Experiments
```
input_directory/
├── condition_1/              # Experimental conditions
│   ├── region_1/              # Regions/fields (no timepoint level)
│   │   ├── DAPI.tif          # Channel files
│   │   ├── GFP.tif
│   │   └── RFP.tif
│   └── region_2/
│       ├── DAPI.tif
│       ├── GFP.tif
│       └── RFP.tif
└── condition_2/
    └── region_1/
        ├── DAPI.tif
        ├── GFP.tif
        └── RFP.tif
```

### File Naming Requirements

**✅ Required:**
- **No spaces** in file or directory names (use underscores)
- **No special characters** like `+`, `&`, `%`, etc.
- **Consistent naming** across all levels
- **TIFF format** (`.tif` or `.tiff`)

**✅ Examples of good names:**
- `Control_Treatment`, `DAPI.tif`, `Region_1`, `0min`

**❌ Examples of bad names:**
- `Control Treatment`, `DAPI + GFP.tif`, `Region #1`, `0 min`

## Using the Interactive Menu

When you run `percell`, you'll see the colorful multi-layer interactive menu system:

```
    ███████╗ ████████╗███████╗ ███████╗████████╗██╗      ██╗
    ██╔═══██╗██╔═════╝██╔═══██╗██╔════╝██╔═════╝██║      ██║
    ███████╔╝███████╗ ███████╔╝██║     ███████╗ ██║      ██║
    ██╔════╝ ██╔════╝ ██╔═══██╗██║     ██╔════╝ ██║      ██║
    ██║      ████████╗██║   ██║███████╗████████╗████████╗████████╗
    ╚═╝      ╚═══════╝╚═╝   ╚═╝╚══════╝╚═══════╝╚═══════╝╚═══════╝

🔬 Welcome single-cell microscopy analysis user! 🔬

MAIN MENU:
1.  Configuration - Set input/output directories and analysis parameters
2.  Workflows - Pre-built and custom analysis workflows
3.  Segmentation - Single-cell segmentation tools
4.  Processing - Data processing for downstream analysis
5.  Tracking - Single-cell tracking tools
6.  Visualization - Image and mask visualization tools
7.  Analysis - Semi-automated thresholding and image analysis tools
8.  Plugins - Extend functionality with plugins
9.  Utilities - Cleanup and maintenance tools
10. Exit - Quit the application
```

### Navigation and Menu Structure

The new multi-layer menu system organizes functionality into logical categories for better usability:

#### Main Menu Categories

**1. Configuration Menu**
```
CONFIGURATION MENU:
1. I/O - Set input/output directories
2. Analysis Parameters - Select conditions, timepoints, channels, etc. for
   processing and analysis
3. Current Configuration - View current analysis configuration
4. Back to Main Menu
```

**2. Workflows Menu**
```
WORKFLOWS MENU:
1. Default Workflow - Complete sequence of steps from segmentation to particle analysis
2. Advanced Workflow Builder - Select specific steps to include in a custom workflow
3. Back to Main Menu
```

**3. Segmentation Menu**
```
SEGMENTATION MENU:
1. Cellpose - Single-cell segmentation using Cellpose SAM GUI
2. Back to Main Menu
```

**4. Processing Menu**
```
PROCESSING MENU:
1. Single-Cell Data Processing - Tracking, resizing, extraction, grouping
2. Back to Main Menu
```

**5. Analysis Menu**
```
ANALYSIS MENU:
1. Threshold Grouped Cells - interactive Otsu autothresholding of intensity grouped cell data with imageJ
2. Measure Cell Area - Measure area of cells in ROIs using imageJ
3. Particle Analysis - Analyze particles in segmented images using imageJ
4. Back to Main Menu
```

**6. Plugins Menu**
```
PLUGINS MENU:
1. Auto Image Preprocessing - auto preprocessing for downstream analysis
2. Back to Main Menu
```

**7. Utilities Menu**
```
UTILITIES MENU:
1. Cleanup - Delete intermediate files (individual cells and masks) to save space
2. Back to Main Menu
```

### Setting Up Your Analysis (Configuration → I/O)

**Required for every new dataset** - Navigate to Configuration menu and select I/O:

```
Select an option (1-10): 1  # Configuration
Select an option (1-4): 1   # I/O Setup
```

**Input Directory Setup:**
- Point to the directory containing **microscope-exported .tif files**
- This is your raw data directory from the microscope
- Must follow the hierarchical structure (condition/timepoint/region/channel)
- Example: `/Users/yourname/microscope_data/experiment_2024_01/`

**Output Directory Setup:**
- Specify the **path for a NEW directory** that will be created by PerCell
- This directory does not need to exist - PerCell will create it
- All analysis files, results, and processed data will be saved here
- Example: `/Users/yourname/analysis_results/experiment_2024_01_analysis/`

**Important Notes:**
- ✅ Input directory contains your original microscope data (existing)
- ✅ Output directory will be created by PerCell (new)
- ✅ Must set directories for each new dataset you analyze
- ✅ Paths are saved for the current analysis session

## Complete Workflow (Workflows → Default Workflow)

**⭐ Best starting point for new datasets** - Comprehensive workflow useful for most fluorescence microscopy analyses.

```
Select an option (1-10): 2  # Workflows
Select an option (1-3): 1   # Default Workflow
```

### What the Default Workflow Does:

1. **Analysis Parameters** → Interactive selection of:
   - Experimental conditions to analyze
   - Time points to include
   - Regions/fields to process
   - Channels for segmentation and analysis

2. **Single-cell Segmentation** →
   - Prepares images for Cellpose
   - Launches Cellpose and ImageJ for interactive cell segmentation
   - Saves ROI files for each region

3. **Process Single-cell Data** →
   - Tracks ROIs across timepoints (if multi-timepoint)
   - Resizes ROIs to match original image dimensions
   - Extracts individual cell images
   - Groups cells by brightness/expression levels

4. **Threshold Grouped Cells** →
   - Opens ImageJ for interactive thresholding
   - Apply Gaussian blur and contrast enhancement
   - Create binary masks using Otsu thresholding
   - User draws ROIs for representative thresholding areas

5. **Measure Cell Area** →
   - Measures areas of ROIs in original images
   - Provides quantitative size analysis

6. **Analysis** →
   - Combines masks from different groups
   - Creates individual cell masks
   - Exports comprehensive results with metadata
   - Generates CSV files with measurements

### User Interaction Points:

- **Analysis Parameters**: Choose which data to analyze
- **Segmentation**: Draw cell boundaries in ImageJ/Cellpose
- **Thresholding**: Draw ROI areas for thresholding and decide on grouping

## Individual Menu Options

**Purpose**: Access specific analysis steps through their respective menu categories. The multi-layer menu system allows you to start analysis from a specific point in the workflow or continue from where you left off, enabling you to pause and resume long analyses across multiple sessions, or refine specific steps without restarting the entire analysis.

### Configuration Menu Options

#### Configuration → I/O
- **Purpose**: Configure directories for microscope data analysis
- **Use**: **Required for every new dataset** - not just first-time setup
- **Input Directory**: Path to existing directory with microscope-exported .tif files
- **Output Directory**: Path for NEW directory that PerCell will create for analysis results
- **Action**: Configures PerCell for your specific dataset analysis
- **Notes**:
  - Input = existing microscope data
  - Output = new directory PerCell creates
  - Must be done for each experiment/dataset

#### Configuration → Analysis Parameters
- **Purpose**: Choose specific data subsets for analysis
- **Use**: Select conditions, timepoints, regions, channels
- **Required**: Must be run before other analysis steps
- **Output**: Creates output directory structure

#### Configuration → Current Configuration
- **Purpose**: View current settings
- **Use**: Display configured directories and data selection
- **Output**: Shows current input/output paths and selected data

### Segmentation Menu Options

#### Segmentation → Cellpose
- **Purpose**: Identify individual cells using Cellpose
- **Use**: Interactive cell boundary drawing
- **Requirements**: Data selection completed
- **Output**: ROI files for each region

### Processing Menu Options

#### Processing → Single-Cell Data Processing
- **Purpose**: Extract and group individual cells
- **Use**: Automated processing of segmented cells
- **Requirements**: Segmentation completed
- **Output**: Individual cell images grouped by brightness

### Analysis Menu Options

#### Analysis → Threshold Grouped Cells
- **Purpose**: Create binary masks for analysis
- **Use**: Interactive ImageJ thresholding with user guidance
- **Requirements**: Cell processing completed
- **Features**:
  - Gaussian blur preprocessing
  - Contrast enhancement
  - User-guided ROI selection
  - Otsu thresholding

#### Analysis → Measure Cell Area
- **Purpose**: Quantify cell sizes from ROIs
- **Use**: Automated area measurements
- **Requirements**: Segmentation completed
- **Output**: Area measurements for statistical analysis

#### Analysis → Particle Analysis
- **Purpose**: Final analysis and data export
- **Use**: Combine all results and generate reports
- **Requirements**: Previous steps completed
- **Output**:
  - Combined masks
  - Individual cell masks
  - CSV files with measurements
  - Metadata-rich results

### Plugins Menu Options

#### Plugins → Auto Image Preprocessing
- **Purpose**: Comprehensive microscopy image preprocessing workflow
- **Use**: Process raw microscopy data before cell analysis
- **Features**:
  - **Metadata extraction** and analysis from TIFF files
  - **Z-stack creation** from individual z-plane images (if z-series data detected)
  - **Maximum intensity projections** from z-stacks (if z-series data detected)
  - **Multi-channel image merging** into ImageJ-compatible composites (if multi-channel data detected)
  - **Directory structure preservation** - mirrors input experiment organization
  - **Intelligent processing** - only creates directories and runs processes for detected data types
- **Input**: Raw microscopy TIFF files with naming patterns (e.g., `name_z00_ch00.tif`)
- **Output**: Organized directory structure with:
  - `z-stacks/` - Multi-page TIFF stacks per channel
  - `max_projections/` - Maximum intensity projections in timepoint subdirectories
  - `merged/` - Channel-merged composite images
  - `stitched/` - Created only if tile-scan data detected
  - `time_lapse/` - Created only if time-series data detected
- **Data Detection**: Automatically detects and reports:
  - Z-series data (multiple z-planes)
  - Multi-channel data (multiple channels)
  - Time-series data (multiple timepoints)
  - Tile-scan data (multiple tiles/sites)
- **Interactive**: Prompts for input/output directories with validation
- **Navigation**: Returns to main menu after completion

### Utilities Menu Options

#### Utilities → Cleanup
- **Purpose**: Free up disk space
- **Use**: Remove intermediate files while preserving final results
- **Safety**: Only removes cells and masks directories
- **Preserves**: Grouped/combined data and analysis results

## Advanced Workflow Builder (Workflows → Advanced Workflow Builder)

**For experienced users** who need custom analysis sequences or want to repeat specific steps.

```
Select an option (1-10): 2  # Workflows
Select an option (1-3): 2   # Advanced Workflow Builder
```

### How It Works:

1. **Step Selection**: Choose which analysis steps to run
2. **Custom Sequence**: Define the order of operations
3. **Flexible Execution**: Skip unnecessary steps or repeat specific analyses

### Available Steps:
- `data_selection` - Choose data subsets
- `segmentation` - Cell segmentation with Cellpose
- `process_single_cell` - Extract and group cells
- `threshold_grouped_cells` - Interactive thresholding
- `measure_roi_area` - Cell area measurements
- `analysis` - Final analysis and export
- `cleanup` - Disk space management

### Example Custom Workflows:

**Re-run only thresholding and analysis:**
```
Steps: threshold_grouped_cells → analysis
```

**Analyze different data selection:**
```
Steps: data_selection → segmentation → process_single_cell → analysis
```

**Multiple thresholding attempts:**
```
Steps: threshold_grouped_cells → analysis → cleanup → threshold_grouped_cells → analysis
```

### Advantages:
- **Time Saving**: Skip completed steps
- **Experimentation**: Try different parameters
- **Batch Processing**: Analyze multiple datasets
- **Error Recovery**: Resume from failed steps

## Troubleshooting

### Command Not Found
```bash
# Solution 1: Re-run installer
cd percell
./install

# Solution 2: Fix symlink manually
./percell/setup/fix_global_install.sh
```

### Permission Errors
```bash
# Ensure you have write access to /usr/local/bin
ls -la /usr/local/bin/percell

# Alternative: Run with sudo during installation
sudo ./install
```

### ImageJ/Fiji Not Found
- Install ImageJ or Fiji
- Ensure it's in your system PATH
- Or specify path in PerCell configuration

### Missing Dependencies
```bash
# Reinstall in virtual environment
cd percell
source venv/bin/activate
pip install -e .
```

### Data Structure Issues
- Verify directory hierarchy matches requirements
- Remove spaces from all file/folder names
- Ensure TIFF format for all images
- Check that channel files exist in each region

### Memory Issues
- Use cleanup option (Menu 9) to free disk space
- Process smaller data subsets
- Ensure sufficient disk space for output

## Architecture

PerCell is built with **hexagonal architecture** (ports and adapters) for:

- **🔧 Maintainability**: Clean separation of concerns
- **🧪 Testability**: Independent component testing
- **🔄 Extensibility**: Easy addition of new features
- **🛡️ Reliability**: Isolated business logic
- **📈 Scalability**: Independent component development

### Key Components:

- **Domain Layer**: Core business logic (cell analysis, workflow orchestration)
- **Application Layer**: Pipeline orchestration, configuration management
- **Adapters**: External tool integration (ImageJ, Cellpose, file systems)
- **Ports**: Interface definitions for external dependencies

### Technology Stack:

- **Python 3.8+** with scientific libraries (NumPy, SciPy, pandas)
- **Image Processing**: OpenCV, PIL, scikit-image, tifffile
- **External Tools**: Cellpose, ImageJ/Fiji
- **Architecture**: Clean hexagonal design with dependency injection

## Contributing

We welcome contributions! Please see our contributing guidelines for:
- Code style and standards
- Testing requirements
- Pull request process
- Architecture principles

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Support

- **Issues**: [GitHub Issues](https://github.com/marcusjoshm/percell/issues)
- **Discussions**: [GitHub Discussions](https://github.com/marcusjoshm/percell/discussions)
- **Documentation**: Additional docs in `/docs` directory