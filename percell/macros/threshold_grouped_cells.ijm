// Threshold Grouped Cells Macro for Single Cell Analysis Workflow
// This macro thresholds grouped cell images to create masks
// Parameters are passed from the Python script

#@ String input_dir
#@ String output_dir
#@ String flag_file
#@ Boolean auto_close

// Enable batch mode for better performance
setBatchMode(false); // Keep this false for user interaction

// Validate input parameters
if (input_dir == "") {
    exit("Error: Input directory not specified");
}
if (output_dir == "") {
    exit("Error: Output directory not specified");
}

print("=== Threshold Grouped Cells Macro Started ===");
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
needMoreBinsFlag = false;
binFileCount = 0;

print("cellsDir: " + cellsDir);
print("outputDir: " + outputDir);

// Get list of condition directories in cellsDir
print("Debug - About to call getFileList on: " + cellsDir);
print("Debug - Directory exists: " + File.exists(cellsDir));
print("Debug - Is directory: " + File.isDirectory(cellsDir));

conditionDirs = getFileList(cellsDir);
print("Found condition directories: " + joinArray(conditionDirs, ", "));
print("Debug - cellsDir path: " + cellsDir);
print("Debug - conditionDirs array length: " + conditionDirs.length);

// Check each condition directory individually
for (debug_i = 0; debug_i < conditionDirs.length; debug_i++) {
    debug_condition = conditionDirs[debug_i];
    debug_path = cellsDir + debug_condition;
    print("Debug - Condition " + debug_i + ": '" + debug_condition + "'");
    print("Debug - Full path: '" + debug_path + "'");
    print("Debug - Exists: " + File.exists(debug_path));
    print("Debug - Is directory: " + File.isDirectory(debug_path));
    print("Debug - Starts with dot: " + startsWith(debug_condition, "."));
}

// Skip initial image preview - proceed directly to thresholding
print("Proceeding directly to thresholding without preview.");

