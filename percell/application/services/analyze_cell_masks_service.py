"""
Analyze Cell Masks Application Service.

This service implements the use case for analyzing cell mask files
using ImageJ to measure particle properties and generate CSV reports.
"""

import os
import tempfile
import glob
import re
from pathlib import Path
from typing import Optional, Dict, List, Tuple
import pandas as pd

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


class AnalyzeCellMasksService:
    """
    Application service for analyzing cell mask files using ImageJ.
    
    This service coordinates the domain operations needed to:
    1. Find mask files based on filtering criteria
    2. Create temporary ImageJ macros with embedded parameters
    3. Execute ImageJ to analyze masks and generate measurements
    4. Combine CSV results into consolidated reports
    5. Clean up temporary files
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
        self.logger = logging_port.get_logger("AnalyzeCellMasksService")
    
    def analyze_cell_masks(
        self,
        input_directory: str,
        output_directory: str,
        imagej_path: str,
        macro_path: str = "percell/macros/analyze_cell_masks.ijm",
        regions: Optional[List[str]] = None,
        timepoints: Optional[List[str]] = None,
        max_files: int = 50,
        channels: Optional[List[str]] = None
    ) -> Dict[str, any]:
        """
        Analyze cell mask files using ImageJ.
        
        Args:
            input_directory: Directory containing mask files
            output_directory: Directory for output analysis files
            imagej_path: Path to ImageJ executable
            macro_path: Path to the ImageJ macro file
            regions: Specific regions to process (e.g., R_1 R_2)
            timepoints: Specific timepoints to process (e.g., t00 t03)
            max_files: Maximum number of files to process per directory
            channels: Channels to process
            
        Returns:
            Dict containing analysis results and statistics
        """
        try:
            self.logger.info(f"Starting cell mask analysis process")
            self.logger.info(f"Input directory: {input_directory}")
            self.logger.info(f"Output directory: {output_directory}")
            
            # Validate inputs
            if not self._validate_inputs(input_directory, output_directory, macro_path):
                return {"success": False, "error": "Input validation failed"}
            
            # Find mask files grouped by directory
            mask_files_by_dir = self._find_mask_files(
                input_directory, 
                max_files,
                regions,
                timepoints
            )
            
            if not mask_files_by_dir:
                self.logger.warning(f"No mask files found in {input_directory} matching the specified filters.")
                return {"success": False, "error": "No mask files found", "mask_files_by_dir": {}}
            
            self.logger.info(f"Found {len(mask_files_by_dir)} directories with mask files to process")
            
            # Process each directory
            success_count = 0
            total_dirs = len(mask_files_by_dir)
            failed_directories = []
            
            for dir_path, mask_paths in mask_files_by_dir.items():
                self.logger.info(f"Processing directory: {dir_path} with {len(mask_paths)} mask files")
                
                success = self._process_mask_directory(
                    dir_path, 
                    mask_paths, 
                    output_directory, 
                    imagej_path, 
                    macro_path,
                    auto_close=True  # Always auto-close for batch processing
                )
                
                if success:
                    success_count += 1
                else:
                    failed_directories.append(str(dir_path))
            
            # Prepare results
            results = {
                "success": success_count > 0,
                "total_directories": total_dirs,
                "successful_directories": success_count,
                "failed_directories": failed_directories,
                "output_directory": output_directory
            }
            
            # Combine CSV files if multiple directories were processed successfully
            if success_count > 1:
                combined_file = self._combine_csv_files(output_directory)
                if combined_file:
                    results["combined_csv_file"] = combined_file
                    self.logger.info(f"Created combined analysis file: {combined_file}")
            
            # Report overall results
            if success_count > 0:
                self.logger.info(f"Cell mask analysis completed successfully: {success_count}/{total_dirs} directories processed")
            else:
                self.logger.error("Cell mask analysis failed - no successful directories processed")
            
            return results
            
        except Exception as e:
            self.logger.error(f"Error in analyze_cell_masks: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def _validate_inputs(self, input_directory: str, output_directory: str, macro_path: str) -> bool:
        """Validate input directories and files."""
        try:
            input_path = Path(input_directory)
            output_path = Path(output_directory)
            macro_file = Path(macro_path)
            
            if not input_path.exists():
                self.logger.error(f"Input directory does not exist: {input_directory}")
                return False
            
            if not macro_file.exists():
                self.logger.error(f"Macro file does not exist: {macro_path}")
                return False
            
            # Create output directory if it doesn't exist
            self.filesystem_port.create_directory(output_path)
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error validating inputs: {str(e)}")
            return False
    
    def _find_mask_files(
        self,
        input_directory: str,
        max_files: int,
        regions: Optional[List[str]] = None,
        timepoints: Optional[List[str]] = None
    ) -> Dict[Path, List[Path]]:
        """Find mask files grouped by directory with filtering."""
        try:
            input_path = Path(input_directory)
            mask_files_by_dir = {}
            
            # Find all subdirectories
            for subdir in input_path.iterdir():
                if not subdir.is_dir() or subdir.name.startswith('.'):
                    continue
                
                # Find mask files in this subdirectory
                mask_files = list(subdir.glob("*_mask.tif"))
                
                if not mask_files:
                    continue
                
                # Apply filters
                filtered_files = self._filter_mask_files(mask_files, regions, timepoints)
                
                if filtered_files:
                    # Limit the number of files per directory
                    if len(filtered_files) > max_files:
                        self.logger.warning(f"Limiting {subdir.name} to {max_files} files (found {len(filtered_files)})")
                        filtered_files = filtered_files[:max_files]
                    
                    mask_files_by_dir[subdir] = filtered_files
            
            return mask_files_by_dir
            
        except Exception as e:
            self.logger.error(f"Error finding mask files: {str(e)}")
            return {}
    
    def _filter_mask_files(
        self,
        mask_files: List[Path],
        regions: Optional[List[str]] = None,
        timepoints: Optional[List[str]] = None
    ) -> List[Path]:
        """Filter mask files based on regions and timepoints."""
        filtered_files = []
        
        for mask_file in mask_files:
            filename = mask_file.name
            
            # Check if file matches region filter
            if regions:
                region_match = any(region in filename for region in regions)
                if not region_match:
                    continue
            
            # Check if file matches timepoint filter
            if timepoints:
                timepoint_match = any(timepoint in filename for timepoint in timepoints)
                if not timepoint_match:
                    continue
            
            filtered_files.append(mask_file)
        
        return filtered_files
    
    def _process_mask_directory(
        self,
        dir_path: Path,
        mask_paths: List[Path],
        output_directory: str,
        imagej_path: str,
        macro_path: str,
        auto_close: bool
    ) -> bool:
        """Process a single directory of mask files."""
        try:
            self.logger.info(f"Processing {len(mask_paths)} mask files in {dir_path}")
            
            # Create temporary macro with embedded parameters
            temp_macro_file = self._create_macro_with_parameters(
                macro_path, mask_paths, output_directory, auto_close
            )
            
            if not temp_macro_file:
                self.logger.error("Failed to create macro with parameters")
                return False
            
            try:
                # Run the ImageJ macro
                success = self._run_imagej_macro(imagej_path, temp_macro_file, auto_close)
                
                if success:
                    self.logger.info(f"Successfully analyzed masks in {dir_path}")
                    return True
                else:
                    self.logger.error(f"ImageJ macro execution failed for {dir_path}")
                    return False
                    
            finally:
                # Clean up temporary macro file
                self._cleanup_temp_macro(temp_macro_file)
                
        except Exception as e:
            self.logger.error(f"Error processing mask directory {dir_path}: {str(e)}")
            return False
    
    def _create_macro_with_parameters(
        self,
        macro_template_file: str,
        mask_paths: List[Path],
        output_directory: str,
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
            normalized_mask_paths = []
            for mask_path in mask_paths:
                normalized_path = str(mask_path).replace('\\', '/')
                normalized_mask_paths.append(normalized_path)
            
            output_dir_path = str(output_directory).replace('\\', '/')
            
            # Create semicolon-separated list of mask files
            mask_files_list = ";".join(normalized_mask_paths)
            
            # Add parameter definitions at the beginning
            parameter_definitions = f"""
