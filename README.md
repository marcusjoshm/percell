# <p>  <b>PerCell </b> </p>
<img src="percell/art/percell_terminal_window.png?v=2" width="900" title="Percell Terminal Interface" alt="Percell Terminal Interface" align="center">

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![repo size](https://img.shields.io/github/repo-size/marcusjoshm/percell)](https://github.com/marcusjoshm/percell/)
[![License: MIT](https://img.shields.io/github/license/marcusjoshm/percell)](https://github.com/marcusjoshm/percell/blob/main/LICENSE)
[![Contributors](https://img.shields.io/github/contributors-anon/marcusjoshm/percell)](https://github.com/marcusjoshm/percell/graphs/contributors)
[![Last commit](https://img.shields.io/github/last-commit/marcusjoshm/percell)](https://github.com/marcusjoshm/percell/)
[![Issues](https://img.shields.io/github/issues/marcusjoshm/percell)](https://github.com/marcusjoshm/percell/issues)
[![Pull requests](https://img.shields.io/github/issues-pr/marcusjoshm/percell)](https://github.com/marcusjoshm/percell/pulls)
[![GitHub stars](https://img.shields.io/github/stars/marcusjoshm/percell?style=social)](https://github.com/marcusjoshm/percell/)
[![GitHub forks](https://img.shields.io/github/forks/marcusjoshm/percell?style=social)](https://github.com/marcusjoshm/percell/)

A single cell microscopy analysis tool that integrates single cell segmentation using cellpose with imageJ macros into a single software package with an easy-to-use command line interface. Built with a clean hexagonal architecture for maintainability and extensibility.

## Table of Contents

1. [Installation](#installation)
2. [Architecture Overview](#architecture-overview)
3. [Getting Started](#getting-started)
4. [Modular CLI System](#modular-cli-system)
5. [Step 1: Remove Spaces from File Names](#step-1-remove-spaces-from-file-names)
6. [Step 2: Activate the Python Environment](#step-2-activate-the-python-environment)
7. [Step 3: Run the Analysis Workflow](#step-3-run-the-analysis-workflow)
8. [Step 4: Data Analysis Selection](#step-4-data-analysis-selection)
9. [Step 5: Cellpose Segmentation](#step-5-cellpose-segmentation)
10. [Step 6: Otsu Thresholding](#step-6-otsu-thresholding)
11. [Tips and Tricks](#tips-and-tricks)
12. [Troubleshooting](#troubleshooting)
13. [Technical Documentation](#technical-documentation)


## Installation

### Quick Installation (Recommended)

After cloning this repository, run a single command to complete the installation:

```bash
# Clone the repository
git clone https://github.com/marcusjoshm/percell.git
cd percell

# Run the installation script (choose one method)
./install
```

This single command will:
- ✅ Create virtual environments (main + Cellpose)
- ✅ Install all dependencies
- ✅ Install the package in development mode
- ✅ Detect software paths (ImageJ/Fiji)
- ✅ Create configuration files
- ✅ Verify the installation

### After Installation

Once the installation is complete, you can use the tool:

```bash
# Option 1: Run from anywhere (recommended)
percell

# Option 2: Run from project directory with activated environment
cd ~/percell
source venv/bin/activate
percell
```

**Global Installation Benefits:**
- ✅ Run `percell` from any directory
- ✅ No need to navigate to project folder
- ✅ No need to activate virtual environment manually
- ✅ Works seamlessly across different terminals

**Why development mode?**
- ✅ Changes to code are immediately reflected (no reinstall needed)
- ✅ Command-line tool available: `percell`
- ✅ Proper package imports work
- ✅ Ideal for development and testing

### Troubleshooting Global Installation

If the `percell` command is not found globally after installation:

```bash
# Quick fix - run this script from the project directory
./percell/setup/fix_global_install.sh

# Or manually create the symlink (replace with your actual path)
sudo ln -sf /path/to/your/percell/venv/bin/percell /usr/local/bin/percell
```

**Common Issue**: The package is installed in the virtual environment but the global symbolic link wasn't created. This happens when:
- You ran `pip install -e .` manually instead of using the installation script
- The installation script didn't have permission to create the symlink
- The symlink was accidentally removed

**Symptoms**:
- `which percell` returns nothing
- `percell --help` says "command not found"
- You have to navigate to the project directory and activate the venv to use percell

**Solution**: Run the fix script from the project root directory. It will automatically detect your setup and create the necessary symlink.

```bash
# From the project root directory (recommended)
./percell/setup/fix_global_install.sh

# Or from anywhere, specifying the full path
/path/to/percell/percell/setup/fix_global_install.sh
```

**Note**: The fix script is self-contained and will automatically find the correct paths regardless of where you run it from.

## Architecture Overview

PerCell is built using a **hexagonal architecture** (also known as ports and adapters pattern) that provides clean separation of concerns and makes the codebase maintainable and extensible.

### Architecture Layers

```
┌─────────────────────────────────────────────────────────────┐
│                    User Interface Layer                     │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────┐  │
│  │   CLI Adapter   │  │   GUI Adapter   │  │  API Adapter│  │
│  └─────────────────┘  └─────────────────┘  └─────────────┘  │
└─────────────────────────────────────────────────────────────┘
                                │
┌─────────────────────────────────────────────────────────────┐
│                   Application Layer                         │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────┐  │
│  │  Pipeline API   │  │  Configuration  │  │   Progress  │  │
│  │                 │  │      API        │  │     API     │  │
│  └─────────────────┘  └─────────────────┘  └─────────────┘  │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────┐  │
│  │  Stage Classes  │  │  CLI Services   │  │  Workflow   │  │
│  │                 │  │                 │  │ Coordinator │  │
│  └─────────────────┘  └─────────────────┘  └─────────────┘  │
└─────────────────────────────────────────────────────────────┘
                                │
┌─────────────────────────────────────────────────────────────┐
│                     Domain Layer                            │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────┐  │
│  │     Models      │  │    Services     │  │   Business  │  │
│  │                 │  │                 │  │    Logic    │  │
│  └─────────────────┘  └─────────────────┘  └─────────────┘  │
└─────────────────────────────────────────────────────────────┘
                                │
┌─────────────────────────────────────────────────────────────┐
│                   Infrastructure Layer                      │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────┐  │
│  │ ImageJ Adapter  │  │ File System     │  │ Cellpose    │  │
│  │                 │  │ Adapter         │  │ Adapter     │  │
│  └─────────────────┘  └─────────────────┘  └─────────────┘  │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────┐  │
│  │ Image Processing│  │  CLI Interface  │  │   Progress  │  │
│  │ Adapter         │  │ Adapter         │  │   Adapter   │  │
│  └─────────────────┘  └─────────────────┘  └─────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

### Key Components

#### **Domain Layer** (`percell/domain/`)
- **Models**: Core business entities and data structures
- **Services**: Pure business logic without external dependencies
  - `DataSelectionService`: Handles data validation and selection
  - `FileNamingService`: Manages file naming conventions
  - `IntensityAnalysisService`: Performs intensity-based analysis
  - `WorkflowOrchestrationService`: Coordinates workflow execution

#### **Application Layer** (`percell/application/`)
- **Pipeline API**: Main orchestration and workflow management
- **Configuration API**: Centralized configuration management
- **Progress API**: Progress tracking and user feedback
- **Stage Classes**: Individual workflow steps and stages
- **CLI Services**: Command-line interface logic

#### **Adapters** (`percell/adapters/`)
- **ImageJ Macro Adapter**: Interfaces with ImageJ/Fiji
- **Cellpose Subprocess Adapter**: Manages Cellpose integration
- **Local File System Adapter**: Handles file operations
- **PIL Image Processing Adapter**: Image manipulation tasks
- **CLI User Interface Adapter**: Terminal-based user interface

#### **Ports** (`percell/ports/`)
- **Driving Ports**: Interfaces that the application uses to interact with external systems
- **Driven Ports**: Interfaces that external systems implement to interact with the application

### Benefits of This Architecture

- **🔧 Maintainability**: Clear separation of concerns makes code easier to understand and modify
- **🧪 Testability**: Each layer can be tested independently with proper mocking
- **🔄 Extensibility**: New adapters can be added without changing core business logic
- **🛡️ Reliability**: Domain logic is isolated from external dependencies
- **📈 Scalability**: Components can be developed and deployed independently

### Package Structure

```
percell/
├── adapters/          # External system integrations
├── application/       # Application orchestration layer
├── domain/           # Core business logic
├── main/             # Application entry points
├── ports/            # Interface definitions
├── config/           # Configuration files
├── bash/             # Shell scripts
├── macros/           # ImageJ macro files
└── setup/            # Installation and setup files
```

## Getting Started

### Input Directory Structure

The workflow requires a specific directory structure to organize your microscopy data. Your input directory should be organized hierarchically as follows:

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
│       ├── region_1/
│       │   ├── channel_1.tif
│       │   ├── channel_2.tif
│       │   └── channel_3.tif
│       └── region_2/
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

#### Directory Structure Requirements:

**For Multi-timepoint Experiments:**
1. **Conditions** (top level): Different experimental conditions (e.g., `Control`, `Treatment`, `Dish_1`, `Dish_2`)
2. **Timepoints** (second level): Time points in your experiment (e.g., `0min`, `30min`, `60min`, `T1`, `T2`)
3. **Regions** (third level): Different regions or fields of view (e.g., `Region_1`, `Field_1`, `ROI_1`)
4. **Channels** (files): Individual channel images as `.tif` files

**For Single-timepoint Experiments:**
1. **Conditions** (top level): Different experimental conditions (e.g., `Control`, `Treatment`, `Dish_1`, `Dish_2`)
2. **Regions** (second level): Different regions or fields of view (e.g., `Region_1`, `Field_1`, `ROI_1`)
3. **Channels** (files): Individual channel images as `.tif` files

*Note: For single-timepoint experiments, the timepoint level is automatically filled in by the workflow.*

#### File Naming Requirements:

- **No spaces** in directory or file names (use underscores `_` instead)
- **No special characters** like `+`, `&`, `%`, etc.
- **Consistent naming** across conditions, timepoints, and regions
- **Channel files** should be named descriptively (e.g., `DAPI.tif`, `GFP.tif`, `RFP.tif`)

#### Example Structures:

**Multi-timepoint Experiment:**
```
microscopy_data/
├── Control/
│   ├── 0min/
│   │   ├── Region_1/
│   │   │   ├── DAPI.tif
│   │   │   ├── GFP.tif
│   │   │   └── RFP.tif
│   │   └── Region_2/
│   │       ├── DAPI.tif
│   │       ├── GFP.tif
│   │       └── RFP.tif
│   └── 30min/
│       └── Region_1/
│           ├── DAPI.tif
│           ├── GFP.tif
│           └── RFP.tif
└── Treatment/
    ├── 0min/
    │   └── Region_1/
    │       ├── DAPI.tif
    │       ├── GFP.tif
    │       └── RFP.tif
    └── 30min/
        └── Region_1/
            ├── DAPI.tif
            ├── GFP.tif
            └── RFP.tif
```

**Single-timepoint Experiment:**
```
microscopy_data/
├── Control/
│   ├── Region_1/
│   │   ├── DAPI.tif
│   │   ├── GFP.tif
│   │   └── RFP.tif
│   └── Region_2/
│       ├── DAPI.tif
│       ├── GFP.tif
│       └── RFP.tif
└── Treatment/
    └── Region_1/
        ├── DAPI.tif
        ├── GFP.tif
        └── RFP.tif
```

> **Important:** 
> - Avoid using a `+` when naming files or directories
> - Ensure all conditions have the same timepoints and regions for consistent analysis
> - Use descriptive names for channels to identify them during analysis
> 
## Modular CLI System

PerCell features a modular command-line interface that provides a user-friendly experience. This system allows you to run individual workflow steps or the complete pipeline with an interactive menu, built on the hexagonal architecture for reliability and maintainability.

### Quick Start with Modular CLI

**After running `python percell/setup/install.py`, you can use the tool**

```bash
# Enter this command in a terminal window. It will work from any working directory.
percell

```


**You'll see the colorful ASCII header and interactive menu:**
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
   9. Cleanup (empty cells and masks directories, preserves grouped/combined data)
   10. Advanced Workflow Builder (custom sequence of steps)
   11. Exit
   Select an option (1-11):
   ```



### Menu Options Explained

#### Option 1: Set Input/Output Directories
- Updates the configuration file with your input and output paths
- Does not create any directories (only updates config)
- Use this to set up your paths before running other options

#### Option 2: Run Complete Workflow ⭐ **Recommended for New Users**
- Runs all steps in sequence: 3 → 4 → 5 → 6 → 7
- Handles interactive steps automatically
- Perfect for running the entire analysis pipeline

#### Option 3: Data Selection
- Interactive selection of conditions, regions, timepoints, and channels
- Creates the output directory structure
- Prepares input data for analysis
- **Required before running other workflow steps**

#### Option 4: Single-cell Segmentation
- Bins images for segmentation
- Launches Cellpose and FIJI for interactive cell segmentation
- **Requires data selection to be completed first**

#### Option 5: Process Single-cell Data
- Tracks ROIs across timepoints (if multiple timepoints)
- Resizes ROIs to match original image dimensions
- Duplicates ROIs for analysis channels
- Extracts individual cells
- **Requires data selection to be completed first**

#### Option 6: Threshold Grouped Cells
- Groups cells by expression level
- Interactive ImageJ thresholding for grouped cells
- **Requires data selection to be completed first**

#### Option 7: Measure Cell Area
- Measures areas of ROIs in raw images
- Provides quantitative analysis of cell sizes
- **Requires data selection to be completed first**

#### Option 8: Analysis
- Combines masks from different groups
- Creates individual cell masks
- Analyzes cell features
- Includes group metadata in results
- **Requires data selection to be completed first**

#### Option 9: Cleanup
- Empties cells and masks directories to free up space
- Preserves grouped/combined data
- Useful for managing disk space after analysis
- **Safe to run after analysis is complete**

#### Option 10: Advanced Workflow Builder
- Allows custom sequence of workflow steps
- Provides fine-grained control over the analysis process
- **For advanced users who need custom workflows**

### Example Workflow

**For a complete analysis:**
1. Choose Option 2 (Run Complete Workflow)
2. Follow the prompts for data selection
3. Complete the interactive segmentation step
4. Wait for all processing to complete

**For step-by-step analysis:**
1. Choose Option 1 to set directories
2. Choose Option 3 for data selection
3. Choose Option 4 for segmentation
4. Choose Option 5 for cell processing
5. Choose Option 6 for thresholding
6. Choose Option 7 for cell area measurement
7. Choose Option 8 for analysis
8. Choose Option 9 for cleanup (optional)

### Benefits of the Modular System

- **User-friendly**: Clear menu with color-coded options
- **Flexible**: Run individual steps or complete workflow
- **Error recovery**: Returns to menu after errors
- **Progress tracking**: Shows which step is currently running
- **Interactive support**: Proper handling of user input

### Opening Terminal

1. Press Command + Space to open Spotlight Search
2. Type "Terminal"
3. Click on the Terminal application

Alternatively you can click on the Terminal app icon located in the doc at the bottom of the screen. It looks like a black square with >_ in the top left corner.

When Terminal opens, you'll see a prompt that looks something like `(base) ➜  ~`


## Step 1: Remove Spaces from File Names

Our analysis workflow requires file paths without spaces. Follow these steps to convert spaces in your file names to underscores:

1. Copy and paste the following command into Terminal:

```bash
cd ~/bash_scripts/
```

3. Press `Enter`.

2. Next, copy and paste this command:

```bash
./replace_spaces.sh
```

3. Drag the folder you want to analyze from Finder into the Terminal window. The file path will appear automatically.

4. Press `Enter`.

5. You will see a prompt that looks like this:

```
========================================================
  Space to Underscore Converter - Enhanced Version
========================================================
```

Followed by information about the directory you want to modify.

6. At the end, you will see:

```
Do you want to continue? (y/n)
```

7. Type `y` and press Enter to run the program.

8. When the process completes successfully, you will see:

```
[SUCCESS] Operation completed successfully!
```

This means the program has finished removing spaces from all file names in the directory and you're ready to proceed to the analysis workflow.

## Step 2: Activate the Python Environment

In the same Terminal window:

1. Copy and paste the following commands:

```bash
cd ~/percell
venvact
```

2. Press `Enter`.

3. You should now see `(venv)` at the beginning of the command prompt line. This indicates that the Python virtual environment is activated and the program is ready to run.

Example of how your prompt should look:
```bash
(venv) (base) ➜  percell git:(main) ✗
```

## Step 3: Run the Analysis Workflow

You have two options for running the analysis workflow:

### Option A: Modular CLI (Recommended) ⭐

1. **Run the modular interface**:
   ```bash
   percell
   ```

2. **Choose Option 2 (Run Complete Workflow)** from the menu

3. **Follow the interactive prompts** for data selection and segmentation

This is the recommended approach as it provides a user-friendly experience built on the hexagonal architecture.

### Option B: Direct Command Line

If you prefer direct command-line execution:

1. Copy and paste the following into Terminal:

```bash
percell --input /path/to/input --output /path/to/output --complete-workflow
```

2. Replace `/path/to/input` with your actual input directory path

3. Replace `/path/to/output` with your desired output directory path

Your final command should look something like this:
```bash
percell --input /Volumes/LEELAB/JL_Data/2025-05-08_export_max --output /Volumes/LEELAB/JL_Data/2025-05-08_analysis_Dish_1_Control_40minWash --complete-workflow
```

4. Press `Enter` to start the analysis.

5. The script will create an output folder with the name you specified, containing all analysis results.

> **Important:** Remember that the output folder name can be anything you want as long as there are no spaces in it. Use underscores (_) instead of spaces.

## Step 4: Data Analysis Selection

After starting the analysis workflow, you'll need to make selections about your data:

### Selecting Data Type

The program will prompt you to select the type of data you're analyzing:

```
================================================================================
MANUAL STEP REQUIRED: select_datatype
================================================================================
Select the type of data: single_timepoint or multi_timepoint. You can specify the datatype when running the script with the --datatype option.

Detected datatype based on found timepoints: single_timepoint
Select data type:
1. single_timepoint
2. multi_timepoint
Enter selection (number or name, press Enter for detected default):
```

**Important:** 
- Choose `single_timepoint` (option 1) for immunofluorescence or single time-point live microscopy
- Choose `multi_timepoint` (option 2) for time-lapse microscopy data only

Make your selection by typing "1" or "2" followed by Enter. If the detected default is correct, you can simply press Enter.

### Selecting Condition

Next, you'll see a prompt to select the experimental condition for analysis:

```
================================================================================
MANUAL STEP REQUIRED: select_condition
================================================================================
```

"Condition" in this case will be the name of the .lif project file where data was exported. If you exported data from multiple project files, there will be a list of conditions to choose from, otherwise there will only be one. An example of a condition list looks something like this:

```
Available conditions:
1. Dish_1_Sec61b_Washout_+_DMSO
2. Dish_2_Sec61b_Washout_+_Rapa
3. Dish_3_RTN4_Washout_+_DMSO
4. Dish_4_RTN4_Washout_+_Rapa
5. Dish_5_CLIMP63_Washout_+_DMSO
6. Dish_6_CLIMP63_Washout_+_Rapa

Input options for conditions:
- Enter conditions as space-separated text (e.g., 'Dish_1_Sec61b_Washout_+_DMSO Dish_6_CLIMP63_Washout_+_Rapa')
- Enter numbers from the list (e.g., '1 6')
- Type 'all' to select all conditions

Enter your selection:
```

Type the number of the project file you would like to analyze. If you want to analyze multiple condition datasets at the same time, type the numbers separated by a space, or type "all" if you want to analyze everything. Then press `Enter`.

### Selecting Timepoints

Next, you'll see a prompt to select timepoints for analysis:

```
================================================================================
MANUAL STEP REQUIRED: select_timepoints
================================================================================
Available timepoints:
1. 0min
2. 30min
3. 60min

Input options for timepoints:
- Enter timepoints as space-separated text (e.g., '0min 30min')
- Enter numbers from the list (e.g., '1 2')
- Type 'all' to select all timepoints

Enter your selection:
```

Type the numbers of the timepoints you want to analyze, separated by spaces, or type "all" to analyze all timepoints. Then press `Enter`.

## Tips and Tricks

### Performance Optimization
- **Batch Processing**: Process multiple conditions simultaneously for faster analysis
- **Memory Management**: Use the cleanup option to free up disk space after analysis
- **Parallel Processing**: The hexagonal architecture enables efficient parallel processing

### Data Organization
- **Consistent Naming**: Use consistent naming conventions across all conditions
- **Directory Structure**: Follow the recommended directory structure for optimal performance
- **File Formats**: Use `.tif` files for best compatibility with ImageJ integration

### Troubleshooting Common Issues

#### Installation Issues
```bash
# If percell command is not found
./percell/setup/fix_global_install.sh

# If dependencies are missing
pip install -e .
```

#### Runtime Issues
- **File Path Issues**: Ensure no spaces in file or directory names
- **Permission Issues**: Check file permissions for input/output directories
- **Memory Issues**: Use cleanup option to free up space during long analyses

## Technical Documentation

### Architecture Benefits

The hexagonal architecture provides several key advantages:

- **Separation of Concerns**: Business logic is isolated from external dependencies
- **Testability**: Each component can be tested independently
- **Maintainability**: Changes to one layer don't affect others
- **Extensibility**: New adapters can be added without modifying core logic
- **Reliability**: External system failures don't crash the application

### Development Guidelines

#### Adding New Features
1. **Domain Layer**: Add business logic to domain services
2. **Application Layer**: Add orchestration logic to application services
3. **Adapters**: Create new adapters for external system integration
4. **Ports**: Define interfaces for new external interactions

#### Testing Strategy
- **Unit Tests**: Test domain services in isolation
- **Integration Tests**: Test adapter implementations
- **Contract Tests**: Verify port implementations
- **End-to-End Tests**: Test complete workflows

### API Reference

#### Core APIs
- **Pipeline API**: `percell.application.pipeline_api`
- **Configuration API**: `percell.application.config_api`
- **Progress API**: `percell.application.progress_api`
- **Logger API**: `percell.application.logger_api`

#### Domain Services
- **Data Selection**: `percell.domain.services.data_selection_service`
- **File Naming**: `percell.domain.services.file_naming_service`
- **Intensity Analysis**: `percell.domain.services.intensity_analysis_service`
- **Workflow Orchestration**: `percell.domain.services.workflow_orchestration_service`

#### Adapters
- **ImageJ Integration**: `percell.adapters.imagej_macro_adapter`
- **File System**: `percell.adapters.local_filesystem_adapter`
- **Cellpose Integration**: `percell.adapters.cellpose_subprocess_adapter`
- **Image Processing**: `percell.adapters.pil_image_processing_adapter`

### Contributing

We welcome contributions! Please see our [Contributing Guidelines](CONTRIBUTING.md) for details on:
- Code style and standards
- Testing requirements
- Pull request process
- Architecture principles

### License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

### Support

For support and questions:
- **Issues**: [GitHub Issues](https://github.com/marcusjoshm/percell/issues)
- **Discussions**: [GitHub Discussions](https://github.com/marcusjoshm/percell/discussions)
- **Documentation**: [Project Wiki](https://github.com/marcusjoshm/percell/wiki)
