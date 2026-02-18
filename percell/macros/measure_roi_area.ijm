// Measure ROI Area Macro for Single Cell Analysis Workflow
// This macro opens an ROI list and corresponding raw data file, then measures ROI areas
// Parameters are passed from the Python script

#@ String roi_file
#@ String image_file
#@ String csv_file
#@ Boolean auto_close

// Enable batch mode for better performance
setBatchMode(true);

// Validate input parameters
if (roi_file == "") {
    exit("Error: ROI file not specified");
}
if (image_file == "") {
    exit("Error: Image file not specified");
}
if (csv_file == "") {
    exit("Error: CSV output file not specified");
}

print("=== Measure ROI Area Macro Started ===");
print("ROI file: " + roi_file);
print("Image file: " + image_file);
print("CSV output file: " + csv_file);
print("Auto close: " + auto_close);

// Check if ROI file exists
if (!File.exists(roi_file)) {
    exit("Error: ROI file does not exist: " + roi_file);
}

// Check if image file exists
if (!File.exists(image_file)) {
    exit("Error: Image file does not exist: " + image_file);
}

print("MEASUREMENT_START:" + image_file);

// Open the image file
open(image_file);
image_name = getTitle();
print("Opened image: " + image_name);

// Open ROI Manager and load ROIs
run("ROI Manager...");
roiManager("Open", roi_file);
num_rois = roiManager("count");
print("Loaded " + num_rois + " ROIs from: " + roi_file);
print("MEASURE_TOTAL: " + num_rois);

// Debug: List all ROI names to verify they're loaded correctly
for (i = 0; i < num_rois; i++) {
    roiManager("Select", i);
    roi_name = Roi.getName();
    print("DEBUG: ROI " + (i+1) + " name: " + roi_name);
}

if (num_rois == 0) {
    print("Warning: No ROIs found in file");
} else {
    // Clear any existing measurements
    run("Clear Results");
    
    // Set measurements to include area (similar to particle analysis)
    run("Set Measurements...", "area display redirect=None decimal=3");
    
    // Get the base image name for identification
    image_basename = File.getName(image_file);
    if (endsWith(image_basename, ".tif")) {
        image_basename = substring(image_basename, 0, lengthOf(image_basename) - 4);
    } else if (endsWith(image_basename, ".tiff")) {
        image_basename = substring(image_basename, 0, lengthOf(image_basename) - 5);
    }
    
    // Clear any existing measurements and manually build results table
    run("Clear Results");
    
    // Set measurements to include area
    run("Set Measurements...", "area display redirect=None decimal=3");
    
    print("DEBUG: Building results table manually for " + num_rois + " ROIs");
    
    // Measure each ROI and manually add to results table
    for (i = 0; i < num_rois; i++) {
        // Select ROI
        roiManager("Select", i);
        roi_name = Roi.getName();
        
        // Get area using getStatistics instead of Measure
        getStatistics(area, mean, min, max, std, histogram);
        
        // Create sequential cell ID (CELL1, CELL2, CELL3, etc.)
        cell_number = "CELL" + (i + 1);
        
        // Debug: print ROI name and assigned cell number
        print("ROI " + (i+1) + ": " + roi_name + " -> " + cell_number + " (Area: " + area + ")");
        print("MEASURE_ROI: " + (i+1) + "/" + num_rois);
        
        // Manually add this measurement to the results table
        setResult("Label", i, roi_name);
        setResult("Area", i, area);
        setResult("Image", i, image_basename);
        setResult("Cell_ID", i, cell_number);
    }
    
    // Update the results table after all measurements
    updateResults();
    
    // Check final results
    final_count = nResults;
    print("DEBUG: Final results table has " + final_count + " rows");
    
    // Debug: show first few and last few entries
    if (final_count > 0) {
        print("DEBUG: First entry - Label: " + getResultString("Label", 0) + ", Area: " + getResult("Area", 0));
        if (final_count > 1) {
            print("DEBUG: Last entry - Label: " + getResultString("Label", final_count-1) + ", Area: " + getResult("Area", final_count-1));
        }
    }
    updateResults();
    
    // Save the results as CSV
    print("Saving measurements to: " + csv_file);
    saveAs("Results", csv_file);
    
    print("Successfully measured " + num_rois + " ROIs");
}

print("MEASUREMENT_END:" + image_file);

// Close ROI Manager
if (isOpen("ROI Manager")) {
    selectWindow("ROI Manager");
    run("Close");
}

// Close Results window
if (isOpen("Results")) {
    selectWindow("Results");
    run("Close");
}

// Close all open images
while (nImages > 0) {
    selectImage(nImages);
    close();
}

print("MACRO_COMPLETE");
print("=== Measure ROI Area Macro Completed ===");

// Turn off batch mode
setBatchMode(false);

// Signal macro completion to the Python adapter
print("MACRO_DONE");

// Auto-close ImageJ if requested
if (auto_close) {
    run("Quit");
}