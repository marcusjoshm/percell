// Full Auto Threshold Grouped Cells Macro for Single Cell Analysis Workflow
// This macro automatically thresholds grouped cell images to create masks without user interaction
// Parameters are passed from the Python script

#@ String input_dir
#@ String output_dir
#@ Boolean auto_close

// Enable batch mode for better performance
setBatchMode(true);

// Validate input parameters
if (input_dir == "") {
    exit("Error: Input directory not specified");
}
if (output_dir == "") {
    exit("Error: Output directory not specified");
}

print("=== Full Auto Threshold Grouped Cells Macro Started ===");
print("Input directory: " + input_dir);
print("Output directory: " + output_dir);
print("Auto close: " + auto_close);

// Helper function to join array elements with a separator
function joinArray(arr, separator) {
    s = "";
    for (i = 0; i < arr.length; i++) {
        s += arr[i];
        if (i < arr.length - 1)
            s += separator;
    }
    return s;
}

// Helper function to ensure proper path construction
function ensurePath(path) {
    // Remove any double slashes and ensure proper path format
    path = replace(path, "//", "/");
    // Ensure no trailing slash for directory creation
    if (endsWith(path, "/")) {
        path = substring(path, 0, lengthOf(path) - 1);
    }
    return path;
}

// Configuration from parameters
cellsDir = ensurePath(input_dir);
if (!endsWith(cellsDir, "/")) cellsDir = cellsDir + "/";
outputDir = ensurePath(output_dir);
if (!endsWith(outputDir, "/")) outputDir = outputDir + "/";
binFileCount = 0;

print("cellsDir: " + cellsDir);
print("outputDir: " + outputDir);

// Get list of condition directories in cellsDir
conditionDirs = getFileList(cellsDir);
print("Found condition directories: " + joinArray(conditionDirs, ", "));

// Process each condition directory
for (d = 0; d < conditionDirs.length; d++) {
    conditionName = conditionDirs[d];

    // Remove trailing slash from conditionName for directory checking
    cleanConditionName = conditionName;
    if (endsWith(cleanConditionName, "/")) {
        cleanConditionName = substring(cleanConditionName, 0, lengthOf(cleanConditionName) - 1);
    }

    // Skip non-directories and hidden files
    if (!File.isDirectory(cellsDir + cleanConditionName) || startsWith(cleanConditionName, ".")) {
        continue;
    }

    conditionPath = cellsDir + cleanConditionName + "/";
    // Clean up any double slashes but keep trailing slash
    conditionPath = replace(conditionPath, "//", "/");
    print("Processing condition: " + conditionPath);

    // Get list of region/channel/timepoint subdirectories within the condition folder
    regionDirs = getFileList(conditionPath);

    if (regionDirs.length == 0) {
        print("No subdirectories found in " + conditionName);
        continue;
    }

    print("Found region subdirectories in " + conditionName + ": " + joinArray(regionDirs, ", "));

    for (t = 0; t < regionDirs.length; t++) {
        regionName = regionDirs[t];

        // Skip non-directories and hidden files
        if (!File.isDirectory(conditionPath + regionName) || startsWith(regionName, ".")) {
            continue;
        }

        print("Processing region: " + regionName);

        // Channel filtering logic will be embedded here by Python script
        // CHANNEL_FILTER_PLACEHOLDER

        regionPath = conditionPath + regionName + "/";
        // Clean up any double slashes but keep trailing slash
        regionPath = replace(regionPath, "//", "/");
        print("Processing region folder: " + regionPath);

        // Get list of files in the region folder
        files = getFileList(regionPath);
        if (files.length == 0) {
            print("No files found in " + regionName);
            continue;
        }

        print("Found files in " + regionName + ": " + joinArray(files, ", "));

        for (f = 0; f < files.length; f++) {
            fileName = files[f];

            // Process only bin TIFF files (skip CSV and txt files)
            if (endsWith(fileName, ".tif") && indexOf(fileName, "_bin_") >= 0) {
                binFileCount++;
                imagePath = regionPath + fileName;
                print("Found bin file: " + fileName);
                print("Opening file: " + imagePath);

                // Open the image
                open(imagePath);

                // Clear any existing ROI that might be embedded in the file
                run("Select None");

                // Image processing steps - Apply Gaussian blur first for better contrast enhancement
                run("Gaussian Blur...", "sigma=1.70");
                run("Enhance Contrast...", "saturated=0.01");

                // Ensure we're working with the correct image
                imageTitle = getTitle();
                selectWindow(imageTitle);

                // Convert to appropriate bit depth if needed for consistent processing
                if (bitDepth() == 16) {
                    print("Converting 16-bit image to 8-bit for thresholding");
                    run("8-bit");
                }

                // Use entire image for thresholding (no user ROI selection)
                run("Select All");

                // Apply Otsu thresholding - use appropriate method for image type
                if (bitDepth() == 8) {
                    setAutoThreshold("Otsu dark");
                } else {
                    setAutoThreshold("Otsu dark 16-bit");
                }

                // Convert to mask
                setOption("BlackBackground", true);
                run("Convert to Mask");

                // Ensure mask is properly formatted (binary 8-bit)
                run("8-bit");

                // Create matching output directory structure with proper path handling
                // Ensure we don't have double slashes and proper path construction
                outFolder = outputDir;
                if (!endsWith(outFolder, "/")) outFolder = outFolder + "/";
                outFolder = outFolder + conditionName + "/";
                if (!endsWith(outFolder, "/")) outFolder = outFolder + "/";
                outFolder = outFolder + regionName + "/";
                // Clean up any double slashes
                outFolder = replace(outFolder, "//", "/");

                // Create directories step by step since ImageJ can't create nested paths
                // First create the condition directory
                conditionOutputDir = outputDir;
                if (!endsWith(conditionOutputDir, "/")) conditionOutputDir = conditionOutputDir + "/";
                conditionOutputDir = conditionOutputDir + conditionName;
                if (endsWith(conditionOutputDir, "/")) {
                    conditionOutputDir = substring(conditionOutputDir, 0, lengthOf(conditionOutputDir) - 1);
                }

                if (!File.exists(conditionOutputDir)) {
                    File.makeDirectory(conditionOutputDir);
                }

                // Then create the region directory
                if (!File.exists(outFolder)) {
                    File.makeDirectory(outFolder);
                }

                // Save the processed image with "MASK_" prepended
                outputPath = outFolder + "MASK_" + fileName;

                print("Saving to: " + outputPath);

                // Save the image
                saveAs("Tiff", outputPath);

                if (File.exists(outputPath)) {
                    print("Successfully saved: " + outputPath);
                } else {
                    print("Warning: Failed to save " + outputPath);
                }

                // Close the image
                close();
            }
        }
    }
}

print("Thresholding of grouped cells completed.");
print("Total bin files processed: " + binFileCount);
print("=== Full Auto Threshold Grouped Cells Macro Completed ===");

// Auto-close ImageJ if requested
if (auto_close) {
    print("Auto-close requested - closing ImageJ...");
    // Close all windows first
    run("Close All");
    // Use run("Quit") which is more reliable than System.exit on Windows
    run("Quit");
}