// Parameters embedded from Python script
mask_files_list = "{mask_files_list}";
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
                title="ImageJ: Analyze Cell Masks",
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
    
    def _combine_csv_files(self, output_directory: str) -> Optional[str]:
        """
        Combine all CSV summary files in the output directory into a single consolidated file.
        
        Args:
            output_directory: Directory containing individual CSV summary files
        
        Returns:
            Path to the combined CSV file, or None if no files were found/combined
        """
        try:
            # Find all CSV files in the output directory
            csv_pattern = os.path.join(output_directory, '*_summary.csv')
            csv_files = glob.glob(csv_pattern)
            
            if not csv_files:
                self.logger.warning(f"No CSV summary files found in {output_directory} to combine")
                return None
            
            self.logger.info(f"Found {len(csv_files)} CSV summary files to combine")
            
            # Read all CSV files into pandas DataFrames
            all_dfs = []
            for csv_file in csv_files:
                try:
                    # Extract condition/region information from filename
                    filename = os.path.basename(csv_file)
                    base_name = filename.replace('_summary.csv', '')
                    
                    # Read the CSV file
                    df = pd.read_csv(csv_file)
                    
                    # Add columns to identify the source
                    # Parse out experiment details from the filename
                    if filename.startswith('masks_'):
                        # Example: masks_Dish_9_FUS-P525L_VCPi_+_Washout_+_DMSO_R_1_t00_summary.csv
                        parts = base_name.split('_')
                        
                        # Extract information - assuming a specific format
                        # This may need to be adjusted based on actual filename patterns
                        region_idx = -2 if parts[-2].startswith('R') else None
                        time_idx = -1 if parts[-1].startswith('t') else None
                        
                        if region_idx:
                            df['Region'] = parts[region_idx]
                        if time_idx:
                            df['Timepoint'] = parts[time_idx]
                        
                        # Extract condition by removing timepoint and region
                        condition_parts = parts[1:-2] if region_idx and time_idx else parts[1:]
                        df['Condition'] = '_'.join(condition_parts)
                    else:
                        # Generic handling if the filename doesn't match expected pattern
                        df['Source'] = base_name
                    
                    all_dfs.append(df)
                    self.logger.info(f"Processed {filename} with {len(df)} rows")
                    
                except Exception as e:
                    self.logger.warning(f"Error reading CSV file {csv_file}: {e}")
                    continue
            
            if not all_dfs:
                self.logger.warning("No valid data found in CSV files")
                return None
            
            # Combine all DataFrames
            combined_df = pd.concat(all_dfs, ignore_index=True)
            
            # Generate output filename based on common elements
            # Extract what appears to be the experiment identifier (e.g., Dish_9)
            experiment_ids = set()
            for csv_file in csv_files:
                filename = os.path.basename(csv_file)
                if filename.startswith('masks_'):
                    parts = filename.split('_')
                    if len(parts) > 2:
                        experiment_ids.add(f"{parts[1]}_{parts[2]}")
            
            # Create a combined filename
            if experiment_ids:
                combined_name = '_'.join(sorted(experiment_ids))
            else:
                # Fallback if we can't extract experiment IDs
                combined_name = "combined_analysis"
            
            combined_file = os.path.join(output_directory, f"{combined_name}_combined_analysis.csv")
            
            # Save the combined DataFrame
            combined_df.to_csv(combined_file, index=False)
            self.logger.info(f"Created combined analysis file: {combined_file} with {len(combined_df)} rows")
            
            return combined_file
            
        except Exception as e:
            self.logger.error(f"Error combining CSV files: {str(e)}")
            return None
