#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Auto-Threshold Analysis Module for Single Cell Analysis

This module provides automated thresholding capabilities for microscopy images.
It can be used as a standalone tool or integrated into the analysis pipeline.

Features:
- Multiple thresholding algorithms (Otsu, Triangle, Yen, etc.)
- Batch processing of images
- Channel-specific thresholding
- Quality assessment of thresholding results
- Export of thresholded masks and statistics
"""

import os
import sys
import argparse
import logging
import tempfile
import subprocess
try:
    import numpy as np
    NUMPY_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
import json

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("AutoThresholdAnalysis")

class AutoThresholdAnalyzer:
    """
    Automated thresholding analysis for microscopy images.
    
    Provides multiple thresholding algorithms and quality assessment.
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize the auto-threshold analyzer.
        
        Args:
            config: Configuration dictionary with thresholding parameters
        """
        self.config = config or {}
        self.thresholding_methods = {
            'otsu': 'Otsu',
            'triangle': 'Triangle', 
            'yen': 'Yen',
            'li': 'Li',
            'isodata': 'IsoData',
            'maxentropy': 'MaxEntropy',
            'moments': 'Moments',
            'percentile': 'Percentile',
            'ridler': 'RidlerCalvard'
        }
        
    def validate_inputs(self, input_dir: str, output_dir: str) -> bool:
        """
        Validate input and output directories.
        
        Args:
            input_dir: Input directory containing images
            output_dir: Output directory for results
            
        Returns:
            True if valid, False otherwise
        """
        if not os.path.exists(input_dir):
            logger.error(f"Input directory does not exist: {input_dir}")
            return False
            
        if not os.path.isdir(input_dir):
            logger.error(f"Input path is not a directory: {input_dir}")
            return False
            
        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)
        
        return True
    
    def get_available_images(self, input_dir: str, file_extensions: List[str] = None) -> List[str]:
        """
        Get list of available images in the input directory.
        
        Args:
            input_dir: Input directory path
            file_extensions: List of file extensions to include (default: ['.tif', '.tiff', '.png', '.jpg', '.jpeg'])
            
        Returns:
            List of image file paths
        """
        if file_extensions is None:
            file_extensions = ['.tif', '.tiff', '.png', '.jpg', '.jpeg']
            
        image_files = []
        input_path = Path(input_dir)
        
        for ext in file_extensions:
            image_files.extend(input_path.glob(f"*{ext}"))
            image_files.extend(input_path.glob(f"*{ext.upper()}"))
            
        return [str(f) for f in sorted(image_files)]
    
    def get_available_rois(self, rois_dir: str) -> List[str]:
        """
        Get list of available ROI files in the ROIs directory.
        
        Args:
            rois_dir: ROIs directory path
            
        Returns:
            List of ROI file paths
        """
        roi_files = []
        rois_path = Path(rois_dir)
        
        # Look for .zip files
        roi_files.extend(rois_path.glob("*.zip"))
        roi_files.extend(rois_path.glob("*.ZIP"))
            
        return [str(f) for f in sorted(roi_files)]
    
    def filter_images_by_channel(self, image_files: List[str], channel: str) -> List[str]:
        """
        Filter image files by channel pattern.
        
        Args:
            image_files: List of image file paths
            channel: Channel pattern to match (e.g., 'ch0', 'ch1')
            
        Returns:
            List of filtered image file paths
        """
        import re
        # Extract channel number from the channel argument (e.g., 'ch0' -> '0')
        channel_match = re.match(r'ch(\d+)', channel)
        if not channel_match:
            logger.error(f"Invalid channel format: {channel}. Expected format like 'ch0', 'ch1', etc.")
            return []
        
        channel_number = channel_match.group(1)
        # Look for _ch{channel_number} pattern in filename
        channel_pattern = re.compile(rf'_ch{channel_number}(?:_|\.|$)')
        filtered_files = []
        
        for image_file in image_files:
            filename = Path(image_file).name
            if channel_pattern.search(filename):
                filtered_files.append(image_file)
        
        return filtered_files
    
    def extract_base_name(self, filename: str) -> str:
        """
        Extract base name from filename with pattern: base_name_sX_zY_chZ_tW.tif
        
        Args:
            filename: Image filename
            
        Returns:
            Base name (everything before the first pattern)
        """
        import re
        # Remove file extension
        name_without_ext = Path(filename).stem
        
        # Find the first pattern (_s, _z, _ch, or _t) and extract everything before it
        pattern = re.compile(r'(_s\d+|_z\d+|_ch\d+|_t\d+)')
        match = pattern.search(name_without_ext)
        
        if match:
            return name_without_ext[:match.start()]
        else:
            # If no pattern found, return the whole name
            return name_without_ext
    
    def get_matching_roi_file(self, base_name: str, rois_dir: str) -> str:
        """
        Find ROI file that matches the base name.
        
        Args:
            base_name: Base name to match
            rois_dir: Directory containing ROI files
            
        Returns:
            Path to matching ROI file, or None if not found
        """
        roi_files = self.get_available_rois(rois_dir)
        
        for roi_file in roi_files:
            roi_name = Path(roi_file).stem  # Remove .zip extension
            if roi_name == base_name:
                return roi_file
        
        return None
    
    def create_thresholding_macro(self, input_dir: str, output_dir: str, 
                                method: str = 'otsu', channels: List[str] = None,
                                quality_assessment: bool = True) -> str:
        """
        Create an ImageJ macro for automated thresholding.
        
        Args:
            input_dir: Input directory containing images
            output_dir: Output directory for results
            method: Thresholding method to use
            channels: List of channels to process (None for all)
            quality_assessment: Whether to perform quality assessment
            
        Returns:
            Path to the created macro file
        """
        if method not in self.thresholding_methods:
            raise ValueError(f"Unknown thresholding method: {method}")
            
        # Create temporary macro file
        macro_content = self._generate_macro_content(
            input_dir, output_dir, method, channels, quality_assessment
        )
        
        # Write macro to temporary file
        temp_macro = tempfile.NamedTemporaryFile(mode='w', suffix='.ijm', delete=False)
        temp_macro.write(macro_content)
        temp_macro.close()
        
        return temp_macro.name
    
    def _generate_macro_content(self, input_dir: str, output_dir: str, 
                              method: str, channels: List[str], 
                              quality_assessment: bool) -> str:
        """
        Generate ImageJ macro content for thresholding.
        
        Args:
            input_dir: Input directory path
            output_dir: Output directory path
            method: Thresholding method
            channels: List of channels to process
            quality_assessment: Whether to perform quality assessment
            
        Returns:
            Macro content as string
        """
        # Ensure paths use forward slashes for ImageJ
        input_dir_path = str(input_dir).replace('\\', '/').rstrip('/')
        output_dir_path = str(output_dir).replace('\\', '/').rstrip('/')
        
        # Create channel filtering logic
        channel_filter_logic = ""
        if channels:
            channel_conditions = []
            for channel in channels:
                channel_conditions.append(f'indexOf(getTitle(), "{channel}") >= 0')
            channel_filter_logic = f"""
        // Check if this image matches any of the specified channels
        channelMatch = false;
        if ({' || '.join(channel_conditions)}) {{
            channelMatch = true;
        }}
        if (!channelMatch) {{
            continue; // Skip this image if it doesn't match specified channels
        }}
        """
        
        macro_content = f"""
