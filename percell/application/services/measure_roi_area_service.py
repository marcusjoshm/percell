"""
Measure ROI Area Application Service.

This service implements the use case for measuring ROI areas from ROI files
and corresponding raw image files using ImageJ.
"""

import os
import tempfile
from pathlib import Path
from typing import Optional, Dict, List, Tuple

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


class MeasureROIAreaService:
    """
    Application service for measuring ROI areas using ImageJ.
    
    This service coordinates the domain operations needed to:
    1. Find ROI files and corresponding image files
    2. Create temporary ImageJ macros with embedded parameters
    3. Execute ImageJ to measure ROI areas and generate CSV reports
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
        self.logger = logging_port.get_logger("MeasureROIAreaService")
    
    def measure_roi_areas(
        self,
        input_directory: str,
        output_directory: str,
        imagej_path: str,
        auto_close: bool = True
    ) -> Dict[str, any]:
        """
        Measure ROI areas for all found ROI-image pairs.
        
        Args:
            input_directory: Input directory containing raw data
            output_directory: Output directory containing processed data
            imagej_path: Path to ImageJ executable
            auto_close: Whether to auto-close ImageJ after each measurement
            
        Returns:
            Dict containing measurement results and statistics
        """
        try:
            self.logger.info("Starting ROI area measurement...")
            self.logger.info(f"Input directory: {input_directory}")
            self.logger.info(f"Output directory: {output_directory}")
            
            # Validate inputs
            if not self._validate_inputs(input_directory, output_directory):
                return {"success": False, "error": "Input validation failed"}
            
            # Find ROI-image pairs
            pairs = self._find_roi_image_pairs(input_directory, output_directory)
            
            if not pairs:
                self.logger.warning("No ROI-image pairs found for measurement")
                return {"success": True, "message": "No ROI-image pairs found", "pairs": []}
            
            self.logger.info(f"Found {len(pairs)} ROI-image pairs for measurement")
            
            # Get macro template path
            macro_template = Path(__file__).parent.parent.parent / "macros" / "measure_roi_area.ijm"
            
            if not macro_template.exists():
                self.logger.error(f"Macro template not found: {macro_template}")
                return {"success": False, "error": f"Macro template not found: {macro_template}"}
            
            success_count = 0
            total_count = len(pairs)
            failed_pairs = []
            
            # Process all pairs
            for roi_file, image_file, csv_file in pairs:
                self.logger.info(f"Processing pair {success_count + 1}/{total_count}")
                self.logger.info(f"  ROI: {roi_file}")
                self.logger.info(f"  Image: {image_file}")
                self.logger.info(f"  Output: {csv_file}")
                
                # Create macro with parameters
                macro_file = self._create_macro_with_parameters(
                    str(macro_template), roi_file, image_file, csv_file, auto_close
                )
                
                if not macro_file:
                    self.logger.error(f"Failed to create macro for {roi_file}")
                    failed_pairs.append((roi_file, image_file, "Failed to create macro"))
                    continue
                
                try:
                    # Run ImageJ macro
                    if self._run_imagej_macro(imagej_path, macro_file, auto_close):
                        if os.path.exists(csv_file):
                            self.logger.info(f"Successfully measured ROIs: {csv_file}")
                            success_count += 1
                        else:
                            self.logger.warning(f"Macro completed but CSV file not found: {csv_file}")
                            failed_pairs.append((roi_file, image_file, "CSV file not generated"))
                    else:
                        self.logger.error(f"Failed to run ImageJ macro for {roi_file}")
                        failed_pairs.append((roi_file, image_file, "ImageJ macro execution failed"))
                        # Stop processing if ImageJ fails consistently
                        break
                    
                finally:
                    # Clean up temporary macro file
                    self._cleanup_temp_macro(macro_file)
            
            # Prepare results
            results = {
                "success": success_count > 0,
                "total_pairs": total_count,
                "successful_pairs": success_count,
                "failed_pairs": failed_pairs,
                "output_directory": output_directory
            }
            
            self.logger.info(f"ROI area measurement completed: {success_count}/{total_count} successful")
            return results
            
        except Exception as e:
            self.logger.error(f"Error in measure_roi_areas: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def _validate_inputs(self, input_directory: str, output_directory: str) -> bool:
        """Validate input directories."""
        try:
            input_path = Path(input_directory)
            output_path = Path(output_directory)
            
            if not input_path.exists():
                self.logger.error(f"Input directory does not exist: {input_directory}")
                return False
            
            # Create output directory if it doesn't exist
            self.filesystem_port.create_directory(output_path)
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error validating inputs: {str(e)}")
            return False
    
    def _find_roi_image_pairs(
        self, 
        input_directory: str, 
        output_directory: str
    ) -> List[Tuple[str, str, str]]:
        """
        Find ROI files and corresponding image files for measurement.
        
        Args:
            input_directory: Input directory containing raw data
            output_directory: Output directory containing processed data
            
        Returns:
            List of tuples (roi_file, image_file, csv_file)
        """
        try:
            input_path = Path(input_directory)
            output_path = Path(output_directory)
            pairs = []
            
            # Find ROI files in output directory
            roi_files = list(output_path.glob("**/*.zip")) + list(output_path.glob("**/*.roi"))
            
            if not roi_files:
                self.logger.warning(f"No ROI files found in {output_directory}")
                return pairs
            
            self.logger.info(f"Found {len(roi_files)} ROI files")
            
            for roi_file in roi_files:
                roi_name = roi_file.name
                
                # Extract base name from ROI filename
                if roi_name.endswith(".roi"):
                    # Remove ".roi" suffix
                    base_name = roi_name[:-4]
                elif roi_name.endswith(".zip"):
                    # Remove ".zip" suffix
                    base_name = roi_name[:-4]
                else:
                    self.logger.warning(f"Unrecognized ROI file pattern: {roi_name}")
                    continue
                
                self.logger.info(f"Extracted base name: {base_name}")
                
                # Search for corresponding image files in input directory
                found_match = False
                
                # Search recursively in input directory for matching image files
                for img_ext in ['.tif', '.tiff', '.png', '.jpg']:
                    # Try different matching patterns
                    search_patterns = [
                        f"**/{base_name}{img_ext}",  # Exact match
                        f"**/*{base_name}*{img_ext}",  # Contains base name
                        f"**/*{base_name.split('_')[0]}*{base_name.split('_')[1]}*{base_name.split('_')[2]}*{img_ext}",  # Match region, channel, timepoint
                    ]
                    
                    for pattern in search_patterns:
                        matching_images = list(input_path.glob(pattern))
                        
                        for potential_image in matching_images:
                            # Create output CSV file path with condition and "cell_area" in the filename
                            # Extract condition from ROI file path
                            roi_path = Path(roi_file)
                            condition_name = roi_path.parent.name  # Get the condition directory name
                            
                            # Extract the ROI directory name from the ROI filename
                            roi_name = roi_file.stem  # Get filename without extension
                            # Remove "ROIs_" prefix and "_rois" suffix to get the directory name
                            if roi_name.startswith("ROIs_"):
                                roi_dir_name = roi_name[5:]  # Remove "ROIs_" prefix
                            else:
                                roi_dir_name = roi_name
                            
                            if roi_dir_name.endswith("_rois"):
                                roi_dir_name = roi_dir_name[:-5]  # Remove "_rois" suffix
                            
                            # Create filename with condition and ROI directory name
                            csv_filename = f"{condition_name}_{roi_dir_name}_cell_area.csv"
                            csv_file = output_path / "analysis" / csv_filename
                            csv_file.parent.mkdir(parents=True, exist_ok=True)
                            
                            pairs.append((str(roi_file), str(potential_image), str(csv_file)))
                            self.logger.info(f"Found pair: ROI={roi_file.name}, Image={potential_image.name}")
                            found_match = True
                            break
                        
                        if found_match:
                            break
                    
                    if found_match:
                        break
                
                if not found_match:
                    self.logger.warning(f"No matching image found for ROI file: {roi_name}")
            
            self.logger.info(f"Found {len(pairs)} ROI-image pairs for measurement")
            return pairs
            
        except Exception as e:
            self.logger.error(f"Error finding ROI-image pairs: {str(e)}")
            return []
    
    def _create_macro_with_parameters(
        self,
        macro_template_file: str,
        roi_file: str,
        image_file: str,
        csv_file: str,
        auto_close: bool
    ) -> Optional[str]:
        """
        Create a dedicated ImageJ macro file with specific parameters.
        
        Args:
            macro_template_file: Path to the macro template file
            roi_file: Path to the ROI file (.zip or .roi)
            image_file: Path to the raw image file
            csv_file: Path to output CSV file
            auto_close: Whether the macro should automatically close ImageJ
            
        Returns:
            Path to the created macro file, or None if error
        """
        try:
            # Validate inputs
            if not os.path.exists(macro_template_file):
                self.logger.error(f"Macro template file not found: {macro_template_file}")
                return None
                
            if not os.path.exists(roi_file):
                self.logger.error(f"ROI file not found: {roi_file}")
                return None
                
            if not os.path.exists(image_file):
                self.logger.error(f"Image file not found: {image_file}")
                return None
            
            # Ensure output directory exists
            os.makedirs(os.path.dirname(csv_file), exist_ok=True)
            
            # Read the macro template
            with open(macro_template_file, 'r') as f:
                macro_content = f.read()

            # Convert paths to forward slashes for ImageJ compatibility
            roi_file_clean = roi_file.replace(os.sep, '/')
            image_file_clean = image_file.replace(os.sep, '/')
            csv_file_clean = csv_file.replace(os.sep, '/')
            auto_close_str = str(auto_close).lower()

            # Build a header that sets variables, and strip any ImageJ2 parameter annotations ("#@ ...")
            header = (
                f'roi_file = "{roi_file_clean}";\n'
                f'image_file = "{image_file_clean}";\n'
                f'csv_file = "{csv_file_clean}";\n'
                f'auto_close = {auto_close_str};\n'
            )
            
            # Build a clean macro body programmatically to avoid any stray '#'
            body = "\n".join([
                'setBatchMode(true);',
                'if (roi_file == "") exit("Error: ROI file not specified");',
                'if (image_file == "") exit("Error: Image file not specified");',
                'if (csv_file == "") exit("Error: CSV output file not specified");',
                'if (!File.exists(roi_file)) exit("Error: ROI file does not exist: " + roi_file);',
                'if (!File.exists(image_file)) exit("Error: Image file does not exist: " + image_file);',
                'open(image_file);',
                'image_name = getTitle();',
                'run("ROI Manager...");',
                'roiManager("Open", roi_file);',
                'num_rois = roiManager("count");',
                'if (num_rois > 0) {',
                '  run("Clear Results");',
                '  run("Set Measurements...", "area display redirect=None decimal=3");',
                '  roiManager("Deselect");',
                '  roiManager("Measure");',
                '  image_basename = File.getName(image_file);',
                '  if (endsWith(image_basename, ".tif")) image_basename = substring(image_basename, 0, lengthOf(image_basename) - 4);',
                '  else if (endsWith(image_basename, ".tiff")) image_basename = substring(image_basename, 0, lengthOf(image_basename) - 5);',
                '  for (i = 0; i < num_rois; i++) {',
                '    setResult("Image", i, image_basename);',
                '    roiManager("Select", i);',
                '    cell_number = "CELL" + (i + 1);',
                '    setResult("Cell_ID", i, cell_number);',
                '  }',
                '  updateResults();',
                '  saveAs("Results", csv_file);',
                '}',
                'if (isOpen("ROI Manager")) { selectWindow("ROI Manager"); run("Close"); }',
                'if (isOpen("Results")) { selectWindow("Results"); run("Close"); }',
                'while (nImages > 0) { selectImage(nImages); close(); }',
                'if (auto_close) exit();'
            ])
            
            # Combine header and body
            macro_content = header + "\n" + body
            
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
                title="ImageJ: Measure ROI Areas",
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
            os.remove(temp_macro_file)
            self.logger.debug(f"Cleaned up temporary macro file: {temp_macro_file}")
        except Exception as e:
            self.logger.warning(f"Could not clean up temporary macro file {temp_macro_file}: {e}")
