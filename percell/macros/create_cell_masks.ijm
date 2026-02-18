// Create Cell Masks Macro for Single Cell Analysis Workflow
// This macro creates individual cell masks by applying ROIs to combined mask images
// Parameters are passed from the Python script

#@ String roi_file
#@ String mask_file
#@ String output_dir
#@ Boolean auto_close

// Enable batch mode for better performance
setBatchMode(true);

// Validate input parameters
if (roi_file == "") {
    exit("Error: ROI file not specified");
}
if (mask_file == "") {
    exit("Error: Mask file not specified");
}
if (output_dir == "") {
    exit("Error: Output directory not specified");
}

print("=== Create Cell Masks Macro Started ===");
print("ROI file: " + roi_file);
print("Mask file: " + mask_file);
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
print("CREATE_TOTAL: " + roi_count);

if (roi_count == 0) {
    print("No ROIs found in file: " + roi_file);
    exit("No ROIs found");
}

// Open the mask image
print("Opening mask file");
open(mask_file);
if (nImages == 0) {
    print("Failed to open mask file: " + mask_file);
    exit("Failed to open mask file");
}

// Get the title of the open image
maskTitle = getTitle();
print("Mask opened: " + maskTitle);

// Process each ROI
for (i = 0; i < roi_count; i++) {
    // Duplicate the mask image so the original remains unaltered
    selectWindow(maskTitle);
    run("Duplicate...", "title=TempMask duplicate");
    
    // Apply the ROI (from the ROI Manager) to the duplicate
    roiManager("select", i);
    nslices = nSlices();
    for (s = 1; s <= nslices; s++) {
        setSlice(s);
        run("Clear Outside");
    }
    
    // Save the cell mask
    cell_num = i + 1;
    cell_path = output_dir + "/MASK_CELL" + cell_num + ".tif";
    print("Saving mask " + cell_num + " to: " + cell_path);
    print("CREATE_MASK: " + (i+1) + "/" + roi_count);
    saveAs("Tiff", cell_path);
    
    // Close the duplicate
    close();
}

// Close the original image
selectWindow(maskTitle);
close();

// Clear ROI Manager
roiManager("reset");

// Turn off batch mode
setBatchMode(false);

print("Cell mask creation completed for " + roi_count + " cells");
print("=== Create Cell Masks Macro Completed ===");

// Signal macro completion to the Python adapter
print("MACRO_DONE");

// Auto-close ImageJ if requested
if (auto_close) {
    run("Quit");
}