// Extract Cells Macro for Single Cell Analysis Workflow
// This macro extracts individual cells from an image file using ROIs
// Parameters are passed from the Python script

#@ String roi_file
#@ String image_file
#@ String output_dir
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
if (output_dir == "") {
    exit("Error: Output directory not specified");
}

print("=== Extract Cells Macro Started ===");
print("ROI file: " + roi_file);
print("Image file: " + image_file);
print("Output directory: " + output_dir);
print("Auto close: " + auto_close);

// Create output directory if it doesn't exist
File.makeDirectory(output_dir);

// Reset ROI Manager
roiManager("reset");

// Open ROIs
print("Opening ROI file");
roiManager("Open", roi_file);
roi_count = roiManager("count");
print("Found " + roi_count + " ROIs");
print("EXTRACT_TOTAL: " + roi_count);

if (roi_count == 0) {
    print("No ROIs found in file: " + roi_file);
    exit("No ROIs found");
}

// Open the image
print("Opening image file");
open(image_file);
if (nImages == 0) {
    print("Failed to open image: " + image_file);
    exit("Failed to open image");
}

// Get the title of the open image
regionTitle = getTitle();
print("Image opened: " + regionTitle);

// Process each ROI
for (i = 0; i < roi_count; i++) {
    // Duplicate the region image so the original remains unaltered
    selectWindow(regionTitle);
    run("Duplicate...", "title=TempRegion duplicate");
    
    // Apply the ROI (from the ROI Manager) to the duplicate
    roiManager("select", i);
    nslices = nSlices();
    for (s = 1; s <= nslices; s++) {
        setSlice(s);
        run("Clear Outside");
    }
    
    // Save the cell
    cell_num = i + 1;
    cell_path = output_dir + "/CELL" + cell_num + ".tif";
    print("Saving cell " + cell_num + " to: " + cell_path);
    print("EXTRACT_CELL: " + (i+1) + "/" + roi_count);
    saveAs("Tiff", cell_path);
    
    // Close the duplicate
    close();
}

// Close the original image
selectWindow(regionTitle);
close();

// Clear ROI Manager
roiManager("reset");

// Turn off batch mode
setBatchMode(false);

print("Cell extraction completed for " + roi_count + " cells");
print("=== Extract Cells Macro Completed ===");

// Signal macro completion to the Python adapter
print("MACRO_DONE");

// Auto-close ImageJ if requested
if (auto_close) {
    run("Quit");
}