// Auto-Threshold Analysis Macro
// Generated by PerCell Auto-Threshold Module

// Parameters
input_dir = "{input_dir_path}";
output_dir = "{output_dir_path}";
threshold_method = "{self.thresholding_methods[method]}";
quality_assessment = {str(quality_assessment).lower()};

// Create output directories (use File.makeDirectory to avoid errors if directories exist)
File.makeDirectory(output_dir + "/thresholded_masks");
File.makeDirectory(output_dir + "/statistics");
if (quality_assessment) {{
    File.makeDirectory(output_dir + "/quality_assessment");
}}

// Initialize statistics
stats_file = output_dir + "/statistics/thresholding_stats.csv";
File.append("Image,Channel,Method,Threshold,Mean_Intensity,Std_Dev,Min_Intensity,Max_Intensity,Area_Pixels,Area_um2\\n", stats_file);

// Process images
input_list = getFileList(input_dir);
for (i = 0; i < input_list.length; i++) {{
    image_path = input_dir + "/" + input_list[i];
    
    // Open image
    open(image_path);
    image_name = getTitle();
    
    {channel_filter_logic}
    
    // Get image properties
    getDimensions(width, height, channels, slices, frames);
    
    // Process each channel if multi-channel
    if (channels > 1) {{
        for (c = 1; c <= channels; c++) {{
            Stack.setChannel(c);
            channel_name = "ch" + (c-1);
            
            // Apply thresholding
            setAutoThreshold(threshold_method);
            getThreshold(lower, upper);
            
            // Create mask
            run("Create Mask");
            mask_name = image_name + "_" + channel_name + "_mask";
            rename(mask_name);
            
            // Save mask
            saveAs("Tiff", output_dir + "/thresholded_masks/" + mask_name + ".tif");
            
            // Calculate statistics
            run("Measure");
            mean_intensity = getResult("Mean");
            std_dev = getResult("StdDev");
            min_intensity = getResult("Min");
            max_intensity = getResult("Max");
            area_pixels = getResult("Area");
            
            // Convert area to um2 (assuming 1 pixel = 0.1 um, adjust as needed)
            area_um2 = area_pixels * 0.01;
            
            // Save statistics
            stats_line = image_name + "," + channel_name + "," + threshold_method + "," + 
                        lower + "," + mean_intensity + "," + std_dev + "," + 
                        min_intensity + "," + max_intensity + "," + area_pixels + "," + area_um2 + "\\n";
            File.append(stats_line, stats_file);
            
            // Quality assessment
            if (quality_assessment) {{
                // Calculate quality metrics
                run("Analyze Particles...", "size=10-Infinity circularity=0.00-1.00 show=Outlines display clear");
                particle_count = nResults;
                
                // Save quality metrics
                quality_file = output_dir + "/quality_assessment/" + image_name + "_" + channel_name + "_quality.txt";
                File.open(quality_file);
                File.write("Image: " + image_name + "\\n");
                File.write("Channel: " + channel_name + "\\n");
                File.write("Threshold Method: " + threshold_method + "\\n");
                File.write("Threshold Value: " + lower + "\\n");
                File.write("Particle Count: " + particle_count + "\\n");
                File.write("Mean Intensity: " + mean_intensity + "\\n");
                File.write("Standard Deviation: " + std_dev + "\\n");
                File.write("Area (pixels): " + area_pixels + "\\n");
                File.write("Area (um2): " + area_um2 + "\\n");
                File.close();
            }}
            
            // Close mask
            close();
        }}
    }} else {{
        // Single channel image
        // Apply thresholding
        setAutoThreshold(threshold_method);
        getThreshold(lower, upper);
        
        // Create mask
        run("Create Mask");
        mask_name = image_name + "_mask";
        rename(mask_name);
        
        // Save mask
        saveAs("Tiff", output_dir + "/thresholded_masks/" + mask_name + ".tif");
        
        // Calculate statistics
        run("Measure");
        mean_intensity = getResult("Mean");
        std_dev = getResult("StdDev");
        min_intensity = getResult("Min");
        max_intensity = getResult("Max");
        area_pixels = getResult("Area");
        area_um2 = area_pixels * 0.01;
        
        // Save statistics
        stats_line = image_name + ",single," + threshold_method + "," + 
                    lower + "," + mean_intensity + "," + std_dev + "," + 
                    min_intensity + "," + max_intensity + "," + area_pixels + "," + area_um2 + "\\n";
        File.append(stats_line, stats_file);
        
        // Quality assessment
        if (quality_assessment) {{
            run("Analyze Particles...", "size=10-Infinity circularity=0.00-1.00 show=Outlines display clear");
            particle_count = nResults;
            
            quality_file = output_dir + "/quality_assessment/" + image_name + "_quality.txt";
            File.open(quality_file);
            File.write("Image: " + image_name + "\\n");
            File.write("Channel: single\\n");
            File.write("Threshold Method: " + threshold_method + "\\n");
            File.write("Threshold Value: " + lower + "\\n");
            File.write("Particle Count: " + particle_count + "\\n");
            File.write("Mean Intensity: " + mean_intensity + "\\n");
            File.write("Standard Deviation: " + std_dev + "\\n");
            File.write("Area (pixels): " + area_pixels + "\\n");
            File.write("Area (um2): " + area_um2 + "\\n");
            File.close();
        }}
        
        // Close mask
        close();
    }}
    
    // Close original image
    close();
}}

