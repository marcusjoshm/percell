// Analyze Cell Masks Macro for Single Cell Analysis Workflow
// This macro analyzes cell mask files using Analyze Particles
// Parameters are passed from the Python script

#@ String mask_files_list
#@ String csv_file
#@ Boolean auto_close

// Enable batch mode for better performance
setBatchMode(true);

// Validate input parameters
if (mask_files_list == "") {
    exit("Error: Mask files list not specified");
}
if (csv_file == "") {
    exit("Error: CSV output file not specified");
}

print("=== Analyze Cell Masks Macro Started ===");
print("CSV output file: " + csv_file);
print("Auto close: " + auto_close);

// Parse the mask files list (semicolon-separated)
mask_files = split(mask_files_list, ";");
num_files = mask_files.length;

print("Number of mask files to process: " + num_files);
print("ANALYZE_TOTAL: " + num_files);

// Create an array to store slice names
var sliceNames = newArray(num_files);

// Process each mask file
for (i = 0; i < num_files; i++) {
    mask_path = mask_files[i];
    print("Processing mask " + (i+1) + ": " + mask_path);
    
    // Extract the base file name without extension for slice naming
    file_basename = File.getName(mask_path);
    if (endsWith(file_basename, ".tif")) {
        file_basename = substring(file_basename, 0, lengthOf(file_basename) - 4);
    } else if (endsWith(file_basename, ".tiff")) {
        file_basename = substring(file_basename, 0, lengthOf(file_basename) - 5);
    }
    
    // Get the parent folder name
    parent_folder = File.getParent(mask_path);
    parent_name = File.getName(parent_folder);
    
    // Combined name for slice identification
    slice_name = parent_name + "_" + file_basename;
    sliceNames[i] = slice_name;
    
    print("ANALYSIS_START:" + mask_path);
    
    // Open the mask file
    open(mask_path);
    
    // Run Analyze Particles with the specified parameters
    run("Analyze Particles...", "size=0.10-Infinity summarize");
    
    print("ANALYSIS_END:" + mask_path);
    print("ANALYZE_FILE: " + (i+1) + "/" + num_files);
    
    // Close all open images
    while (nImages > 0) {
        selectImage(nImages);
        close();
    }
}

// Update slice names in the Summary table and save as CSV
if (isOpen("Summary")) {
    for (i = 0; i < sliceNames.length; i++) {
        Table.set("Slice", i, sliceNames[i], "Summary");
    }
    Table.update("Summary");
    
    // Save the Summary table as CSV
    print("Saving summary to: " + csv_file);
    Table.save(csv_file, "Summary");
    close("Summary");
} else {
    print("Warning: No Summary table was created");
}

print("MACRO_COMPLETE");
print("=== Analyze Cell Masks Macro Completed ===");

// Turn off batch mode
setBatchMode(false);

// Auto-close ImageJ if requested
if (auto_close) {
    run("Quit");
} 