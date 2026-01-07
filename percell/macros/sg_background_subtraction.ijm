// ImageJ Macro for Stress Granule Analysis
// Automated version for percell integration - no user interaction required
//
// Expected directory structure:
// mainDir/
//   ├── Masks/           (containing MASK_MAX_z-stack_*_ch1_*.tif)
//   ├── Raw Data/        (containing MAX_z-stack_*_ch1_*.tif)
//   └── Processed/       (output directory, created automatically)
//
// Parameters passed via macro argument:
//   arg = mainDir (directory containing Masks and Raw Data folders)

// Set batch mode for faster processing
setBatchMode(true);

// Get the main directory from macro argument
arg = getArgument();
if (arg == "") {
    print("ERROR: No main directory argument provided");
    exit("Missing required argument: mainDir");
}

mainDir = arg;
if (!endsWith(mainDir, File.separator)) {
    mainDir = mainDir + File.separator;
}

masksDir = mainDir + "Masks" + File.separator;
rawDataDir = mainDir + "Raw Data" + File.separator;
outputBaseDir = mainDir + "Processed" + File.separator;

// Validate directories exist
if (!File.exists(masksDir)) {
    print("ERROR: Masks directory not found: " + masksDir);
    exit("Masks directory not found");
}
if (!File.exists(rawDataDir)) {
    print("ERROR: Raw Data directory not found: " + rawDataDir);
    exit("Raw Data directory not found");
}

// Create output directory if it doesn't exist
File.makeDirectory(outputBaseDir);

// Get list of all mask files
maskFiles = getFileList(masksDir);

// Create an array to store unique condition strings
conditionList = newArray();

// Extract unique conditions from ch1 files (stress granules)
for (i = 0; i < maskFiles.length; i++) {
    if (indexOf(maskFiles[i], "_ch1_") > 0 && endsWith(maskFiles[i], ".tif")) {
        // Extract the unique string part
        filename = maskFiles[i];
        // Remove "MASK_MAX_z-stack_" prefix
        temp = replace(filename, "MASK_MAX_z-stack_", "");
        // Remove "_Merged_ch1_t00.tif" suffix
        condition = replace(temp, "_Merged_ch1_t00.tif", "");
        conditionList = Array.concat(conditionList, condition);
    }
}

print("SG_TOTAL: " + conditionList.length);

// Process each condition
for (c = 0; c < conditionList.length; c++) {
    condition = conditionList[c];
    print("SG_CONDITION: " + (c + 1) + "/" + conditionList.length);
    print("Processing condition: " + condition);

    // Define file paths
    ch1MaskPath = masksDir + "MASK_MAX_z-stack_" + condition + "_Merged_ch1_t00.tif";
    ch1RawPath = rawDataDir + "MAX_z-stack_" + condition + "_Merged_ch1_t00.tif";

    // Check if all required files exist
    if (!File.exists(ch1MaskPath) || !File.exists(ch1RawPath)) {
        print("Skipping " + condition + " - missing files");
        continue;
    }

    // Create output directory for this condition
    conditionOutputDir = outputBaseDir + condition + File.separator;
    File.makeDirectory(conditionOutputDir);
    print("  Created output directory: " + conditionOutputDir);

    // Clear ROI Manager
    roiManager("reset");

    // Step 1: Open ch1 mask (stress granules)
    open(ch1MaskPath);
    ch1Title = getTitle();
    getStatistics(area, mean, min, max);
    print("  Ch1 image type: " + bitDepth() + "-bit");
    print("  Ch1 min/max: " + min + "/" + max);
    getThreshold(lower, upper);
    print("  Ch1 initial threshold: " + lower + "-" + upper);

    // Set threshold for binary mask (in case it's not already set)
    setThreshold(1, 255);
    setOption("BlackBackground", true);

    // Step 2: Analyze particles and get stress granule ROIs
    // Temporarily exit batch mode for ROI operations
    setBatchMode(false);
    run("Analyze Particles...", "size=0-Infinity add");
    numSGRois = roiManager("count");
    setBatchMode(true);
    print("  Found " + numSGRois + " stress granule ROIs");
    print("  DEBUG: ROI count = " + numSGRois);

    // Step 3: Save the stress granule ROI list
    if (numSGRois > 0) {
        roiOutputPath = conditionOutputDir + condition + "_SG_Mask.zip";
        print("  DEBUG: Attempting to save to: " + roiOutputPath);
        roiManager("Save", roiOutputPath);
        print("  Saved ROI list: " + roiOutputPath);

        // Step 4: Enlarge all ROIs by 5 pixels (note: different from PB which uses 2)
        for (r = 0; r < numSGRois; r++) {
            roiManager("select", r);
            run("Enlarge...", "enlarge=5 pixel");
            roiManager("update");
        }

        // Step 5: Save the dilated ROI list
        dilatedRoiOutputPath = conditionOutputDir + condition + "_SG_Dilated_Mask.zip";
        roiManager("Save", dilatedRoiOutputPath);
        print("  Saved dilated ROI list: " + dilatedRoiOutputPath);
    }

    // Close ch1 mask
    close(ch1Title);

    // Step 6: Copy the ch1 raw data image to output directory
    rawOutputPath = conditionOutputDir + condition + "_G3BP1_Intensity.tif";
    File.copy(ch1RawPath, rawOutputPath);
    print("  Copied raw data: " + rawOutputPath);

    // Clear ROI manager for next iteration
    roiManager("reset");
    print("Completed: " + condition);
    print("---");
}

// Exit batch mode
setBatchMode(false);

print("=================================");
print("SG processing complete!");
print("Output saved to: " + outputBaseDir);
print("=================================");