print("Auto-thresholding analysis completed successfully!");
"""
        
        return macro_content
    
    def create_roi_thresholding_macro(self, input_dir: str, rois_dir: str, output_dir: str, 
                                    channel: str, quality_assessment: bool) -> str:
        """
        Create an ImageJ macro for ROI-based automated thresholding.
        
        Args:
            input_dir: Input directory containing images
            rois_dir: Directory containing ROI files
            output_dir: Output directory for results
            channel: Channel pattern to match
            quality_assessment: Whether to perform quality assessment
            
        Returns:
            Path to the created macro file
        """
        # Create temporary macro file
        macro_content = self._generate_roi_macro_content(
            input_dir, rois_dir, output_dir, channel, quality_assessment
        )
        
        # Write macro to temporary file
        temp_macro = tempfile.NamedTemporaryFile(mode='w', suffix='.ijm', delete=False)
        temp_macro.write(macro_content)
        temp_macro.close()
        
        return temp_macro.name
    
    def _generate_roi_macro_content(self, input_dir: str, rois_dir: str, output_dir: str, 
                                  channel: str, quality_assessment: bool) -> str:
        """
        Generate ImageJ macro content for ROI-based thresholding.
        
        Args:
            input_dir: Input directory path
            rois_dir: ROIs directory path
            output_dir: Output directory path
            channel: Channel pattern to match
            quality_assessment: Whether to perform quality assessment
            
        Returns:
            Macro content as string
        """
        # Ensure paths use forward slashes for ImageJ
        input_dir_path = str(input_dir).replace('\\', '/').rstrip('/')
        rois_dir_path = str(rois_dir).replace('\\', '/').rstrip('/')
        output_dir_path = str(output_dir).replace('\\', '/').rstrip('/')
        
        # Extract channel number from channel argument
        import re
        channel_match = re.match(r'ch(\d+)', channel)
        channel_number = channel_match.group(1) if channel_match else "0"
        
        macro_content = f"""
