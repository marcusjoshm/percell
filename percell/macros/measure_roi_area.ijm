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
    
    // Measure all ROIs
    roiManager("Deselect");
    print("DEBUG: About to measure " + num_rois + " ROIs");
    roiManager("Measure");
    print("DEBUG: Measurement completed");
    
    // Get the base image name for identification
    image_basename = File.getName(image_file);
    if (endsWith(image_basename, ".tif")) {
        image_basename = substring(image_basename, 0, lengthOf(image_basename) - 4);
    } else if (endsWith(image_basename, ".tiff")) {
        image_basename = substring(image_basename, 0, lengthOf(image_basename) - 5);
    }
    
    // Add image identifier and cell numbers to results table
    for (i = 0; i < num_rois; i++) {
        // Get ROI name first
        roiManager("Select", i);
        roi_name = Roi.getName();
        
        // Create sequential cell ID (CELL1, CELL2, CELL3, etc.)
        cell_number = "CELL" + (i + 1);
        
        // Debug: print ROI name and assigned cell number
        print("ROI " + (i+1) + ": " + roi_name + " -> " + cell_number);
        print("MEASURE_ROI: " + (i+1) + "/" + num_rois);
        
        // Get the area value from the results table (ImageJ uses 1-based indexing)
        area_value = getResult("Area", i + 1);
        print("DEBUG: ROI " + (i+1) + " area: " + area_value);
        
        // Set all columns for this row (ImageJ uses 1-based indexing)
        setResult("Image", i + 1, image_basename);
        setResult("Label", i + 1, roi_name);
        setResult("Cell_ID", i + 1, cell_number);
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

// Auto-close ImageJ if requested
if (auto_close) {
    run("Quit");
}