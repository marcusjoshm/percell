"""
Create Cell Masks Application Service.

This service implements the use case for creating individual cell masks
by applying ROIs to combined mask images using ImageJ.
"""

import os
import tempfile
import shutil
from pathlib import Path
from typing import Optional, Dict, List

from percell.domain.ports import (
    SubprocessPort, 
    FileSystemPort, 
    LoggingPort,
    ImageProcessingService
)
from percell.domain.exceptions import (
    FileSystemError, 
    SubprocessError, 
    ImageProcessingError
)


class CreateCellMasksService:
    """
    Application service for creating cell masks from ROIs and combined masks.
    
    This service coordinates the domain operations needed to:
    1. Find matching mask files for ROI files
    2. Create ImageJ macros for mask generation
    3. Execute ImageJ to create individual cell masks
    """
    
    def __init__(
        self,
        subprocess_port: SubprocessPort,
        filesystem_port: FileSystemPort,
        logging_port: LoggingPort,
        image_processing_service: ImageProcessingService
    ):
        self.subprocess_port = subprocess_port
        self.filesystem_port = filesystem_port
        self.logging_port = logging_port
        self.logger = logging_port.get_logger("CreateCellMasksService")
    
    def create_cell_masks(
        self,
        roi_directory: str,
        mask_directory: str,
        output_directory: str,
        imagej_path: str,
        auto_close: bool = True
    ) -> bool:
        """
        Create individual cell masks from ROIs and combined masks.
        
        Args:
            roi_directory: Directory containing ROI files
            mask_directory: Directory containing combined masks
            output_directory: Directory to save cell masks
            imagej_path: Path to ImageJ executable
            auto_close: Whether to close ImageJ after execution
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            self.logger.info(f"Starting cell mask creation process")
            self.logger.info(f"ROI directory: {roi_directory}")
            self.logger.info(f"Mask directory: {mask_directory}")
            self.logger.info(f"Output directory: {output_directory}")
            
            # Ensure output directory exists
            output_path = Path(output_directory)
            self.filesystem_port.create_directory(output_path)
            
            # Get ROI files
            roi_files = self._get_roi_files(roi_directory)
            if not roi_files:
                self.logger.warning("No ROI files found")
                return False
            
            # Process each ROI file
            success_count = 0
            for roi_file in roi_files:
                if self._process_single_roi(roi_file, mask_directory, output_directory, imagej_path, auto_close):
                    success_count += 1
            
            self.logger.info(f"Successfully processed {success_count}/{len(roi_files)} ROI files")
            return success_count > 0
            
        except Exception as e:
            self.logger.error(f"Error in create_cell_masks: {str(e)}")
            return False
    
    def _get_roi_files(self, roi_directory: str) -> List[Path]:
        """Get all ROI files from the directory."""
        roi_path = Path(roi_directory)
        if not self.filesystem_port.directory_exists(roi_path):
            self.logger.error(f"ROI directory does not exist: {roi_directory}")
            return []
        
        roi_files = list(roi_path.glob("**/*.zip"))
        self.logger.info(f"Found {len(roi_files)} ROI files")
        return roi_files
    
    def _process_single_roi(
        self,
        roi_file: Path,
        mask_directory: str,
        output_directory: str,
        imagej_path: str,
        auto_close: bool
    ) -> bool:
        """Process a single ROI file to create cell masks."""
        try:
            # Find matching mask file
            mask_file = self._find_matching_mask(roi_file, mask_directory)
            if not mask_file:
                self.logger.warning(f"No matching mask found for {roi_file.name}")
                return False
            
            # Create macro file
            macro_file = self._create_mask_macro(roi_file, mask_file, output_directory)
            if not macro_file:
                return False
            
            # Run ImageJ
            return self._run_imagej_macro(macro_file, imagej_path, auto_close)
            
        except Exception as e:
            self.logger.error(f"Error processing ROI {roi_file.name}: {str(e)}")
            return False
    
    def _find_matching_mask(self, roi_file: Path, mask_directory: str) -> Optional[Path]:
        """Find the corresponding mask file for a ROI file."""
        # Extract metadata from ROI filename
        roi_filename = roi_file.name
        
        # Get the condition from the parent directory
        condition = roi_file.parent.name
        condition_mask_dir = Path(mask_directory) / condition
        
        if not self.filesystem_port.directory_exists(condition_mask_dir):
            self.logger.warning(f"Condition directory not found: {condition_mask_dir}")
            return None
        
        # Parse ROI filename to extract components
        # Example: ROIs_A549 Control_Merged_Processed001_ch00_t00_rois.zip
        cleaned_name = roi_filename
        if cleaned_name.startswith("ROIs_"):
            cleaned_name = cleaned_name[5:]
        
        if cleaned_name.endswith("_rois.zip"):
            cleaned_name = cleaned_name[:-9]
        elif cleaned_name.endswith(".zip"):
            cleaned_name = cleaned_name[:-4]
        
        # Extract channel and timepoint
        import re
        channel_match = re.search(r'_(ch\d+)_', cleaned_name)
        timepoint_match = re.search(r'_(t\d+)(?:_|$)', cleaned_name)
        
        channel = channel_match.group(1) if channel_match else ""
        timepoint = timepoint_match.group(1) if timepoint_match else ""
        
        # The region is the remaining part
        region = cleaned_name
        if channel:
            region = region.replace(f"_{channel}", "")
        if timepoint:
            region = region.replace(f"_{timepoint}", "")
        region = region.rstrip("_")
        
        # Look for mask file
        mask_pattern = f"MASK_{region}_{channel}_{timepoint}.tif"
        mask_files = list(condition_mask_dir.glob(mask_pattern))
        
        if mask_files:
            return mask_files[0]
        
        return None
    
    def _create_mask_macro(
        self, 
        roi_file: Path, 
        mask_file: Path, 
        output_directory: str
    ) -> Optional[Path]:
        """Create ImageJ macro for creating cell masks."""
        try:
            # Create temporary directory for macro
            temp_dir = Path("macros")
            self.filesystem_port.create_directory(temp_dir)
            
            # Create macro file
            macro_path = temp_dir / "temp_create_masks.ijm"
            
            # Convert paths to absolute paths
            roi_dir = str(roi_file.parent.absolute())
            mask_dir = str(mask_file.parent.absolute())
            output_dir = str(Path(output_directory).absolute())
            
            # Create macro content
            macro_content = self._generate_macro_content(roi_dir, mask_dir, output_dir)
            
            # Write macro file
            with open(macro_path, 'w') as f:
                f.write(macro_content)
            
            self.logger.info(f"Created macro file: {macro_path}")
            return macro_path
            
        except Exception as e:
            self.logger.error(f"Error creating macro file: {str(e)}")
            return None
    
    def _generate_macro_content(self, roi_dir: str, mask_dir: str, output_dir: str) -> str:
        """Generate the ImageJ macro content."""
        return f"""