// ROI-Based Auto-Threshold Analysis Macro
// Generated by PerCell Auto-Threshold Module

// Parameters
input_dir = "{input_dir_path}";
rois_dir = "{rois_dir_path}";
output_dir = "{output_dir_path}";
channel_number = "{channel_number}";
quality_assessment = {str(quality_assessment).lower()};

print("Starting ROI-based auto-thresholding analysis...");
print("Input directory: " + input_dir);
print("ROIs directory: " + rois_dir);
print("Output directory: " + output_dir);
print("Channel number: " + channel_number);

// Create output directories (use File.makeDirectory to avoid errors if directories exist)
File.makeDirectory(output_dir + "/thresholded_masks");
File.makeDirectory(output_dir + "/statistics");
if (quality_assessment) {{
    File.makeDirectory(output_dir + "/quality_assessment");
}}

// Initialize statistics
stats_file = output_dir + "/statistics/roi_thresholding_stats.csv";

// Function to extract base name from filename
function extractBaseName(filename) {{
    // Remove file extension
    if (endsWith(filename, ".tif")) {{
        filename = substring(filename, 0, lengthOf(filename) - 4);
    }} else if (endsWith(filename, ".tiff")) {{
        filename = substring(filename, 0, lengthOf(filename) - 5);
    }}
    
    // For files like "Series001_z00_ch00.tif", extract "Series001"
    // Find the first underscore and extract everything before it
    underscore_pos = indexOf(filename, "_");
    if (underscore_pos >= 0) {{
        return substring(filename, 0, underscore_pos);
    }} else {{
        return filename;
    }}
}}

// Get list of image files with matching channel
image_list = getFileList(input_dir);
channel_pattern = "_ch" + channel_number;
matching_images = newArray(0);

print("Total files in input directory: " + image_list.length);
print("Looking for channel pattern: " + channel_pattern);

