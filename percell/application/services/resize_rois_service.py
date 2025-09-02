"""
Resize ROIs Application Service.

This service implements the use case for resizing ROIs from binned images
using ImageJ to match the original image dimensions.
"""

import os
import tempfile
from pathlib import Path
from typing import Optional, Dict, Any

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


class ResizeROIsService:
    """
    Application service for resizing ROIs using ImageJ.
    
    This service coordinates the domain operations needed to:
    1. Validate input parameters and directories
    2. Check macro file compatibility
    3. Create temporary ImageJ macros with embedded parameters
    4. Execute ImageJ to resize ROIs
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
        self.logger = logging_port.get_logger("ResizeROIsService")
    
    def resize_rois(
        self,
        input_directory: str,
        output_directory: str,
        imagej_path: str,
        channel: str,
        macro_path: str = "percell/macros/resize_rois.ijm",
        auto_close: bool = True
    ) -> Dict[str, Any]:
        """
        Resize ROIs from binned images using ImageJ.
        
        Args:
            input_directory: Input directory containing preprocessed images and ROIs
            output_directory: Output directory for resized ROIs
            imagej_path: Path to ImageJ executable
            channel: Segmentation channel to process ROIs for (e.g., ch00)
            macro_path: Path to the dedicated ImageJ macro file
            auto_close: Whether to close ImageJ when the macro completes
            
        Returns:
            Dict containing resizing results and statistics
        """
        try:
            self.logger.info("Starting ROI resizing process...")
            self.logger.info(f"Input directory: {input_directory}")
            self.logger.info(f"Output directory: {output_directory}")
            self.logger.info(f"Channel: {channel}")
            self.logger.info(f"Macro file: {macro_path}")
            
            # Validate inputs
            if not self._validate_inputs(input_directory, output_directory, channel):
                return {"success": False, "error": "Input validation failed"}
            
            # Check macro file
            if not self._check_macro_file(macro_path):
                return {"success": False, "error": "Macro file validation failed"}
            
            # Create temporary macro with embedded parameters
            self.logger.info("Creating macro with embedded parameters...")
            temp_macro_file = self._create_macro_with_parameters(
                macro_path,
                input_directory,
                output_directory, 
                channel,
                auto_close
            )
            
            if not temp_macro_file:
                return {"success": False, "error": "Failed to create macro with parameters"}
            
            try:
                # Run the ImageJ macro
                self.logger.info("Starting ROI resizing process...")
                success = self._run_imagej_macro(imagej_path, temp_macro_file, auto_close)
                
                if success:
                    self.logger.info("ROI resizing completed successfully")
                    return {
                        "success": True,
                        "input_directory": input_directory,
                        "output_directory": output_directory,
                        "channel": channel,
                        "macro_file": macro_path
                    }
                else:
                    self.logger.error("ROI resizing failed")
                    return {"success": False, "error": "ImageJ macro execution failed"}
                
            finally:
                # Clean up temporary macro file
                self._cleanup_temp_macro(temp_macro_file)
                
        except Exception as e:
            self.logger.error(f"Error in resize_rois: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def _validate_inputs(self, input_directory: str, output_directory: str, channel: str) -> bool:
        """
        Validate input parameters.
        
        Args:
            input_directory: Input directory path
            output_directory: Output directory path  
            channel: Channel specification
            
        Returns:
            True if all inputs are valid, False otherwise
        """
        try:
            # Check input directory exists
            if not os.path.exists(input_directory):
                self.logger.error(f"Input directory does not exist: {input_directory}")
                return False
            
            # Check input directory has content
            if not os.listdir(input_directory):
                self.logger.error(f"Input directory is empty: {input_directory}")
                return False
            
            # Validate channel format
            if not channel.startswith('ch'):
                self.logger.error(f"Channel should start with 'ch' (e.g., 'ch00'): {channel}")
                return False
            
            # Create output directory if it doesn't exist
            try:
                self.filesystem_port.create_directory(Path(output_directory))
                self.logger.info(f"Output directory ready: {output_directory}")
            except Exception as e:
                self.logger.error(f"Cannot create output directory {output_directory}: {e}")
                return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error validating inputs: {str(e)}")
            return False
    
    def _check_macro_file(self, macro_file: str) -> bool:
        """
        Check if the dedicated macro file exists and is readable.
        
        Args:
            macro_file: Path to the macro file
            
        Returns:
            True if macro file is accessible, False otherwise
        """
        try:
            macro_path = Path(macro_file)
            
            if not macro_path.exists():
                self.logger.error(f"Macro file does not exist: {macro_file}")
                return False
            
            if not macro_path.is_file():
                self.logger.error(f"Macro path is not a file: {macro_file}")
                return False
            
            try:
                with open(macro_path, 'r') as f:
                    content = f.read()
                    # Check if it contains the expected parameter declarations
                    if '#@ String input_dir' not in content:
                        self.logger.warning(f"Macro file may not be compatible - missing input_dir parameter")
                    if '#@ String output_dir' not in content:
                        self.logger.warning(f"Macro file may not be compatible - missing output_dir parameter")
                    if '#@ String channel' not in content:
                        self.logger.warning(f"Macro file may not be compatible - missing channel parameter")
                
                self.logger.info(f"Macro file validated: {macro_file}")
                return True
                
            except Exception as e:
                self.logger.error(f"Cannot read macro file {macro_file}: {e}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error checking macro file: {str(e)}")
            return False
    
    def _create_macro_with_parameters(
        self,
        macro_template_file: str,
        input_dir: str,
        output_dir: str,
        channel: str,
        auto_close: bool
    ) -> Optional[str]:
        """
        Create a temporary macro file with parameters embedded from the dedicated macro template.
        
        Args:
            macro_template_file: Path to the dedicated macro template file
            input_dir: Input directory containing binned images and ROIs
            output_dir: Output directory for resized ROIs
            channel: Segmentation channel to process (e.g., ch00)
            auto_close: Whether to add auto-close functionality
            
        Returns:
            Path to the created temporary macro file, or None if error
        """
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
            input_dir_clean = str(input_dir).replace('\\', '/')
            output_dir_clean = str(output_dir).replace('\\', '/')
            
            # Add parameter definitions at the beginning
            parameter_definitions = f"""
