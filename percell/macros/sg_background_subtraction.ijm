// ImageJ Macro for Stress Granule Analysis
// Automated version for percell integration - no user interaction required
//
// This macro is filename-agnostic and works with any naming convention as long as:
//   - Files in Masks/ and Raw Data/ contain channel identifiers (ch1 or ch01)
//   - Corresponding mask and raw files have the same base name with different prefixes
//   - Stress granule files contain ch1 or ch01
//
// Expected directory structure:
// mainDir/
//   ├── Masks/           (containing mask files with ch1/ch01 channel identifiers)
//   ├── Raw Data/        (containing raw files with ch1/ch01 channel identifiers)
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

// Build arrays to store ch1 mask files (Stress granules)
ch1MaskFiles = newArray();
for (i = 0; i < maskFiles.length; i++) {
    // Look for any file containing ch1 or ch01 (case insensitive for SG channel)
    if ((indexOf(toLowerCase(maskFiles[i]), "ch1") > 0 || indexOf(toLowerCase(maskFiles[i]), "ch01") > 0) && endsWith(maskFiles[i], ".tif")) {
        ch1MaskFiles = Array.concat(ch1MaskFiles, maskFiles[i]);
    }
}

print("SG_TOTAL: " + ch1MaskFiles.length);

// Process each ch1 mask file
for (fileIdx = 0; fileIdx < ch1MaskFiles.length; fileIdx++) {
    ch1MaskFile = ch1MaskFiles[fileIdx];
    print("SG_CONDITION: " + (fileIdx + 1) + "/" + ch1MaskFiles.length);

    ch1MaskPath = masksDir + ch1MaskFile;

    // Derive ch1 raw filename by removing "MASK_" prefix if present
    ch1RawFile = replace(ch1MaskFile, "MASK_", "");
    ch1RawPath = rawDataDir + ch1RawFile;

    // Extract condition name for output (remove MASK_ prefix and channel suffix)
    condition = ch1MaskFile;
    condition = replace(condition, "MASK_", "");
    condition = replace(condition, ".tif", "");
    // Remove channel and timepoint suffixes (works for both ch1 and ch01)
    if (indexOf(condition, "ch01") > 0) {
        idx = indexOf(condition, "ch01");
        condition = substring(condition, 0, idx - 1);  // -1 to remove underscore before ch
    } else if (indexOf(condition, "ch1") > 0) {
        idx = indexOf(condition, "ch1");
        condition = substring(condition, 0, idx - 1);
    }

    print("Processing condition: " + condition);
    print("  Ch1 mask: " + ch1MaskFile);
    print("  Ch1 raw: " + ch1RawFile);

    // Check if all required files exist
    if (!File.exists(ch1MaskPath)) {
        print("  WARNING: Ch1 mask not found: " + ch1MaskFile);
        print("  Skipping " + condition);
        continue;
    }
    if (!File.exists(ch1RawPath)) {
        print("  WARNING: Ch1 raw not found: " + ch1RawFile);
        print("  Skipping " + condition);
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

// Signal macro completion to the Python adapter
print("MACRO_DONE");
run("Quit");