for (img_idx = 0; img_idx < image_list.length; img_idx++) {{
    image_file = image_list[img_idx];
    print("Checking file: " + image_file);
    if ((endsWith(image_file, ".tif") || endsWith(image_file, ".tiff")) && indexOf(image_file, channel_pattern) >= 0) {{
        print("  -> MATCH: " + image_file);
        // Add to matching images array
        matching_images = Array.concat(matching_images, image_file);
    }}
}}

print("Found " + matching_images.length + " matching images");

// Process each matching image
for (img_idx = 0; img_idx < matching_images.length; img_idx++) {{
    image_file = matching_images[img_idx];
    image_path = input_dir + "/" + image_file;
    
    // Extract base name from image file
    base_name = extractBaseName(image_file);
    
    // Look for matching ROI file
    roi_list = getFileList(rois_dir);
    roi_found = false;
    
    print("Looking for ROI matching base_name: " + base_name);
    print("Available ROI files:");
    for (roi_idx = 0; roi_idx < roi_list.length; roi_idx++) {{
        roi_file = roi_list[roi_idx];
        print("  " + roi_file);
    }}
    
            for (roi_idx = 0; roi_idx < roi_list.length; roi_idx++) {{
            roi_file = roi_list[roi_idx];
            if (endsWith(roi_file, ".zip")) {{
                roi_name = substring(roi_file, 0, lengthOf(roi_file) - 4); // Remove .zip extension
                print("Checking ROI: " + roi_name + " against base_name: " + base_name);
                
                // Check if the base_name is contained within the ROI filename
                if (indexOf(roi_name, base_name) >= 0) {{
                    roi_path = rois_dir + "/" + roi_file;
                    roi_found = true;
                    print("  -> MATCH found: " + roi_path + " (contains " + base_name + ")");
                    break;
                }}
            }}
        }}
    
    if (!roi_found) {{
        print("No matching ROI found for image: " + image_file + " (base_name: " + base_name + ")");
        continue;
    }}
    
    // Step 1: Open the .tif file from input directory
    open(image_path);
    image_name = getTitle();
    
    // Step 2: Select the image explicitly
    selectImage(image_name);
    
    // Step 3: Perform autothreshold on the full image using Otsu method to create binary mask
    run("Auto Threshold", "method=Otsu white");
    
    // Save the binary mask
    mask_name =  "binary_mask_" + image_name;
    saveAs("Tiff", output_dir + "/thresholded_masks/" + mask_name + ".tif");
    
    // Step 4: Load the corresponding ROI list
    roiManager("Open", roi_path);
    
    // Step 5: Clear any previous results before measuring
    run("Clear Results");
    
    // Step 6: Set measurements to include area, mean, standard deviation, integrated density, raw integrated density
    run("Set Measurements...", "area mean standard integrated raw_integrated display redirect=None decimal=3");
    
    // Step 7: Measure each ROI individually to guarantee all rows are captured
    roi_total = roiManager("count");
    
    // Step 8: Build CSV in memory and save
    image_csv_file = output_dir + "/statistics/" + image_name + "_measurements.csv";
    csv = "Label,Area,Mean,StdDev,IntDen,RawIntDen\\n";
    for (ri = 0; ri < roi_total; ri++) {{
        run("Clear Results");
        roiManager("Select", ri);
        roiManager("Measure");
        // Read the single-row results
        label = getResultString("Label", 0);
        // Prepend unique string for sorting: per-ROI iteration index
        label = "cell_" + (ri+1) + "_" + label;
        area = getResult("Area", 0);
        mean = getResult("Mean", 0);
        sd = getResult("StdDev", 0);
        intden = getResult("IntDen", 0);
        raw = getResult("RawIntDen", 0);
        csv = csv + label + "," + area + "," + mean + "," + sd + "," + intden + "," + raw + "\\n";
    }}
    File.saveString(csv, image_csv_file);
    print("  -> Saved " + roi_total + " ROI measurements to " + image_csv_file);    
    
    // Step 10: Clear results for next image
    run("Clear Results");
    
    // Quality assessment (if enabled)
    if (quality_assessment) {{
        // Save quality metrics
        quality_file = output_dir + "/quality_assessment/" + image_name + "_" + roi_name + "_quality.txt";
        File.open(quality_file);
        File.write("Image: " + image_name + "\\n");
        File.write("ROI File: " + roi_name + "\\n");
        File.write("Channel: ch" + channel_number + "\\n");
        File.write("Threshold Method: Otsu\\n");
        File.write("Number of ROIs: " + roi_count + "\\n");
        File.write("Binary Mask Created: " + mask_name + "\\n");
        File.close();
    }}
    
    // Step 11: Close the files and clear the ROI manager
    // Check if images are open before closing
    if (nImages > 0) {{
        close(); // Close the binary mask
    }}
    if (nImages > 0) {{
        close(); // Close the original image
    }}
    roiManager("Reset"); // Clear the ROI manager
    
    print("Processed: " + image_name + " with " + roi_total + " ROIs");
}}



