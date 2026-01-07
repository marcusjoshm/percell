// ImageJ Macro for P-body Analysis with Stress Granule Subtraction
// Automated version for percell integration - no user interaction required
//
// Expected directory structure:
// mainDir/
//   ├── Masks/           (containing MASK_MAX_z-stack_*_ch1_*.tif and *_ch2_*.tif)
//   ├── Raw Data/        (containing MAX_z-stack_*_ch1_*.tif and *_ch2_*.tif)
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

// Extract unique conditions from ch2 files (p-bodies)
for (i = 0; i < maskFiles.length; i++) {
    if (indexOf(maskFiles[i], "_ch2_") > 0 && endsWith(maskFiles[i], ".tif")) {
        // Extract the unique string part
        filename = maskFiles[i];
        // Remove "MASK_MAX_z-stack_" prefix
        temp = replace(filename, "MASK_MAX_z-stack_", "");
        // Remove "_Merged_ch2_t00.tif" suffix
        condition = replace(temp, "_Merged_ch2_t00.tif", "");
        conditionList = Array.concat(conditionList, condition);
    }
}

print("PB_TOTAL: " + conditionList.length);

// Process each condition
for (c = 0; c < conditionList.length; c++) {
    condition = conditionList[c];
    print("PB_CONDITION: " + (c + 1) + "/" + conditionList.length);
    print("Processing condition: " + condition);

    // Define file paths
    ch1MaskPath = masksDir + "MASK_MAX_z-stack_" + condition + "_Merged_ch1_t00.tif";
    ch2MaskPath = masksDir + "MASK_MAX_z-stack_" + condition + "_Merged_ch2_t00.tif";
    ch2RawPath = rawDataDir + "MAX_z-stack_" + condition + "_Merged_ch2_t00.tif";

    // Check if all required files exist
    if (!File.exists(ch1MaskPath) || !File.exists(ch2MaskPath) || !File.exists(ch2RawPath)) {
        print("Skipping " + condition + " - missing files");
        continue;
    }

    // Create output directory for this condition
    conditionOutputDir = outputBaseDir + condition + File.separator;
    File.makeDirectory(conditionOutputDir);
    print("  Created output directory: " + conditionOutputDir);

    // Clear ROI Manager
    roiManager("reset");

    // Step 1: Open ch1 mask (stress granules) and get ROIs
    open(ch1MaskPath);
    ch1Title = getTitle();
    // For binary masks, just analyze directly without threshold conversion
    // Temporarily exit batch mode for ROI operations
    setBatchMode(false);
    run("Analyze Particles...", "size=0-Infinity add");
    numSGRois = roiManager("count");
    setBatchMode(true);
    print("  Found " + numSGRois + " stress granule ROIs");
    print("  DEBUG: SG ROI count = " + numSGRois);

    // Close ch1
    close(ch1Title);

	// Step 2: Open ch2 mask (p-bodies)
	open(ch2MaskPath);
	ch2Title = getTitle();
	getStatistics(area, mean, min, max);
	print("  Ch2 image type: " + bitDepth() + "-bit");
	print("  Ch2 min/max: " + min + "/" + max);
	getThreshold(lower, upper);
	print("  Ch2 initial threshold: " + lower + "-" + upper);

	// Set threshold for binary mask (in case it's not already set)
	setThreshold(1, 255);
	setOption("BlackBackground", true);

    // Step 3: Subtract stress granule regions from p-bodies
    if (numSGRois > 0) {
        roiManager("Combine");
        run("Clear", "slice");
        run("Select None");
    }

    // Clear ROI manager and analyze the subtracted p-body mask
    roiManager("reset");
    // Temporarily exit batch mode for ROI operations
    setBatchMode(false);
    run("Analyze Particles...", "size=0-Infinity add");
    numPBodyRois = roiManager("count");
    setBatchMode(true);
    print("  Found " + numPBodyRois + " p-body ROIs after subtraction");
    print("  DEBUG: ROI count = " + numPBodyRois);

    // Step 4: Save the p-body ROI list (with "Mask" in name)
    if (numPBodyRois > 0) {
        roiOutputPath = conditionOutputDir + condition + "_PB_Mask.zip";
        print("  DEBUG: Attempting to save to: " + roiOutputPath);
        roiManager("Save", roiOutputPath);
        print("  Saved ROI list: " + roiOutputPath);

        // Step 5: Enlarge all ROIs by 2 pixels
        for (r = 0; r < numPBodyRois; r++) {
            roiManager("select", r);
            run("Enlarge...", "enlarge=2 pixel");
            roiManager("update");
        }

        // Step 6: Save the dilated ROI list (with "Dilated" and "Mask" in name)
        dilatedRoiOutputPath = conditionOutputDir + condition + "_PB_Dilated_Mask.zip";
        roiManager("Save", dilatedRoiOutputPath);
        print("  Saved dilated ROI list: " + dilatedRoiOutputPath);
    }

    // Close ch2 mask
    close(ch2Title);

    // Step 7: Copy the ch2 raw data image to output directory (with "Intensity" in name)
    rawOutputPath = conditionOutputDir + condition + "_DDX6_Intensity.tif";
    File.copy(ch2RawPath, rawOutputPath);
    print("  Copied raw data: " + rawOutputPath);

    // Clear ROI manager for next iteration
    roiManager("reset");
    print("Completed: " + condition);
    print("---");
}

// Exit batch mode
setBatchMode(false);

print("=================================");
print("PB processing complete!");
print("Output saved to: " + outputBaseDir);
print("=================================");
