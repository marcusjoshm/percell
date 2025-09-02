#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Interactive Thresholding Service for Single Cell Analysis Workflow

This service provides interactive thresholding of grouped cell images using ImageJ
with Otsu thresholding, allowing users to draw ROIs and make decisions about
thresholding parameters.
"""

import os
import tempfile
import logging
from pathlib import Path
from typing import List, Tuple, Optional, Dict, Any
from percell.domain.ports import FileSystemPort, LoggingPort, SubprocessPort


class InteractiveThresholdingService:
    """
    Service for interactive thresholding of grouped cell images using ImageJ.
    
    This service orchestrates the interactive thresholding process by:
    1. Creating temporary ImageJ macros with embedded parameters
    2. Running ImageJ in interactive mode for user ROI selection
    3. Handling user decisions about thresholding and bin adjustments
    4. Managing the creation of binary mask outputs
    """
    
    def __init__(
        self,
        filesystem_port: FileSystemPort,
        logging_port: LoggingPort,
        subprocess_port: SubprocessPort
    ):
        """
        Initialize the Interactive Thresholding Service.
        
        Args:
            filesystem_port: Port for file system operations
            logging_port: Port for logging operations
            subprocess_port: Port for subprocess operations
        """
        self.filesystem_port = filesystem_port
        self.logging_port = logging_port
        self.subprocess_port = subprocess_port
        self.logger = self.logging_port.get_logger("InteractiveThresholdingService")
    
    def create_channel_filter_logic(self, channels: List[str]) -> str:
        """
        Create the channel filtering logic for the ImageJ macro.
        
        Args:
            channels: List of channels to process (e.g., ['ch00', 'ch02'])
            
        Returns:
            ImageJ macro code for channel filtering
        """
        if not channels:
            return ""  # No filtering, process all channels
        
        # Create channel filter conditions
        channel_conditions = []
        for channel in channels:
            channel_conditions.append(f'indexOf(regionName, "{channel}") >= 0')
        
        channel_filter_code = f"""
        // Check if this region directory matches any of the specified channels
        channelMatch = false;
        if ({' || '.join(channel_conditions)}) {{
            channelMatch = true;
        }}
        if (!channelMatch) {{
            continue; // Skip this directory if it doesn't match specified channels
        }}
        """
        
        return channel_filter_code
    
    def create_macro_with_parameters(
        self,
        macro_template_file: str,
        input_dir: str,
        output_dir: str,
        channels: Optional[List[str]] = None,
        auto_close: bool = False
    ) -> Tuple[Optional[str], Optional[str]]:
        """
        Create a temporary macro file with parameters embedded from the dedicated macro template.
        
        Args:
            macro_template_file: Path to the dedicated macro template file
            input_dir: Directory containing grouped cell images
            output_dir: Directory to save thresholded mask images
            channels: List of channels to process
            auto_close: Whether to add auto-close functionality
            
        Returns:
            Tuple of (temp_macro_file_path, flag_file_path) or (None, None) on failure
        """
        try:
            # Read the dedicated macro template
            template_content = self.filesystem_port.read_file(macro_template_file)
            
            # Remove the #@ parameter declarations since we're embedding the values
            lines = template_content.split('\n')
            filtered_lines = []
            for line in lines:
                if not line.strip().startswith('#@'):
                    filtered_lines.append(line)
            
            # Ensure paths use forward slashes for ImageJ and remove trailing slashes
            input_dir_path = str(input_dir).replace('\\', '/').rstrip('/')
            output_dir_path = str(output_dir).replace('\\', '/').rstrip('/')
            
            # Define the flag file path
            flag_file_path = Path(output_dir) / "NEED_MORE_BINS.flag"
            flag_file_path_str = str(flag_file_path).replace('\\', '/')
            
            # Create channel filtering logic
            channel_filter_logic = self.create_channel_filter_logic(channels)
            
            # Add parameter definitions at the beginning
            parameter_definitions = f"""