print("ROI-based auto-thresholding analysis completed successfully!");
"""
        
        return macro_content
    
    def run_thresholding_analysis(self, input_dir: str, output_dir: str, 
                                method: str = 'otsu', channels: List[str] = None,
                                quality_assessment: bool = True, 
                                imagej_path: str = None) -> bool:
        """
        Run the automated thresholding analysis.
        
        Args:
            input_dir: Input directory containing images
            output_dir: Output directory for results
            method: Thresholding method to use
            channels: List of channels to process (None for all)
            quality_assessment: Whether to perform quality assessment
            imagej_path: Path to ImageJ executable (optional)
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Validate inputs
            if not self.validate_inputs(input_dir, output_dir):
                return False
            
            # Get available images
            image_files = self.get_available_images(input_dir)
            if not image_files:
                logger.error(f"No image files found in {input_dir}")
                return False
                
            logger.info(f"Found {len(image_files)} images to process")
            
            # Create macro
            macro_path = self.create_thresholding_macro(
                input_dir, output_dir, method, channels, quality_assessment
            )
            
            # Run ImageJ macro
            if not self._run_imagej_macro(macro_path, imagej_path):
                return False
            
            # Clean up temporary macro file
            try:
                os.unlink(macro_path)
            except:
                pass
            
            logger.info("Auto-thresholding analysis completed successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error in auto-thresholding analysis: {e}")
            return False
    
    def run_thresholding_analysis_with_rois(self, input_dir: str, rois_dir: str, 
                                          channel: str, output_dir: str,
                                          quality_assessment: bool = True, 
                                          imagej_path: str = None) -> bool:
        """
        Run the automated thresholding analysis with ROI processing.
        
        Args:
            input_dir: Input directory containing .tif images
            rois_dir: Directory containing .zip ROI files
            channel: Channel pattern to match (e.g., 'ch0', 'ch1')
            output_dir: Output directory for results
            method: Thresholding method to use
            quality_assessment: Whether to perform quality assessment
            imagej_path: Path to ImageJ executable (optional)
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Validate inputs
            if not self.validate_inputs(input_dir, output_dir):
                return False
            
            if not os.path.exists(rois_dir):
                logger.error(f"ROIs directory does not exist: {rois_dir}")
                return False
            
            # Get available images and filter by channel
            image_files = self.get_available_images(input_dir, ['.tif', '.tiff'])
            if not image_files:
                logger.error(f"No .tif image files found in {input_dir}")
                return False
            
            filtered_images = self.filter_images_by_channel(image_files, channel)
            if not filtered_images:
                logger.error(f"No images found matching channel pattern: {channel}")
                return False
                
            logger.info(f"Found {len(filtered_images)} images matching channel {channel}")
            
            # Get available ROI files
            roi_files = self.get_available_rois(rois_dir)
            if not roi_files:
                logger.error(f"No .zip ROI files found in {rois_dir}")
                return False
                
            logger.info(f"Found {len(roi_files)} ROI files")
            
            # Create macro for ROI-based thresholding
            macro_path = self.create_roi_thresholding_macro(
                input_dir, rois_dir, output_dir, channel, quality_assessment
            )
            
            # Run ImageJ macro
            if not self._run_imagej_macro(macro_path, imagej_path):
                return False
            
            # Clean up temporary macro file
            try:
                os.unlink(macro_path)
            except:
                pass
            
            # Extract channel number from channel parameter
            import re
            channel_match = re.match(r'ch(\d+)', channel)
            channel_number = channel_match.group(1) if channel_match else "0"
            
            # Combine all individual CSV files into one final CSV file
            self._combine_csv_files(output_dir, channel_number)
            
            logger.info("ROI-based auto-thresholding analysis completed successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error in ROI-based auto-thresholding analysis: {e}")
            return False
    
    def _combine_csv_files(self, output_dir: str, channel_number: str) -> None:
        """
        Combine all individual CSV files into one final CSV file.
        
        Args:
            output_dir: Output directory containing individual CSV files
        """
        import glob
        import pandas as pd
        
        try:
            # Find all individual CSV files
            csv_pattern = os.path.join(output_dir, "statistics", "*_measurements.csv")
            csv_files = glob.glob(csv_pattern)
            
            if not csv_files:
                logger.warning("No individual CSV files found to combine")
                return
            
            # Read and combine all CSV files
            all_data = []
            for csv_file in sorted(csv_files):
                try:
                    df = pd.read_csv(csv_file)
                    
                    # Extract image name from filename
                    filename = os.path.basename(csv_file)
                    image_name = filename.replace("_measurements.csv", "")
                    
                    # Add Image and Channel columns
                    df['Image'] = image_name
                    df['Channel'] = f"ch{channel_number}"
                    
                    # Reorder columns to match expected format
                    if 'Label' in df.columns:
                        df = df[['Image', 'Label', 'Channel', 'Area', 'Mean', 'StdDev', 'IntDen', 'RawIntDen']]
                    
                    all_data.append(df)
                    logger.info(f"Added data from {filename}")
                except Exception as e:
                    logger.error(f"Error reading {csv_file}: {e}")
            
            if all_data:
                # Combine all dataframes
                combined_df = pd.concat(all_data, ignore_index=True)
                
                # Save to final CSV file
                final_csv_path = os.path.join(output_dir, "statistics", "roi_thresholding_stats.csv")
                combined_df.to_csv(final_csv_path, index=False)
                logger.info(f"Combined {len(csv_files)} files into {final_csv_path}")
                
                # Clean up individual files
                for csv_file in csv_files:
                    try:
                        os.remove(csv_file)
                    except:
                        pass
                        
        except Exception as e:
            logger.error(f"Error combining CSV files: {e}")

    def _run_imagej_macro(self, macro_path: str, imagej_path: str = None) -> bool:
        """
        Run ImageJ macro.
        
        Args:
            macro_path: Path to the macro file
            imagej_path: Path to ImageJ executable (currently ignored, hardcoded to Fiji)
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # TODO: Change this behavior later to use configurable ImageJ path
            # For now, hardcode to Fiji path
            imagej_path = "/Applications/Fiji.app/Contents/MacOS/ImageJ-macosx"
            
            if not os.path.exists(imagej_path):
                logger.error(f"Fiji not found at hardcoded path: {imagej_path}")
                logger.error("Please install Fiji or modify the hardcoded path in the script.")
                return False
            
            # Run ImageJ with macro (without headless mode for debugging)
            cmd = [imagej_path, "-batch", macro_path]
            logger.info(f"Running ImageJ command: {' '.join(cmd)}")
            
            # Run without capturing output so we can see ImageJ output in real-time
            result = subprocess.run(cmd, text=True)
            
            if result.returncode != 0:
                logger.error(f"ImageJ execution failed: {result.stderr}")
                return False
            
            logger.info("ImageJ macro executed successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error running ImageJ macro: {e}")
            return False
    
    def generate_report(self, output_dir: str) -> str:
        """
        Generate a summary report of the thresholding analysis.
        
        Args:
            output_dir: Output directory containing results
            
        Returns:
            Path to the generated report
        """
        try:
            stats_file = os.path.join(output_dir, "statistics", "thresholding_stats.csv")
            if not os.path.exists(stats_file):
                logger.error(f"Statistics file not found: {stats_file}")
                return None
            
            # Read statistics
            import pandas as pd
            df = pd.read_csv(stats_file)
            
            # Generate report
            report_path = os.path.join(output_dir, "auto_threshold_report.html")
            
            report_content = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Auto-Threshold Analysis Report</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        .header {{ background-color: #f0f0f0; padding: 10px; border-radius: 5px; }}
        .summary {{ margin: 20px 0; }}
        .stats {{ margin: 20px 0; }}
        table {{ border-collapse: collapse; width: 100%; }}
        th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
        th {{ background-color: #f2f2f2; }}
        .method-summary {{ margin: 20px 0; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>Auto-Threshold Analysis Report</h1>
        <p>Generated on: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
    </div>
    
    <div class="summary">
        <h2>Summary</h2>
        <p><strong>Total Images Processed:</strong> {len(df)}</p>
        <p><strong>Unique Channels:</strong> {df['Channel'].nunique()}</p>
        <p><strong>Threshold Methods Used:</strong> {', '.join(df['Method'].unique())}</p>
    </div>
    
    <div class="method-summary">
        <h2>Method Summary</h2>
        {df.groupby('Method').agg({
            'Threshold': ['mean', 'std'],
            'Area_um2': ['mean', 'std', 'sum'],
            'Mean_Intensity': ['mean', 'std']
        }).round(2).to_html()}
    </div>
    
    <div class="stats">
        <h2>Detailed Statistics</h2>
        {df.to_html(index=False)}
    </div>
</body>
</html>
"""
            
            with open(report_path, 'w') as f:
                f.write(report_content)
            
            logger.info(f"Report generated: {report_path}")
            return report_path
            
        except Exception as e:
            logger.error(f"Error generating report: {e}")
            return None


def main():
    """Main function for command-line execution."""
    parser = argparse.ArgumentParser(
        description="Auto-Threshold Analysis for Microscopy Images with ROI Processing",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run auto-thresholding with Otsu method
  python auto_threshold_analysis.py --input /path/to/images --ROIs /path/to/rois --channel ch0 --method otsu
  
  # Run with Triangle method
  python auto_threshold_analysis.py --input /path/to/images --ROIs /path/to/rois --channel ch1 --method triangle
  
  # Run with quality assessment
  python auto_threshold_analysis.py --input /path/to/images --ROIs /path/to/rois --channel ch0 --method yen --quality-assessment
        """
    )
    
    parser.add_argument(
        '--input', '-i',
        required=True,
        help='Input directory containing .tif microscopy images'
    )
    parser.add_argument(
        '--ROIs', '-r',
        required=True,
        help='Directory containing .zip ROI files'
    )
    parser.add_argument(
        '--channel', '-c',
        required=True,
        help='Channel pattern to match (e.g., ch0, ch1) - matches ch(d+) pattern in filenames'
    )
    parser.add_argument(
        '--output-dir', '-o',
        required=True,
        help='Output directory for results'
    )
    parser.add_argument(
        '--method', '-m',
        default='otsu',
        choices=['otsu', 'triangle', 'yen', 'li', 'isodata', 'maxentropy', 'moments', 'percentile', 'ridler'],
        help='Thresholding method to use (default: otsu)'
    )
    parser.add_argument(
        '--quality-assessment',
        action='store_true',
        help='Perform quality assessment of thresholding results'
    )
    parser.add_argument(
        '--imagej-path',
        help='Path to ImageJ executable'
    )
    parser.add_argument(
        '--generate-report',
        action='store_true',
        help='Generate HTML report after analysis'
    )
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Enable verbose logging'
    )
    
    args = parser.parse_args()
    
    # Set up logging
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Validate channel pattern
    import re
    channel_pattern = re.compile(r'ch(\d+)')
    if not channel_pattern.match(args.channel):
        logger.error(f"Invalid channel format: {args.channel}. Expected format like 'ch0', 'ch1', etc.")
        sys.exit(1)
    
    # Create analyzer
    analyzer = AutoThresholdAnalyzer()
    
    # Run analysis
    success = analyzer.run_thresholding_analysis_with_rois(
        input_dir=args.input,
        rois_dir=args.ROIs,
        channel=args.channel,
        output_dir=args.output_dir,
        quality_assessment=args.quality_assessment,
        imagej_path=args.imagej_path
    )
    
    if success and args.generate_report:
        analyzer.generate_report(args.output_dir)
    
    if success:
        logger.info("Auto-thresholding analysis completed successfully")
        sys.exit(0)
    else:
        logger.error("Auto-thresholding analysis failed")
        sys.exit(1)


if __name__ == "__main__":
    main()