// Process each condition directory
for (d = 0; d < conditionDirs.length; d++) {
    conditionName = conditionDirs[d];
    
    // Remove trailing slash from conditionName for directory checking
    cleanConditionName = conditionName;
    if (endsWith(cleanConditionName, "/")) {
        cleanConditionName = substring(cleanConditionName, 0, lengthOf(cleanConditionName) - 1);
    }
    
    print("Debug - conditionName: " + conditionName);
    print("Debug - cleanConditionName: " + cleanConditionName);
    print("Debug - cellsDir: " + cellsDir);
    
    // Ensure cellsDir has a trailing slash for proper path construction
    if (!endsWith(cellsDir, "/")) {
        cellsDir = cellsDir + "/";
    }
    
    print("Debug - cellsDir with trailing slash: " + cellsDir);
    print("Debug - cellsDir + cleanConditionName: " + cellsDir + cleanConditionName);
    print("Debug - File.exists(cellsDir + cleanConditionName): " + File.exists(cellsDir + cleanConditionName));
    print("Debug - File.isDirectory(cellsDir + cleanConditionName): " + File.isDirectory(cellsDir + cleanConditionName));
    
    // Skip non-directories and hidden files
    if (!File.isDirectory(cellsDir + cleanConditionName) || startsWith(cleanConditionName, ".")) {
        print("Debug - Skipping " + cleanConditionName + " (not a directory or hidden)");
        continue;
    }
    
    conditionPath = cellsDir + cleanConditionName + "/";
    // Clean up any double slashes but keep trailing slash
    conditionPath = replace(conditionPath, "//", "/");
    print("Processing condition: " + conditionPath);
    print("Debug - conditionPath for getFileList: " + conditionPath);
    
    // Get list of region/channel/timepoint subdirectories within the condition folder
    print("Debug - About to call getFileList on condition: " + conditionPath);
    print("Debug - Condition path exists: " + File.exists(conditionPath));
    print("Debug - Condition is directory: " + File.isDirectory(conditionPath));
    
    regionDirs = getFileList(conditionPath);
    print("Debug - regionDirs array length: " + regionDirs.length);
    print("Debug - regionDirs content: " + joinArray(regionDirs, ", "));
    
    // Check each region directory individually
    for (debug_r = 0; debug_r < regionDirs.length; debug_r++) {
        debug_region = regionDirs[debug_r];
        debug_region_path = conditionPath + debug_region;
        print("Debug - Region " + debug_r + ": '" + debug_region + "'");
        print("Debug - Region full path: '" + debug_region_path + "'");
        print("Debug - Region exists: " + File.exists(debug_region_path));
        print("Debug - Region is directory: " + File.isDirectory(debug_region_path));
        print("Debug - Region starts with dot: " + startsWith(debug_region, "."));
    }
    
    if (regionDirs.length == 0) {
        print("No subdirectories found in " + conditionName);
        print("Debug - Trying to list directory contents manually...");
        // Try alternative approach to list directory contents
        testPath = conditionPath;
        if (!endsWith(testPath, "/")) testPath = testPath + "/";
        print("Debug - Testing path: " + testPath);
        print("Debug - Directory exists: " + File.exists(testPath));
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
        // Temporarily disabled for debugging - no channel filtering applied
        
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
        print("Looking for files with '_bin_' pattern...");
        
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
                
                // Set the oval selection tool
                setTool("oval");
                
                // Wait for the user to draw an ROI for thresholding
                waitForUser("Draw ROI for thresholding", "Please draw an oval ROI in a representative area for thresholding, then click OK.");
                
                // Check if user drew an ROI
                if (selectionType() == -1) {
                    // No selection was made, prompt again
                    waitForUser("No ROI detected", "Please draw an oval ROI to select an area for thresholding, then click OK.");
                    
                    // If still no selection, use the entire image
                    if (selectionType() == -1) {
                        print("No ROI drawn, using the entire image for thresholding.");
                        run("Select All");
                    }
                }
                
                // After ROI selection but before thresholding, ask if more bins are needed
                Dialog.create("Evaluate Cell Grouping");
                Dialog.addMessage("Based on what you see in this image, do you want to:");
                Dialog.addChoice("Decision:", newArray(
                    "Continue with thresholding", 
                    "Go back and add one more group",
                    "Ignore thresholding for this group. There are no structures to threshold in the field"
                ));
                Dialog.show();
                
                userBinsDecision = Dialog.getChoice();
                
                // If user wants more bins, create flag file and exit
                if (userBinsDecision == "Go back and add one more group") {
                    File.saveString("User requested more bins for better cell grouping", flag_file);
                    showMessage("More Bins Requested", "Your request for more bins has been recorded. The workflow will restart the cell grouping step with more bins.");
                    run("Close All");
                    run("Quit");
                }
                
                // Handle case when there are no structures to threshold
                if (userBinsDecision == "Ignore thresholding for this group. There are no structures to threshold in the field") {
                    print("User indicated no structures to threshold - creating empty mask");
                    
                    // Create a completely black mask (all pixels = 0)
                    run("Select All");
                    run("Clear", "slice");
                    
                    // Make sure we have a binary image with all black pixels
                    setOption("BlackBackground", true);
                    // Skip Convert to Mask which would turn it to 255 values
                    // Instead manually set as 8-bit binary image with all zeros
                    run("8-bit");
                    setMinAndMax(0, 0);
                    run("Apply LUT", "slice");
                } else {
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
                }
                
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
                
                print("Step 1: Creating condition directory: " + conditionOutputDir);
                if (!File.exists(conditionOutputDir)) {
                    File.makeDirectory(conditionOutputDir);
                    if (File.exists(conditionOutputDir)) {
                        print("Successfully created condition directory");
                    } else {
                        print("Failed to create condition directory");
                    }
                } else {
                    print("Condition directory already exists");
                }
                
                // Then create the region directory
                print("Step 2: Creating region directory: " + outFolder);
                if (!File.exists(outFolder)) {
                    File.makeDirectory(outFolder);
                    if (File.exists(outFolder)) {
                        print("Successfully created region directory");
                    } else {
                        print("Failed to create region directory");
                    }
                } else {
                    print("Region directory already exists");
                }
                
                // Save the processed image with "MASK_" prepended
                outputPath = outFolder + "MASK_" + fileName;
                
                // Add debug information before saving
                print("Attempting to save to: " + outputPath);
                print("Output path length: " + lengthOf(outputPath));
                print("Parent directory exists: " + File.exists(outFolder));
                print("Parent is directory: " + File.isDirectory(outFolder));
                
                // Test write permissions in the directory
                testFilePath = outFolder + "test_write.tmp";
                File.saveString("test", testFilePath);
                if (File.exists(testFilePath)) {
                    File.delete(testFilePath);
                    print("Directory write test: SUCCESS");
                } else {
                    print("Directory write test: FAILED - may not be writable");
                }
                
                // Try to save the image with error handling
                saveSuccess = false;
                
                // First attempt: Normal save
                print("Attempting primary save method...");
                // Use try/catch equivalent by checking if save worked
                saveAs("Tiff", outputPath);
                if (File.exists(outputPath)) {
                    print("Primary save successful: " + outputPath);
                    saveSuccess = true;
                } else {
                    print("Primary save failed - file not found after save attempt");
                    
                    // Second attempt: Try saving with shorter filename
                    print("Attempting fallback save with shorter filename...");
                    shortFileName = "MASK_" + d + "_" + t + "_" + f + ".tif";
                    alternativePath = outFolder + shortFileName;
                    print("Alternative path: " + alternativePath);
                    
                    saveAs("Tiff", alternativePath);
                    if (File.exists(alternativePath)) {
                        print("Fallback save successful: " + alternativePath);
                        saveSuccess = true;
                    } else {
                        print("Fallback save also failed");
                        
                        // Third attempt: Save to local temp directory first
                        print("Attempting save to local temp directory...");
                        tempDir = "/tmp/imagej_temp/";
                        if (!File.exists(tempDir)) {
                            File.makeDirectory(tempDir);
                        }
                        tempFileName = "MASK_temp_" + d + "_" + t + "_" + f + ".tif";
                        tempPath = tempDir + tempFileName;
                        print("Temp path: " + tempPath);
                        
                        saveAs("Tiff", tempPath);
                        if (File.exists(tempPath)) {
                            print("Temp save successful: " + tempPath);
                            print("Note: File saved to temp location due to path issues");
                            print("Manual copy needed: " + tempPath + " -> " + outputPath);
                            saveSuccess = true;
                        } else {
                            // Fourth attempt: Save to emergency directory with short names
                            print("Attempting emergency save to simplified path...");
                            emergencyDir = outputDir + "/emergency_saves/";
                            if (!File.exists(emergencyDir)) {
                                File.makeDirectory(emergencyDir);
                            }
                            emergencyPath = emergencyDir + "MASK_" + d + "_" + t + "_" + f + ".tif";
                            emergencyPath = replace(emergencyPath, "//", "/");
                            print("Emergency path: " + emergencyPath);
                            
                            saveAs("Tiff", emergencyPath);
                            if (File.exists(emergencyPath)) {
                                print("Emergency save successful: " + emergencyPath);
                                saveSuccess = true;
                            } else {
                                print("All save attempts failed!");
                            }
                        }
                    }
                }
                
                if (!saveSuccess) {
                    print("ERROR: Could not save file anywhere. Skipping this image.");
                }
                
                // Close the image
                close();
            }
        }
    }
}

print("Thresholding of grouped cells completed.");
print("Total bin files processed: " + binFileCount);
print("=== Threshold Grouped Cells Macro Completed ===");

// Auto-close ImageJ if requested
if (auto_close) {
    print("Auto-close requested - closing ImageJ...");
    // Close all windows first
    run("Close All");
    // Use run("Quit") which is more reliable than System.exit on Windows
    run("Quit");
}