// Parameters embedded from Python script
input_dir = "{input_dir_path}";
output_dir = "{output_dir_path}";
flag_file = "{flag_file_path_str}";
auto_close = {str(auto_close).lower()};
"""
            
            # Combine parameters with the filtered template content
            macro_content = parameter_definitions + '\n'.join(filtered_lines)
            
            # Replace the channel filter placeholder with the actual logic
            macro_content = macro_content.replace(
                '        // CHANNEL_FILTER_PLACEHOLDER',
                channel_filter_logic
            )
            
            # Create temporary macro file
            temp_macro = tempfile.NamedTemporaryFile(mode='w', suffix='.ijm', delete=False)
            temp_macro.write(macro_content)
            temp_macro.close()
            
            self.logger.info(f"Created temporary macro file: {temp_macro.name}")
            return temp_macro.name, str(flag_file_path)
            
        except Exception as e:
            self.logger.error(f"Error creating macro with parameters: {e}")
            return None, None
    
    def run_imagej_macro(
        self,
        imagej_path: str,
        macro_file: str,
        flag_file: str,
        auto_close: bool = False
    ) -> Tuple[bool, bool]:
        """
        Run ImageJ with the dedicated macro using -macro mode.
        
        Args:
            imagej_path: Path to the ImageJ executable
            macro_file: Path to the dedicated ImageJ macro file
            flag_file: Path to the flag file that indicates need for more bins
            auto_close: Whether the macro will automatically close ImageJ
            
        Returns:
            Tuple of (success, needs_more_bins)
        """
        try:
            # Use -macro mode for user interaction
            cmd = [imagej_path, '-macro', str(macro_file)]
            
            self.logger.info(f"Running ImageJ command: {' '.join(cmd)}")
            self.logger.info(
                f"ImageJ will {'auto-close' if auto_close else 'remain open'} after execution"
            )
            
            result = self.subprocess_port.run_subprocess(
                cmd,
                capture_output=True,
                text=True,
                check=False  # Don't raise an exception on non-zero return code
            )
            
            # Log the output
            if result.stdout:
                self.logger.info("ImageJ output:")
                for line in result.stdout.splitlines():
                    self.logger.info(f"  {line}")
            
            if result.stderr:
                self.logger.warning("ImageJ errors:")
                for line in result.stderr.splitlines():
                    self.logger.warning(f"  {line}")
            
            # Check for the flag file
            needs_more_bins = self.filesystem_port.path_exists(flag_file)
            if needs_more_bins:
                self.logger.info(f"Flag file detected: {flag_file}")
                self.logger.info("User has requested more bins for better cell grouping")
                # Remove the flag file to avoid confusion on subsequent runs
                try:
                    self.filesystem_port.remove_file(flag_file)
                    self.logger.info("Removed flag file after detection")
                except Exception as e:
                    self.logger.warning(f"Could not remove flag file: {e}")
            
            # Check if the command executed successfully
            if result.returncode != 0:
                self.logger.error(f"ImageJ returned non-zero exit code: {result.returncode}")
                return False, needs_more_bins
            
            return True, needs_more_bins
            
        except Exception as e:
            self.logger.error(f"Error running ImageJ: {e}")
            return False, False
    
    def check_macro_file(self, macro_file: str) -> bool:
        """
        Check if the dedicated macro file exists and is readable.
        
        Args:
            macro_file: Path to the macro file
            
        Returns:
            True if macro file is accessible, False otherwise
        """
        macro_path = Path(macro_file)
        
        if not self.filesystem_port.path_exists(macro_file):
            self.logger.error(f"Macro file does not exist: {macro_file}")
            return False
        
        if not self.filesystem_port.is_file(macro_file):
            self.logger.error(f"Macro path is not a file: {macro_file}")
            return False
        
        try:
            content = self.filesystem_port.read_file(macro_file)
            # Check if it contains the expected parameter declarations
            if '#@ String input_dir' not in content:
                self.logger.warning(
                    "Macro file may not be compatible - missing input_dir parameter"
                )
            if '#@ String output_dir' not in content:
                self.logger.warning(
                    "Macro file may not be compatible - missing output_dir parameter"
                )
            if '#@ String flag_file' not in content:
                self.logger.warning(
                    "Macro file may not be compatible - missing flag_file parameter"
                )
            
            self.logger.info(f"Macro file validated: {macro_file}")
            return True
            
        except Exception as e:
            self.logger.error(f"Cannot read macro file {macro_file}: {e}")
            return False
    
    def process_grouped_cells(
        self,
        input_dir: str,
        output_dir: str,
        imagej_path: str,
        macro_file: str = 'percell/macros/threshold_grouped_cells.ijm',
        auto_close: bool = False,
        channels: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Main method to threshold grouped cell images using ImageJ with dedicated macro.
        
        Args:
            input_dir: Directory containing grouped cell images
            output_dir: Directory to save thresholded mask images
            imagej_path: Path to ImageJ executable
            macro_file: Path to the dedicated ImageJ macro file
            auto_close: Whether to close ImageJ when the macro completes
            channels: List of channels to process
            
        Returns:
            Dictionary with results including success status and needs_more_bins flag
        """
        # Parse channels argument
        if channels:
            # Handle both space-separated and single string formats
            if len(channels) == 1 and ' ' in channels[0]:
                channels = channels[0].split()
            self.logger.info(f"Processing channels: {channels}")
        else:
            self.logger.info("No channels specified, processing all channels")
        
        # Create output directory if it doesn't exist
        self.filesystem_port.create_directories(output_dir)
        
        # Check macro file
        if not self.check_macro_file(macro_file):
            self.logger.error("Macro file validation failed")
            return {
                'success': False,
                'needs_more_bins': False,
                'error': 'Macro file validation failed'
            }
        
        # Create temporary macro with embedded parameters
        self.logger.info("Creating macro with embedded parameters...")
        temp_macro_file, flag_file = self.create_macro_with_parameters(
            macro_file,
            input_dir,
            output_dir,
            channels,
            auto_close
        )
        
        if not temp_macro_file:
            self.logger.error("Failed to create macro with parameters")
            return {
                'success': False,
                'needs_more_bins': False,
                'error': 'Failed to create macro with parameters'
            }
        
        try:
            # Run the ImageJ macro
            self.logger.info("Starting thresholding process...")
            success, needs_more_bins = self.run_imagej_macro(
                imagej_path, temp_macro_file, flag_file, auto_close
            )
            
            if success:
                self.logger.info("Thresholding of grouped cells completed successfully")
                
                # If the user requested more bins, signal this to the workflow
                if needs_more_bins:
                    self.logger.info("User requested more bins for better cell grouping")
                
                return {
                    'success': True,
                    'needs_more_bins': needs_more_bins,
                    'message': 'Thresholding completed successfully'
                }
            else:
                self.logger.error("Thresholding of grouped cells failed")
                return {
                    'success': False,
                    'needs_more_bins': needs_more_bins,
                    'error': 'Thresholding process failed'
                }
        
        finally:
            # Clean up temporary macro file
            try:
                self.filesystem_port.remove_file(temp_macro_file)
                self.logger.debug(f"Cleaned up temporary macro file: {temp_macro_file}")
            except Exception as e:
                self.logger.warning(
                    f"Could not clean up temporary macro file {temp_macro_file}: {e}"
                )
    
    def get_available_channels(self, input_dir: str) -> List[str]:
        """
        Get list of available channels from the input directory structure.
        
        Args:
            input_dir: Directory containing grouped cell images
            
        Returns:
            List of available channel names
        """
        try:
            channels = set()
            
            # Walk through the directory structure to find channel names
            for root, dirs, files in self.filesystem_port.walk_directory(input_dir):
                for dir_name in dirs:
                    # Look for channel patterns like ch00, ch01, etc.
                    if dir_name.startswith('ch') and len(dir_name) >= 3:
                        channels.add(dir_name)
            
            return sorted(list(channels))
            
        except Exception as e:
            self.logger.error(f"Error getting available channels: {e}")
            return []
    
    def validate_input_structure(self, input_dir: str) -> Dict[str, Any]:
        """
        Validate the input directory structure for grouped cell images.
        
        Args:
            input_dir: Directory to validate
            
        Returns:
            Dictionary with validation results
        """
        try:
            if not self.filesystem_port.path_exists(input_dir):
                return {
                    'valid': False,
                    'error': f'Input directory does not exist: {input_dir}'
                }
            
            if not self.filesystem_port.is_directory(input_dir):
                return {
                    'valid': False,
                    'error': f'Input path is not a directory: {input_dir}'
                }
            
            # Check for expected subdirectory structure
            condition_dirs = []
            for item in self.filesystem_port.list_directory(input_dir):
                item_path = os.path.join(input_dir, item)
                if self.filesystem_port.is_directory(item_path):
                    condition_dirs.append(item)
            
            if not condition_dirs:
                return {
                    'valid': False,
                    'error': f'No condition directories found in: {input_dir}'
                }
            
            return {
                'valid': True,
                'condition_dirs': condition_dirs,
                'message': f'Found {len(condition_dirs)} condition directories'
            }
            
        except Exception as e:
            return {
                'valid': False,
                'error': f'Error validating input structure: {e}'
            }