// Parameters embedded from Python script
input_dir = "{input_dir_clean}";
output_dir = "{output_dir_clean}";
channel = "{channel}";
auto_close = {str(auto_close).lower()};
"""
            
            # Combine parameters with the filtered template content
            macro_content = parameter_definitions + '\n'.join(filtered_lines)
            
            # Create temporary macro file
            temp_macro = tempfile.NamedTemporaryFile(mode='w', suffix='.ijm', delete=False)
            temp_macro.write(macro_content)
            temp_macro.close()
            
            self.logger.info(f"Created temporary macro file: {temp_macro.name}")
            return temp_macro.name
            
        except Exception as e:
            self.logger.error(f"Error creating macro with parameters: {e}")
            return None
    
    def _run_imagej_macro(self, imagej_path: str, macro_file: str, auto_close: bool) -> bool:
        """
        Run ImageJ with the dedicated macro using -macro mode.
        
        Args:
            imagej_path: Path to the ImageJ executable
            macro_file: Path to the dedicated ImageJ macro file
            auto_close: Whether the macro will automatically close ImageJ
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Use -macro instead of --headless --run to avoid ROI Manager headless issues
            cmd = [imagej_path, '-macro', str(macro_file)]
            
            self.logger.info(f"Running ImageJ command: {' '.join(cmd)}")
            self.logger.info(f"ImageJ will {'auto-close' if auto_close else 'remain open'} after execution")
            
            # Use the subprocess port for execution
            result = self.subprocess_port.run_with_progress(
                cmd,
                title="ImageJ: Resize ROIs",
                capture_output=True,
                text=True
            )
            
            # Check if the command executed successfully
            if result != 0:
                self.logger.error(f"ImageJ returned non-zero exit code: {result}")
                return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error running ImageJ: {e}")
            return False
    
    def _cleanup_temp_macro(self, temp_macro_file: str) -> None:
        """Clean up temporary macro file."""
        try:
            os.unlink(temp_macro_file)
            self.logger.debug(f"Cleaned up temporary macro file: {temp_macro_file}")
        except Exception as e:
            self.logger.warning(f"Could not clean up temporary macro file {temp_macro_file}: {e}")
