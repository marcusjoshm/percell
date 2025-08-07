# Microscopy Single Cell Analysis Workflow Protocol

## Introduction

This document provides step-by-step instructions for running our single cell analysis workflow on the lab Macbook Pro. Each section includes detailed explanations and commands you can copy and paste directly into your Terminal.

> **Note:** Terminal is Mac's command-line interface where you can type commands to interact with your computer.

## Table of Contents

1. [Getting Started](#getting-started)
2. [Modular CLI System (New!)](#modular-cli-system-new)
3. [Step 1: Remove Spaces from File Names](#step-1-remove-spaces-from-file-names)
4. [Step 2: Activate the Python Environment](#step-2-activate-the-python-environment)
5. [Step 3: Run the Analysis Workflow](#step-3-run-the-analysis-workflow)
6. [Step 4: Data Analysis Selection](#step-4-data-analysis-selection)
7. [Step 5: Cellpose Segmentation](#step-5-cellpose-segmentation)
8. [Step 6: Otsu Thresholding](#step-6-otsu-thresholding)
9. [Tips and Tricks](#Tips-and-Tricks)
10. [Troubleshooting](#troubleshooting)
11. [Technical Documentation](#technical-documentation)

## Getting Started

### Export Data from LASX

This workflow is designed to work seamlessly with data exported directly from LASX. It relies on the file naming and directory structure used by LASX when images are exported as .tiff files. From LASX, highlight the images you want to export from the `Open projects` tab. Right click and select "Export Image". Make a new folder in the E drive to export your data and click OK. Make sure "Export Channels" is checked and RAW image is selected, then click Save. Copy the export folder to the LEELAB surver from the microscope PC. You can now proceed to analysis on the lab Macbook Pro.

> **Important:** Avoid using a `+` when naming files. It will cause the workflow to fail.
> 
## Modular CLI System (New!)

We've introduced a new modular command-line interface that provides a more user-friendly experience. This system allows you to run individual workflow steps or the complete pipeline with an interactive menu.

### Quick Start with Modular CLI

1. **Activate the environment** (if not already activated):
   ```bash
   cd ~/microscopy-analysis-single-cell
   source venv/bin/activate
   ```

2. **Run the modular interface**:
   ```bash
   python main.py
   ```

3. **You'll see the colorful ASCII header and interactive menu**:
   ```
      ███████╗ ██╗ ███╗   ██╗  ██████╗  ██╗      ███████╗      
      ██╔════╝ ██║ ████╗  ██║ ██╔════╝  ██║      ██╔════╝      
      ███████╗ ██║ ██╔██╗ ██║ ██║  ███╗ ██║      █████╗        
      ╚════██║ ██║ ██║╚██╗██║ ██║   ██║ ██║      ██╔══╝        
      ███████║ ██║ ██║ ╚████║ ╚██████╔╝ ███████╗ ███████╗      
      ╚══════╝ ╚═╝ ╚═╝  ╚═══╝  ╚═════╝  ╚══════╝ ╚══════╝      
                                                               
      ██████╗ ███████╗ ██╗      ██╗                            
      ██╔═══╝ ██╔════╝ ██║      ██║                            
      ██║     █████╗   ██║      ██║                            
      ██║     ██╔══╝   ██║      ██║                            
      ██████╗ ███████╗ ███████╗ ███████╗                       
      ╚═════╝ ╚══════╝ ╚══════╝ ╚══════╝                       
                                                               
       █████╗  ███╗   ██╗  █████╗             
      ██╔══██╗ ████╗  ██║ ██╔══██╗            
      ███████║ ██╔██╗ ██║ ███████║            
      ██╔══██║ ██║╚██╗██║ ██╔══██║            
      ██║  ██║ ██║ ╚████║ ██║  ██║            
      ╚═╝  ╚═╝ ╚═╝  ╚═══╝ ╚═╝  ╚═╝            
                                                                          
      ██╗    ██╗   ██╗ ███████╗ ███████╗ ███████╗                         
      ██║    ╚██╗ ██╔╝ ╚════██║ ██╔════╝ ██╔══██╗                         
      ██║     ╚████╔╝     ██╔╝  █████╗   ██████╔╝                         
      ██║      ╚██╔╝    ██╔╝    ██╔══╝   ██╔══██╗                         
      ███████╗  ██║    ███████╗ ███████╗ ██║  ██║                         
      ╚══════╝  ╚═╝    ╚══════╝ ╚══════╝ ╚═╝  ╚═╝                         
                                                                          

  🔬 Welcome Single Cell Analysis user! 🔬

   MENU:
   1. Set Input/Output Directories
   2. Run Complete Workflow
   3. Data Selection (conditions, regions, timepoints, channels)
   4. Single-cell Segmentation (Cellpose)
   5. Process Single-cell Data (tracking, resizing, extraction, grouping)
   6. Threshold Grouped Cells (interactive ImageJ thresholding)
   7. Analysis (combine masks, create cell masks, export results)
   8. Exit
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

#### Option 7: Analysis
- Combines masks from different groups
- Creates individual cell masks
- Analyzes cell features
- Includes group metadata in results
- **Requires data selection to be completed first**

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
6. Choose Option 7 for analysis

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
cd ~/microscopy-analysis-single-cell
venvact
```

2. Press `Enter`.

3. You should now see `(venv)` at the beginning of the command prompt line. This indicates that the Python virtual environment is activated and the program is ready to run.

Example of how your prompt should look:
```bash
(venv) (base) ➜  microscopy-analysis-single-cell git:(main) ✗
```

## Step 3: Run the Analysis Workflow

You have two options for running the analysis workflow:

### Option A: New Modular CLI (Recommended) ⭐

1. **Run the modular interface**:
   ```bash
   python main.py
   ```

2. **Choose Option 2 (Run Complete Workflow)** from the menu

3. **Follow the interactive prompts** for data selection and segmentation

This is the recommended approach for new users as it provides a more user-friendly experience.

### Option B: Original Workflow

If you prefer the original command-line approach:

1. Copy and paste the following into Terminal:

```bash
python single_cell_workflow.py --config config/config.json
```

2. After pasting the above, press Space and type `--input` followed by another Space.

3. Drag the folder you want to analyze from Finder into the Terminal window. The absolute file path will appear.

4. Press Space and type `--output` followed by another Space.

5. Drag the same folder into Terminal again.

6. After the path appears, add `_analysis` followed by a description at the end of the folder name. Make sure there are no spaces in the file path.

Your final command should look something like this:
```bash
python single_cell_workflow.py --config config/config.json --input /Volumes/LEELAB/JL_Data/2025-05-08_export_max --output /Volumes/LEELAB/JL_Data/2025-05-08_analysis_Dish_1_Control_40minWash
```

7. Press `Enter` to start the analysis.

8. The script will create an output folder with the name you specified, containing all analysis results.

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
Review available timepoints in the raw data and decide which timepoints to use for analysis. Current experiment has timepoints: t00. Press Enter when you have made your selection. You can specify timepoints when running the script with --timepoints option.

Available timepoints:
1. t00

Input options for timepoints:
- Enter timepoints as space-separated text (e.g., 't00 t00')
- Enter numbers from the list (e.g., '1 1')
- Type 'all' to select all timepoints

Enter your selection:
```

For `single_timepoint` data, there will only be one option (1. t00). Simply type "1" and then Enter.

For `multi_timepoint` data, the program will list all available timepoints like this:
```
Available timepoints:
1. t00
2. t01
3. t02
4. t03
5. t04
```

The first timepoint will always be t00. You can:
- Type "all" to select all timepoints
- Enter specific timepoints separated by spaces

For example, to select only the first and last timepoints from the list above:
```
Enter your selection: 1 5
```

**Important for multi_timepoint data:** The program has a feature that tracks cells across timepoints, so each ROI number from a given dataset corresponds to the same cell throughout the analysis.

### Selecting Regions

After selecting timepoints, you'll be prompted to select regions for analysis:

```
================================================================================
MANUAL STEP REQUIRED: select_regions
================================================================================
Review available regions in the raw data and decide which regions to use for analysis. Current experiment has regions:
```

You'll see a list of available regions like this example:

```
Available regions:
1. Control_40minWash_TS1
2. Control_40minWash_TS2
3. Control_40minWash_TS3
4. Control_MG132_40minWash_TS1
5. Control_MG132_40minWash_TS2
6. Control_NaAsO2_TS1
7. Control_NaAsO2_TS2
...and so on
```

The region names will match the file names exported from LASX. The prompt will show:

```
Input options for regions:
- Enter regions as space-separated text (e.g., 'Control_40minWash_TS1 LSG1i_VCPi_40minWash_TS2')
- Enter numbers from the list (e.g., '1 21')
- Type 'all' to select all regions

Enter your selection: 
```

Make your selection by entering numbers separated by spaces. For example, to analyze all Control_40minWash tile-scans from the example above:

```
Enter your selection: 1 2 3
```

**Important:** Make sure all selected regions were captured with the same channels, or the program will terminate.

### Selecting Segmentation Channels

After selecting regions, you'll be prompted to select channels for segmentation:

```
================================================================================
MANUAL STEP REQUIRED: select_segmentation_channels
================================================================================
Review available channels for segmentation:

Available channels:
1. ch00
2. ch01

Input options for channels:
- Enter channels as space-separated text (e.g., 'ch00 ch01')
- Enter numbers from the list (e.g., '1 2')
- Type 'all' to select all channels

Enter your selection:
```

The channels will be in the order of capture settings configured in LASX:
- ch00 corresponds to the channel setting at the top
- ch01 is the second channel
- And so on

**Important:** Select the channel(s) that will be used for cell segmentation. This is typically a channel that shows cell boundaries or nuclei clearly (e.g., DAPI for nuclei or a cytoplasmic marker).

Enter your channel selection and press Enter.

### Selecting Analysis Channels

Next, you'll be prompted to select channels for analysis:

```
================================================================================
MANUAL STEP REQUIRED: select_analysis_channels
================================================================================
Review available channels for analysis:

Available channels:
1. ch00
2. ch01

Input options for channels:
- Enter channels as space-separated text (e.g., 'ch00 ch01')
- Enter numbers from the list (e.g., '1 2')
- Type 'all' to select all channels

Enter your selection:
```

**Important:** Select only ONE channel at a time for analysis. For example, if you are analyzing stress granules, select the channel that corresponds to G3BP1. This is the channel where you want to measure and threshold your structures of interest.

Enter your channel selection and press Enter to continue with the analysis.

## Step 5: Cellpose Segmentation

After making all data selections, Cellpose and ImageJ will automatically open. Follow these steps to perform cell segmentation:

1. Click on the Cellpose GUI window. You should see "Python" at the top of the screen next to the Apple symbol.

2. Click on **File > Load image** and navigate to the output folder you specified when running the workflow.

3. Go into the **preprocessed** folder and navigate through the subdirectories to find files for segmentation:
   - The program separates files by condition and time-point
   - There will be two layers of folders before reaching the image files
   - Look for files starting with "bin4x4_"
   
   > **Note:** Cellpose cannot handle large tile-scans, so the program shrinks the files for segmentation purposes only.

4. Select the file you want to segment and click **Open**.

5. In the segmentation section on the left panel, find "additional settings" with an upward arrow. Click on the arrow to open the settings options.

6. Configure the segmentation parameters:
   - Next to **diameter:** enter a number in pixels that corresponds to the average size of a cell
     - A magenta circle at the bottom of the screen shows the relative size of your selection
     - Adjust the number until the circle roughly matches the size of your cells
     - Typically, cells are between 70 and 150 pixels depending on cell type and pixel size
   - Next to **niter dynamics:** enter "250"

7. Click the **run CPSAM** button to start segmentation.

8. When segmentation finishes, masks of different colors will appear.

9. Manually remove partial cells at the edges:
   - Go to the Drawing panel on the left
   - Under "delete multiple ROIs" click **click-select**
   - Click on the colored masks you want to delete
   - Selected masks will change color to grey
   - When all unwanted masks are selected, click **done** to delete them
   > **Note:** The program groups cells based on relative expression level. For this reason it is important to remove partial cells at the edge of the field or grouping may not work as expected. It is also good practive to avoid analyzing partial cells because this could scew results.

10. Fix incorrect segmentation if needed:
    > **Note:** The new Cellpose-SAM model (SAM stands for <u>S</u>egment <u>A</u>nything <u>M</u>odel) makes fewer mistakes but they do still occur sometimes
    - Delete problematic masks using the process above
    - Manually draw new masks by:
      - Holding down the space bar and clicking on the image
      - Moving the cursor (no need to hold the space bar) to draw a new mask
      - The mask will automatically display when the shape is completed

11. When segmentation is complete, click **File > Save outlines as .zip archive of ROI files for ImageJ**.

12. Repeat this process for all files you selected to analyze.

13. When finished with all files:
    - Close the Cellpose window
    - Click on the Terminal window
    - Press Enter to continue

At this point, ImageJ macros will run that:
- Resizes the segmented ROIs
- Creates files for the individually segmented cells

## Step 6: Otsu Thresholding

Once the ImageJ macros complete, ImageJ will launch again for guided thresholding:

1. The program groups cells with similar expression levels to allow large groups of cells to be thresholded at the same time.
   > **Note:** This is particularly useful for experiments with polyclonal over-expression.

2. A window will pop up with instructions:
   ```
   Please draw an oval ROI in a representative area for thresholding, then click OK.
   ```

3. An image will also appear showing individual cells with similar intensity levels.
   > **Note:** The default for the program is 5 groups.

4. Draw an oval around the area you want to threshold:
   - For example, if analyzing stress granules from a fluorescence image of G3BP1, draw an oval around some of the stress granules

5. To check how the Otsu thresholding will work with your ROI placement:
   - Press **Shift + T** to bring up the Threshold window
   - Select "Otsu" from the drop-down menu
   - Click **Reset** and then **Auto**
   - Areas identified by thresholding will appear in red
   
6. If the current ROI placement doesn't properly threshold all desired structures or is picking up undesired areas:
   - Draw a new ROI around a different region
   - Test again by clicking **Auto** from the thresholding window
   
7. When satisfied with the ROI placement, click **OK** on the pop-up window

> **Note:** If an acceptable ROI placement doesn't exist, draw an ROI anywhere and press `OK`. There will be options later to handle situations like this.

8. A new window titled "**Evaluate Cell Grouping**" will appear with the message:
   ```
   Based on what you see in this image, do you want to:
   Decision:
   ```
   
   Followed by a dropdown menu with two options:
   - Continue with thresholding
   - Go back and add one more group
   - Ignore thresholding for this group. There are no structures to threshold in the field

9. Choose the appropriate option:
   - If the image contains cells with equal expression levels and the Otsu auto thresholding accurately identifies desired structures, select **Continue with thresholding** and click **OK** (or simply press Enter)
   - If an image is difficult to threshold properly, select **Go back and add one more group** and click **OK**
   - If there aren't any features in the image to threshold (for example, an image where none of the cells have stress granules or P-bodies), select **Ignore thresholding for this group. There are no structures to threshold in the field** and click **OK**

10. If you selected "Go back and add one more group":
    - A window will appear with the message:
      ```
      Your request for more bins has been recorded. The workflow will restart the cell grouping step with more bins. You can now close ImageJ.
      ```
    - Click **OK**
    - The program will repeat the grouping step with one more group than before
    - Continue this process until all images can be thresholded properly

11. Once all images have been thresholded successfully:
    - The ImageJ toolbar will appear
    - A message in the log window will read:
      ```
      Thresholding of grouped cells completed.
      ```

12. Close ImageJ:
    - Close the ImageJ toolbar directly, or
    - Select **File > Quit**

13. The program will automatically:
    - Resume processing
    - Segment the binary masks
    - Analyze particles in the background
    - Compile all results into a .csv file in the analysis folder of your output directory

14. When the process is complete, you'll see this message in the Terminal window:
    ```
    SingleCellWorkflow - INFO - Workflow completed successfully
    ```

At this point, your analysis is complete and the results are ready for review.

## Tips and Tricks

### Terminal Navigation

Here are some helpful tips for using the Terminal efficiently, saving you a lot of time when running this workflow. 

1. **Command History**:
   - Press the **Up Arrow** key to cycle through previously entered commands. The command for running the workflow is long, so by entering the command each time, you can press the **up** key and change the output folder name when analyzing a large dataset. 
   - Type part of a previous command and then press **Up Arrow** to search through history for commands that match what you've typed. Let's say you want to rerun the workflow but don't want to type out the entire command. However, someone used the Terminal before you, and the previous workflow commands are far back in history. You can type `python sing` and then press the **up** key, and the Terminal will only cycle through commands that start with `python sing`.

2. **Tab Completion**:
   - Press the **Tab** key to auto-complete file and directory names. This will save you lots of time if you prefer to type out commands rather than copy and paste from the protocol. For example, to remove spaces from file names without coping and pasting the commands from the protocol, you can type `cd ~/ba` then `tab`, and if there are no other directories that start with "ba," it will fill in `cd ~/bash_scripts`. Similarly, if your working directory is `/Users/leelab/bash_scripts` and you type `./r` followed by `tab`, it will fill in `./replace_spaces.sh`.

3. **Text Navigation**:
The following are useful commands for typing in the Terminal:
   - **Control + A**: Move cursor to the beginning of the line
   - **Control + E**: Move cursor to the end of the line
   - **Control + U**: Clear the line before the cursor
   - **Control + K**: Clear the line after the cursor

## Troubleshooting

### Common Errors and Solutions

I will include common errors in the workflow here, what to look for if there is an issue, and how to fix it. If you run into an unexpected error or issue, take a screenshot and document the issue.

#### Need Additional Help?

If you encounter persistent issues, please contact:
- IT Support: joshua.marcus@bcm.edu

## Technical Documentation

For developers, installation instructions, advanced configuration, and detailed technical information, see [DOCUMENTATION.md](DOCUMENTATION.md).