// ImageJ macro for creating cell masks
// Parameters will be passed from Python

roi_dir = "{roi_dir}";
mask_dir = "{mask_dir}";
output_dir = "{output_dir}";

// Create output directory if it doesn't exist
if (!File.exists(output_dir)) {{
    File.makeDirectory(output_dir);
}}

// Process all ROI files in the directory
roi_files = getFileList(roi_dir);
for (i = 0; i < roi_files.length; i++) {{
    if (endsWith(roi_files[i], ".zip")) {{
        roi_path = roi_dir + File.separator + roi_files[i];
        
        // Find corresponding mask file
        mask_name = replace(roi_files[i], "ROIs_", "");
        mask_name = replace(mask_name, "_rois.zip", "");
        mask_name = "MASK_" + mask_name + ".tif";
        mask_path = mask_dir + File.separator + mask_name;
        
        if (File.exists(mask_path)) {{
            // Open the mask image
            open(mask_path);
            
            // Load ROIs
            roiManager("Open", roi_path);
            
            // Get ROI count
            roi_count = roiManager("count");
            
            // Process each ROI
            for (j = 0; j < roi_count; j++) {{
                roiManager("Select", j);
                
                // Create mask from ROI
                run("Create Selection");
                run("Create Mask");
                
                // Save individual mask
                output_name = replace(roi_files[i], ".zip", "_cell_" + (j+1) + ".tif");
                output_path = output_dir + File.separator + output_name;
                saveAs("Tiff", output_path);
                
                // Close the mask
                close();
                
                // Reopen the original mask for next iteration
                open(mask_path);
                roiManager("Open", roi_path);
            }}
            
            // Close the original mask
            close();
        }}
    }}
}}

print("Cell mask creation completed.");
"""
    
    def _run_imagej_macro(self, macro_file: Path, imagej_path: str, auto_close: bool) -> bool:
        """Run ImageJ macro to create cell masks."""
        try:
            # Ensure ImageJ path is executable
            imagej_executable = self.filesystem_port.ensure_executable(imagej_path)
            
            # Build command
            cmd = [str(imagej_executable), '-macro', str(macro_file)]
            
            self.logger.info(f"Running ImageJ command: {' '.join(cmd)}")
            
            # Run with progress
            result = self.subprocess_port.run_with_progress(
                cmd,
                title="ImageJ: Create Cell Masks"
            )
            
            # Check result
            if result != 0:
                self.logger.error(f"ImageJ returned non-zero exit code: {result}")
                return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error running ImageJ: {str(e)}")
            return False
