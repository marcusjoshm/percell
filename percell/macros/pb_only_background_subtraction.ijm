// ImageJ Macro for P-body Only Analysis (No Stress Granules)
// Automated version for percell integration - no user interaction required
//
// This macro is filename-agnostic and works with any naming convention as long as:
//   - Files in Masks/ and Raw Data/ contain channel identifiers (ch2 or ch02)
//   - Corresponding mask and raw files have the same base name with different prefixes
//   - P-body files contain ch2 or ch02
//
// Expected directory structure:
// mainDir/
//   ├── Masks/           (containing mask files with ch2/ch02 channel identifiers)
//   ├── Raw Data/        (containing raw files with ch2/ch02 channel identifiers)
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

// Get list of all mask and raw files
maskFiles = getFileList(masksDir);
rawFiles = getFileList(rawDataDir);

// Build arrays to store ch2 mask files (Stress granules)
ch2MaskFiles = newArray();
for (i = 0; i < maskFiles.length; i++) {
    // Look for any file containing ch2 or ch02 (case insensitive for PB channel)
    if ((indexOf(toLowerCase(maskFiles[i]), "ch2") > 0 || indexOf(toLowerCase(maskFiles[i]), "ch02") > 0) && endsWith(maskFiles[i], ".tif")) {
        ch2MaskFiles = Array.concat(ch2MaskFiles, maskFiles[i]);
    }
}

print("PB_TOTAL: " + ch2MaskFiles.length);

// Process each ch2 mask file
for (fileIdx = 0; fileIdx < ch2MaskFiles.length; fileIdx++) {
    ch2MaskFile = ch2MaskFiles[fileIdx];
    print("PB_CONDITION: " + (fileIdx + 1) + "/" + ch2MaskFiles.length);

    ch2MaskPath = masksDir + ch2MaskFile;

    // Derive ch2 raw filename by removing "MASK_" prefix if present
    ch2RawFile = replace(ch2MaskFile, "MASK_", "");
    ch2RawPath = rawDataDir + ch2RawFile;

    // Extract condition name for output (remove MASK_ prefix and channel suffix)
    condition = ch2MaskFile;
    condition = replace(condition, "MASK_", "");
    condition = replace(condition, ".tif", "");
    // Remove channel and timepoint suffixes (works for both ch2 and ch02)
    if (indexOf(condition, "ch02") > 0) {
        idx = indexOf(condition, "ch02");
        condition = substring(condition, 0, idx - 1);  // -1 to remove underscore before ch
    } else if (indexOf(condition, "ch2") > 0) {
        idx = indexOf(condition, "ch2");
        condition = substring(condition, 0, idx - 1);
    }

    print("Processing condition: " + condition);
    print("  Ch1 mask: " + ch2MaskFile);
    print("  Ch1 raw: " + ch2RawFile);

    // Check if all required files exist
    if (!File.exists(ch2MaskPath)) {
        print("  WARNING: Ch1 mask not found: " + ch2MaskFile);
        print("  Skipping " + condition);
        continue;
    }
    if (!File.exists(ch2RawPath)) {
        print("  WARNING: Ch1 raw not found: " + ch2RawFile);
        print("  Skipping " + condition);
        continue;
    }

    // Create output directory for this condition
    conditionOutputDir = outputBaseDir + condition + File.separator;
    File.makeDirectory(conditionOutputDir);
    print("  Created output directory: " + conditionOutputDir);

    // Clear ROI Manager
    roiManager("reset");

    // Step 1: Open ch2 mask (p-bodys)
    open(ch2MaskPath);
    ch2Title = getTitle();
    getStatistics(area, mean, min, max);
    print("  Ch1 image type: " + bitDepth() + "-bit");
    print("  Ch1 min/max: " + min + "/" + max);
    getThreshold(lower, upper);
    print("  Ch1 initial threshold: " + lower + "-" + upper);

    // Set threshold for binary mask (in case it's not already set)
    setThreshold(1, 255);
    setOption("BlackBackground", true);

    // Step 2: Analyze particles and get p-body ROIs
    // Temporarily exit batch mode for ROI operations
    setBatchMode(false);
    run("Analyze Particles...", "size=0-Infinity add");
    numPBRois = roiManager("count");
    setBatchMode(true);
    print("  Found " + numPBRois + " p-body ROIs");
    print("  DEBUG: ROI count = " + numPBRois);

    // Step 3: Save the p-body ROI list
    if (numPBRois > 0) {
        roiOutputPath = conditionOutputDir + condition + "_PB_Mask.zip";
        print("  DEBUG: Attempting to save to: " + roiOutputPath);
        roiManager("Save", roiOutputPath);
        print("  Saved ROI list: " + roiOutputPath);

        // Step 4: Enlarge all ROIs by 5 pixels (note: different from PB which uses 2)
        for (r = 0; r < numPBRois; r++) {
            roiManager("select", r);
            run("Enlarge...", "enlarge=5 pixel");
            roiManager("update");
        }

        // Step 5: Save the dilated ROI list
        dilatedRoiOutputPath = conditionOutputDir + condition + "_PB_Dilated_Mask.zip";
        roiManager("Save", dilatedRoiOutputPath);
        print("  Saved dilated ROI list: " + dilatedRoiOutputPath);
    }

    // Close ch2 mask
    close(ch2Title);

    // Step 6: Copy the ch2 raw data image to output directory
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

// Signal macro completion to the Python adapter
print("MACRO_DONE");
run("Quit");
