// Filter Edge ROIs Macro for Single Cell Analysis Workflow
// This macro removes ROIs that are near the edges of the image
// to ensure only complete cells are included in downstream analysis
// Parameters are passed from the Python script

#@ String input_dir
#@ String output_dir
#@ String channel
#@ Integer edge_margin
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

print("=== Filter Edge ROIs Macro Started ===");
print("Input directory: " + input_dir);
print("Output directory: " + output_dir);
print("Processing channel: " + channel);
print("Edge margin: " + edge_margin + " pixels");
print("Auto close: " + auto_close);

// Helper function to process ROI files in a directory
// This function processes all ROI files in the given directory
function processDirectory(dir_path, output_path) {
    // Get all files in the directory
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
        output_roi_path = output_path + "/" + roi_file;

        print("Processing: " + base_name);
        print("  ROI file: " + roi_path);
        print("  Image file: " + image_path);
        print("  Output ROI file: " + output_roi_path);

        // ----- Process the Image and ROIs -----
        print("  Opening image: " + image_path);
        open(image_path);
        image_title = getTitle();

        // Get image dimensions for edge detection
        image_width = getWidth();
        image_height = getHeight();
        print("  Image dimensions: " + image_width + " x " + image_height);

        print("  Opening ROI file: " + roi_path);
        // Initialize ROI Manager
        roiManager("reset");

        // Open ROIs
        roiManager("open", roi_path);

        num_original_rois = roiManager("count");
        print("FILTER_TOTAL: " + num_original_rois);
        print("  Found " + num_original_rois + " ROIs to process");

        // Track which ROIs to keep (non-edge ROIs)
        rois_to_keep = newArray(num_original_rois);
        num_kept = 0;
        num_removed = 0;

        // First pass: identify edge ROIs
        for (j = 0; j < num_original_rois; j++) {
            roiManager("Select", j);

            // Get ROI bounding box
            Roi.getBounds(rx, ry, rw, rh);

            // Check if ROI is within edge_margin pixels of any edge
            near_left = (rx <= edge_margin);
            near_top = (ry <= edge_margin);
            near_right = (rx + rw >= image_width - edge_margin);
            near_bottom = (ry + rh >= image_height - edge_margin);

            touches_edge = near_left || near_top || near_right || near_bottom;

            if (touches_edge) {
                print("  ROI " + j + " touches edge (bounds: x=" + rx + ", y=" + ry + ", w=" + rw + ", h=" + rh + ") - REMOVING");
                num_removed++;
            } else {
                rois_to_keep[num_kept] = j;
                num_kept++;
            }

            // Report progress
            print("FILTER_ROI: " + (j+1) + "/" + num_original_rois);
        }

        print("  Kept " + num_kept + " ROIs, removed " + num_removed + " edge ROIs");
        total_rois_kept = total_rois_kept + num_kept;
        total_rois_removed = total_rois_removed + num_removed;

        // Only save if there are ROIs to keep
        if (num_kept > 0) {
            // Create new ROI set with only non-edge ROIs
            roiManager("Deselect");

            // Mark ROIs to delete
            rois_to_delete = newArray(num_removed);
            delete_idx = 0;
            for (j = 0; j < num_original_rois; j++) {
                is_kept = false;
                for (k = 0; k < num_kept; k++) {
                    if (rois_to_keep[k] == j) {
                        is_kept = true;
                        break;
                    }
                }
                if (!is_kept) {
                    rois_to_delete[delete_idx] = j;
                    delete_idx++;
                }
            }

            // Delete ROIs from end to beginning to preserve indices
            for (j = num_removed - 1; j >= 0; j--) {
                roiManager("Select", rois_to_delete[j]);
                roiManager("Delete");
            }

            // Save the filtered ROIs
            print("  Saving " + roiManager("count") + " filtered ROIs to: " + output_roi_path);
            roiManager("Save", output_roi_path);

            // Copy the image file to output directory (needed for resize step)
            output_image_path = output_path + "/" + image_file;
            print("  Copying image to: " + output_image_path);
            File.copy(image_path, output_image_path);
        } else {
            print("  WARNING: No ROIs remaining after edge filtering for " + base_name);
        }

        // Close the image
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
total_rois_removed = 0;
total_rois_kept = 0;

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
    // and collect subdirectories in a single pass
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

        // Create corresponding output subdirectory
        output_subdir = output_condition_dir + "/" + subdir;
        if (!File.exists(output_subdir)) {
            File.makeDirectory(output_subdir);
        }

        num_processed = num_processed + processDirectory(subdir_path, output_subdir);
    }
}

print("=== Filter Edge ROIs Summary ===");
print("Processed " + num_processed + " ROI files");
print("Total ROIs kept: " + total_rois_kept);
print("Total edge ROIs removed: " + total_rois_removed);
print("Filtered ROIs saved to " + output_dir);
print("=== Filter Edge ROIs Macro Completed ===");

// Turn off batch mode
setBatchMode(false);

// Auto-close ImageJ if requested
if (auto_close) {
    eval("script", "System.exit(0);");
}
