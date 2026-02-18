// Resize ROIs Macro for Single Cell Analysis Workflow
// This macro resizes ROIs from binned images to match original image dimensions
// Parameters are passed from the Python script

#@ String input_dir
#@ String output_dir  
#@ String channel
#@ Boolean auto_close

// Enable batch mode for better performance
setBatchMode(true);

// Helper functions
function endsWith(str, suffix) {
    result = substring(str, lengthOf(str) - lengthOf(suffix), lengthOf(str));
    if (result == suffix)
        return 1;
    else
        return 0;
}

function startsWith(str, prefix) {
    result = substring(str, 0, lengthOf(prefix));
    if (result == prefix)
        return 1;
    else
        return 0;
}

// Validate input
if (input_dir == "") {
    exit("Error: Input directory not specified");
}
if (output_dir == "") {
    exit("Error: Output directory not specified");
}
if (channel == "") {
    exit("Error: Channel not specified");
}

// Ensure output directory exists
if (!File.exists(output_dir)) {
    File.makeDirectory(output_dir);
}

// Strip trailing slashes if present
if (endsWith(input_dir, "/")) {
    input_dir = substring(input_dir, 0, lengthOf(input_dir)-1);
}
if (endsWith(output_dir, "/")) {
    output_dir = substring(output_dir, 0, lengthOf(output_dir)-1);
}

print("=== Resize ROIs Macro Started ===");
print("Input directory: " + input_dir);
print("Output directory: " + output_dir);
print("Processing channel: " + channel);
print("Auto close: " + auto_close);

// Helper function to process ROI files in a directory
function processDirectory(dir_path, output_condition_dir) {
    dir_files = getFileList(dir_path);
    local_processed = 0;

    for (i = 0; i < dir_files.length; i++) {
        roi_file = dir_files[i];

        // Process only files ending with _rois.zip and containing the specified channel
        if (!endsWith(roi_file, "_rois.zip") || indexOf(roi_file, channel) == -1) {
            continue;
        }

        // Find corresponding image file
        base_name = substring(roi_file, 0, indexOf(roi_file, "_rois.zip"));
        image_file = base_name + ".tif";
        image_path = dir_path + "/" + image_file;

        if (!File.exists(image_path)) {
            print("Image file not found: " + image_path);
            continue;
        }

        roi_path = dir_path + "/" + roi_file;

        // Create output ROI file name
        // Remove 'bin4x4_' prefix if present
        if (startsWith(base_name, "bin4x4_")) {
            new_base_name = substring(base_name, lengthOf("bin4x4_"), lengthOf(base_name));
        } else {
            new_base_name = base_name;
        }

        new_roi_file = "ROIs_" + new_base_name + "_rois.zip";
        new_roi_path = output_condition_dir + "/" + new_roi_file;

        print("Processing: " + base_name);
        print("  ROI file: " + roi_path);
        print("  Image file: " + image_path);
        print("  Output ROI file: " + new_roi_path);

        // ----- Process the Image and ROIs -----
        print("  Opening image: " + image_path);
        open(image_path);
        image_title = getTitle();

        print("  Image dimensions: " + getWidth() + " x " + getHeight());

        print("  Opening ROI file: " + roi_path);
        // Initialize ROI Manager
        roiManager("reset");

        // Open ROIs
        roiManager("open", roi_path);

        num_original_rois = roiManager("count");
        print("RESIZE_TOTAL: " + num_original_rois);
        print("  Found " + num_original_rois + " ROIs to process");

        for (j = 0; j < num_original_rois; j++) {
            // Select the input image and ROI
            selectWindow(image_title);
            // Duplicate the image and create a mask
            run("Duplicate...", "title=makeMask");
            selectWindow("makeMask");
            roiManager("Select", j);

            // Create a mask from the ROI
            run("Create Mask");

            // Resize the mask to match original image (4x larger since we binned 4x4)
            orig_width = getWidth();
            orig_height = getHeight();
            new_width = orig_width * 4;
            new_height = orig_height * 4;
            run("Size...", "width=" + new_width + " height=" + new_height + " interpolation=None");

            // Create a selection from the resized mask
            run("Create Selection");
            roiManager("Add");

            // Report progress for determinate progress bars
            print("RESIZE_ROI: " + (j+1) + "/" + num_original_rois);

            // Close the duplicate and mask windows
            close(); // Close mask
            close(); // Close duplicate
        }

        // Remove the original ROIs (they're at the beginning of the list)
        for (j = 0; j < num_original_rois; j++) {
            roiManager("Select", 0);
            roiManager("Delete");
        }

        // Save the new ROIs
        print("  Saving " + (roiManager("count")) + " resized ROIs to: " + new_roi_path);
        roiManager("Save", new_roi_path);

        // Close the original binned image
        selectWindow(image_title);
        close();

        // Reset ROI Manager for next round
        roiManager("reset");

        local_processed++;
    }

    return local_processed;
}

// Process all condition directories in input directory
condition_dirs = getFileList(input_dir);
num_processed = 0;

for (c = 0; c < condition_dirs.length; c++) {
    condition_name = condition_dirs[c];

    // Skip non-directories and hidden folders
    if (!File.isDirectory(input_dir + "/" + condition_name) || indexOf(condition_name, ".") == 0) {
        continue;
    }

    condition_path = input_dir + "/" + condition_name;
    print("Processing condition: " + condition_name);

    // Create corresponding output directory
    output_condition_dir = output_dir + "/" + condition_name;
    if (!File.exists(output_condition_dir)) {
        File.makeDirectory(output_condition_dir);
    }

    // Single pass: process ROI files and collect subdirectories
    condition_files = getFileList(condition_path);
    subdirs_to_process = newArray(condition_files.length);
    num_subdirs = 0;

    // Process files directly in condition directory (flat structure)
    num_processed = num_processed + processDirectory(condition_path, output_condition_dir);

    // Collect subdirectories for processing
    for (f = 0; f < condition_files.length; f++) {
        fname = condition_files[f];
        if (File.isDirectory(condition_path + "/" + fname) && indexOf(fname, ".") != 0) {
            subdirs_to_process[num_subdirs] = fname;
            num_subdirs = num_subdirs + 1;
        }
    }

    // Process subdirectories (legacy nested structure)
    for (s = 0; s < num_subdirs; s++) {
        subdir = subdirs_to_process[s];
        subdir_path = condition_path + "/" + subdir;
        num_processed = num_processed + processDirectory(subdir_path, output_condition_dir);
    }
}

print("Completed processing " + num_processed + " ROI files");
print("Resized ROIs saved to " + output_dir);
print("=== Resize ROIs Macro Completed ===");

// Turn off batch mode
setBatchMode(false);

// Signal macro completion to the Python adapter
print("MACRO_DONE");

// Auto-close ImageJ if requested
if (auto_close) {
    run("Quit");
}