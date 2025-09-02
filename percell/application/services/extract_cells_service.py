"""
Extract Cells Application Service.

This service implements the use case for extracting individual cells
from images using ROIs and ImageJ macros.
"""

import os
import tempfile
import shutil
import re
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


class ExtractCellsService:
    """
    Application service for extracting individual cells from images using ROIs.
    
    This service coordinates the domain operations needed to:
    1. Find ROI files and corresponding image files
    2. Create temporary ImageJ macros with embedded parameters
    3. Execute ImageJ to extract individual cells
    4. Clean up temporary files
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
        self.logger = logging_port.get_logger("ExtractCellsService")
    
    def extract_cells(
        self,
        roi_directory: str,
        raw_data_directory: str,
        output_directory: str,
        imagej_path: str,
        macro_path: str = "percell/macros/extract_cells.ijm",
        regions: Optional[List[str]] = None,
        timepoints: Optional[List[str]] = None,
        conditions: Optional[List[str]] = None,
        channels: Optional[List[str]] = None,
        auto_close: bool = False
    ) -> Dict[str, any]:
        """
        Extract individual cells from images using ROIs.
        
        Args:
            roi_directory: Directory containing ROI files
            raw_data_directory: Directory containing original images
            output_directory: Directory where individual cells will be saved
            imagej_path: Path to ImageJ executable
            macro_path: Path to the ImageJ macro file
            regions: List of regions to process (optional)
            timepoints: List of timepoints to process (optional)
            conditions: List of conditions to process (optional)
            channels: List of channels to process (optional)
            auto_close: Whether to close ImageJ after execution
            
        Returns:
            Dict containing extraction results and statistics
        """
        try:
            self.logger.info(f"Starting cell extraction process")
            self.logger.info(f"ROI directory: {roi_directory}")
            self.logger.info(f"Raw data directory: {raw_data_directory}")
            self.logger.info(f"Output directory: {output_directory}")
            
            # Validate inputs
            if not self._validate_inputs(roi_directory, raw_data_directory, macro_path):
                return {"success": False, "error": "Input validation failed"}
            
            # Find ROI files
            roi_files = self._find_roi_files(roi_directory, regions, timepoints, conditions)
            if not roi_files:
                self.logger.warning("No ROI files found")
                return {"success": False, "error": "No ROI files found", "roi_files": []}
            
            self.logger.info(f"Found {len(roi_files)} ROI files to process")
            
            # Process each ROI file
            successful_extractions = 0
            total_cells_extracted = 0
            failed_extractions = []
            
            for roi_file in roi_files:
                # Skip if channels are specified and this file doesn't match any of them
                if channels and not self._file_matches_channels(roi_file, channels):
                    self.logger.info(f"Skipping {roi_file} - no matching channels")
                    continue
                
                self.logger.info(f"Processing ROI file: {roi_file}")
                
                # Find the corresponding image file
                image_file = self._find_image_for_roi(roi_file, raw_data_directory)
                
                if image_file:
                    # Create output directory for this ROI
                    cell_output_dir = self._create_output_dir_for_roi(roi_file, output_directory)
                    
                    # Extract cells for this ROI
                    extraction_result = self._extract_cells_for_roi(
                        roi_file, image_file, cell_output_dir, imagej_path, macro_path, auto_close
                    )
                    
                    if extraction_result["success"]:
                        successful_extractions += 1
                        total_cells_extracted += extraction_result["cells_extracted"]
                        self.logger.info(f"Successfully extracted {extraction_result['cells_extracted']} cells to {cell_output_dir}")
                    else:
                        failed_extractions.append({
                            "roi_file": str(roi_file),
                            "error": extraction_result["error"]
                        })
                        self.logger.error(f"Cell extraction failed for {roi_file}: {extraction_result['error']}")
                else:
                    failed_extractions.append({
                        "roi_file": str(roi_file),
                        "error": "Could not find matching image file"
                    })
                    self.logger.error(f"Could not find matching image file for {roi_file}")
            
            # Prepare results
            results = {
                "success": successful_extractions > 0,
                "total_roi_files": len(roi_files),
                "successful_extractions": successful_extractions,
                "total_cells_extracted": total_cells_extracted,
                "failed_extractions": failed_extractions
            }
            
            self.logger.info(f"Cell extraction completed. Successfully processed {successful_extractions} of {len(roi_files)} ROI files.")
            self.logger.info(f"Total cells extracted: {total_cells_extracted}")
            
            return results
            
        except Exception as e:
            self.logger.error(f"Error in extract_cells: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def _validate_inputs(self, roi_directory: str, raw_data_directory: str, macro_path: str) -> bool:
        """Validate input directories and files."""
        try:
            roi_path = Path(roi_directory)
            raw_data_path = Path(raw_data_directory)
            macro_file = Path(macro_path)
            
            if not roi_path.exists():
                self.logger.error(f"ROI directory does not exist: {roi_directory}")
                return False
            
            if not raw_data_path.exists():
                self.logger.error(f"Raw data directory does not exist: {raw_data_directory}")
                return False
            
            if not macro_file.exists():
                self.logger.error(f"Macro file does not exist: {macro_path}")
                return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error validating inputs: {str(e)}")
            return False
    
    def _find_roi_files(
        self, 
        roi_directory: str, 
        regions: Optional[List[str]] = None,
        timepoints: Optional[List[str]] = None,
        conditions: Optional[List[str]] = None
    ) -> List[Path]:
        """Find ROI files based on filtering criteria."""
        try:
            roi_path = Path(roi_directory)
            roi_files = []
            
            # Find all ROI files in all subdirectories
            for condition_dir in roi_path.glob("*"):
                if condition_dir.is_dir() and not condition_dir.name.startswith('.'):
                    self.logger.debug(f"Processing condition directory: {condition_dir.name}")
                    
                    # Check for ROI files in this condition directory
                    condition_roi_files = list(condition_dir.glob("*.zip"))
                    self.logger.debug(f"Found {len(condition_roi_files)} ROI files in {condition_dir.name}")
                    
                    # Filter by regions if specified
                    if regions:
                        condition_roi_files = self._filter_files_by_pattern(condition_roi_files, regions)
                    
                    # Filter by timepoints if specified
                    if timepoints:
                        condition_roi_files = self._filter_files_by_pattern(condition_roi_files, timepoints)
                    
                    # Filter by conditions if specified
                    if conditions and condition_dir.name not in conditions:
                        continue
                    
                    roi_files.extend(condition_roi_files)
            
            return roi_files
            
        except Exception as e:
            self.logger.error(f"Error finding ROI files: {str(e)}")
            return []
    
    def _filter_files_by_pattern(self, files: List[Path], patterns: List[str]) -> List[Path]:
        """Filter files by pattern matching."""
        filtered_files = []
        for file_path in files:
            file_name = file_path.name
            for pattern in patterns:
                if pattern in file_name:
                    filtered_files.append(file_path)
                    break
        return filtered_files
    
    def _file_matches_channels(self, roi_file: Path, channels: List[str]) -> bool:
        """Check if ROI file matches any of the specified channels."""
        file_channels = [ch for ch in channels if ch in str(roi_file)]
        return len(file_channels) > 0
    
    def _find_image_for_roi(self, roi_file: Path, raw_data_directory: str) -> Optional[Path]:
        """Find the corresponding image file for a ROI file."""
        try:
            # Extract condition from ROI file path
            condition = roi_file.parent.name
            
            # Look for image files in the raw data directory
            raw_data_path = Path(raw_data_directory) / condition
            
            if not raw_data_path.exists():
                return None
            
            # Look for TIF files that might match the ROI
            # This is a simplified matching - could be enhanced with more sophisticated logic
            tif_files = list(raw_data_path.glob("*.tif")) + list(raw_data_path.glob("*.tiff"))
            
            if tif_files:
                # For now, return the first TIF file found
                # In a real implementation, you might want more sophisticated matching
                return tif_files[0]
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error finding image for ROI {roi_file}: {str(e)}")
            return None
    
    def _create_output_dir_for_roi(self, roi_file: Path, output_base_dir: str) -> Path:
        """Create output directory for a specific ROI file."""
        try:
            # Extract components from ROI filename
            roi_name = roi_file.stem
            condition = roi_file.parent.name
            
            # Parse filename components using regex
            cleaned_name = roi_name.replace('.zip', '')
            
            # Extract components using regex
            channel_match = re.search(r'_(ch\d+)_', cleaned_name)
            timepoint_match = re.search(r'_(t\d+)(?:_|$)', cleaned_name)
            
            # Default to empty strings if not found
            channel = channel_match.group(1) if channel_match else ""
            timepoint = timepoint_match.group(1) if timepoint_match else ""
            
            # Remove channel and timepoint parts to get the region
            region = cleaned_name
            if channel:
                region = region.replace(f"_{channel}", "")
            if timepoint:
                region = region.replace(f"_{timepoint}", "")
            
            # Clean up any trailing underscores
            region = region.rstrip("_")
            
            # Create the output directory structure
            # Format: output_base_dir/condition/region_channel_timepoint
            output_dir = Path(output_base_dir) / condition / f"{region}_{channel}_{timepoint}"
            self.filesystem_port.create_directory(output_dir)
            
            self.logger.debug(f"Created output directory: {output_dir}")
            return output_dir
            
        except Exception as e:
            self.logger.error(f"Error creating output directory for {roi_file}: {str(e)}")
            # Fallback to simple directory structure
            fallback_dir = Path(output_base_dir) / condition / roi_file.stem
            self.filesystem_port.create_directory(fallback_dir)
            return fallback_dir
    
    def _extract_cells_for_roi(
        self,
        roi_file: Path,
        image_file: Path,
        output_dir: Path,
        imagej_path: str,
        macro_path: str,
        auto_close: bool
    ) -> Dict[str, any]:
        """Extract cells for a specific ROI file."""
        try:
            # Create temporary macro with embedded parameters
            self.logger.debug("Creating macro with embedded parameters...")
            temp_macro_file = self._create_macro_with_parameters(
                macro_path, roi_file, image_file, output_dir, auto_close
            )
            
            if not temp_macro_file:
                return {"success": False, "error": "Failed to create macro with parameters"}
            
            try:
                # Run the ImageJ macro
                self.logger.debug("Starting cell extraction process...")
                success = self._run_imagej_macro(imagej_path, temp_macro_file, auto_close)
                
                if success:
                    # Check if cells were actually extracted
                    cell_files = list(output_dir.glob("CELL*.tif"))
                    if cell_files:
                        return {
                            "success": True,
                            "cells_extracted": len(cell_files),
                            "output_directory": str(output_dir)
                        }
                    else:
                        return {
                            "success": False,
                            "error": "No cell files were created",
                            "output_directory": str(output_dir)
                        }
                else:
                    return {"success": False, "error": "ImageJ macro execution failed"}
                    
            finally:
                # Clean up temporary macro file
                self._cleanup_temp_macro(temp_macro_file)
                
        except Exception as e:
            self.logger.error(f"Error extracting cells for {roi_file}: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def _create_macro_with_parameters(
        self,
        macro_template_file: str,
        roi_file: Path,
        image_file: Path,
        output_dir: Path,
        auto_close: bool
    ) -> Optional[str]:
        """Create a temporary macro file with parameters embedded."""
        try:
            # Read the dedicated macro template
            with open(macro_template_file, 'r') as f:
                template_content = f.read()
            
            # Remove the #@ parameter declarations since we're embedding the values
            lines = template_content.split('\n')
            filtered_lines = []
            for line in lines:
                if not line.strip().startswith('#@'):
                    filtered_lines.append(line)
            
            # Ensure paths use forward slashes for ImageJ
            roi_file_path = str(roi_file).replace('\\', '/')
            image_file_path = str(image_file).replace('\\', '/')
            output_dir_path = str(output_dir).replace('\\', '/')
            
            # Add parameter definitions at the beginning
            parameter_definitions = f"""
// Parameters embedded from Python script
roi_file = "{roi_file_path}";
image_file = "{image_file_path}";
output_dir = "{output_dir_path}";
auto_close = {str(auto_close).lower()};
"""
            
            # Combine parameters with the filtered template content
            macro_content = parameter_definitions + '\n'.join(filtered_lines)
            
            # Create temporary macro file
            temp_macro = tempfile.NamedTemporaryFile(mode='w', suffix='.ijm', delete=False)
            temp_macro.write(macro_content)
            temp_macro.close()
            
            self.logger.debug(f"Created temporary macro file: {temp_macro.name}")
            return temp_macro.name
            
        except Exception as e:
            self.logger.error(f"Error creating macro with parameters: {e}")
            return None
    
    def _run_imagej_macro(self, imagej_path: str, macro_file: str, auto_close: bool) -> bool:
        """Run ImageJ with the macro file."""
        try:
            # Use -macro instead of --headless --run to avoid ROI Manager headless issues
            cmd = [imagej_path, "-macro", macro_file]
            
            if auto_close:
                cmd.append("--headless")
            
            self.logger.debug(f"Running ImageJ command: {' '.join(cmd)}")
            
            # Use the subprocess port for execution
            result = self.subprocess_port.run_with_progress(
                cmd, 
                title="ImageJ: Extract Cells",
                capture_output=True,
                text=True
            )
            
            return result == 0
            
        except Exception as e:
            self.logger.error(f"Error running ImageJ macro: {e}")
            return False
    
    def _cleanup_temp_macro(self, temp_macro_file: str) -> None:
        """Clean up temporary macro file."""
        try:
            os.unlink(temp_macro_file)
            self.logger.debug(f"Cleaned up temporary macro file: {temp_macro_file}")
        except Exception as e:
            self.logger.warning(f"Could not clean up temporary macro file {temp_macro_file}: {e}")
