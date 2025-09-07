#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Threshold Grouped Cells Script for Single Cell Analysis Workflow

This script takes the grouped cell images, applies thresholding to create masks,
and saves them to the grouped masks directory.

This version uses a dedicated macro file with parameter passing instead of 
creating permanent macro files with hardcoded paths.
"""

import os
import sys
import argparse
import logging
import tempfile
import subprocess
from pathlib import Path
from percell.adapters.local_filesystem_adapter import LocalFileSystemAdapter

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("GroupedThresholder")

def create_channel_filter_logic(channels):
    """
    Create the channel filtering logic for the ImageJ macro.
    
    Args:
        channels (list): List of channels to process (e.g., ['ch00', 'ch02'])
        
    Returns:
        str: ImageJ macro code for channel filtering
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

def create_macro_with_parameters(macro_template_file, input_dir, output_dir, channels=None, auto_close=False):
    """
    Create a temporary macro file with parameters embedded from the dedicated macro template.
    
    Args:
        macro_template_file (str): Path to the dedicated macro template file
        input_dir (str): Directory containing grouped cell images
        output_dir (str): Directory to save thresholded mask images
        channels (list): List of channels to process
        auto_close (bool): Whether to add auto-close functionality
        
    Returns:
        tuple: (str, str) - (temp_macro_file_path, flag_file_path)
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
        
        # Ensure paths use forward slashes for ImageJ and remove trailing slashes
        input_dir_path = str(input_dir).replace('\\', '/').rstrip('/')
        output_dir_path = str(output_dir).replace('\\', '/').rstrip('/')
        
        # Define the flag file path
        flag_file_path = Path(output_dir) / "NEED_MORE_BINS.flag"
        flag_file_path_str = str(flag_file_path).replace('\\', '/')
        
        # Create channel filtering logic
        channel_filter_logic = create_channel_filter_logic(channels)
        
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
        macro_content = macro_content.replace('        // CHANNEL_FILTER_PLACEHOLDER', channel_filter_logic)
        
        # Create temporary macro file
        temp_macro = tempfile.NamedTemporaryFile(mode='w', suffix='.ijm', delete=False)
        temp_macro.write(macro_content)
        temp_macro.close()
        
        logger.info(f"Created temporary macro file: {temp_macro.name}")
        return temp_macro.name, str(flag_file_path)
        
    except Exception as e:
        logger.error(f"Error creating macro with parameters: {e}")
        return None, None

def run_imagej_macro(imagej_path, macro_file, flag_file, auto_close=False):
    """
    Run ImageJ with the dedicated macro using -macro mode.
    
    Args:
        imagej_path (str): Path to the ImageJ executable
        macro_file (str): Path to the dedicated ImageJ macro file
        flag_file (str): Path to the flag file that indicates need for more bins
        auto_close (bool): Whether the macro will automatically close ImageJ
        
    Returns:
        tuple: (bool, bool) - (success, needs_more_bins)
    """
    try:
        # Use -macro mode for user interaction
        cmd = [imagej_path, '-macro', str(macro_file)]
        
        logger.info(f"Running ImageJ command: {' '.join(cmd)}")
        logger.info(f"ImageJ will {'auto-close' if auto_close else 'remain open'} after execution")
        
        result = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=False  # Don't raise an exception on non-zero return code
        )
        
        # Log the output
        if result.stdout:
            logger.info("ImageJ output:")
            for line in result.stdout.splitlines():
                logger.info(f"  {line}")
        
        if result.stderr:
            logger.warning("ImageJ errors:")
            for line in result.stderr.splitlines():
                logger.warning(f"  {line}")
        
        # Check for the flag file
        needs_more_bins = os.path.exists(flag_file)
        if needs_more_bins:
            logger.info(f"Flag file detected: {flag_file}")
            logger.info("User has requested more bins for better cell grouping")
            # Remove the flag file to avoid confusion on subsequent runs
            try:
                os.remove(flag_file)
                logger.info(f"Removed flag file after detection")
            except Exception as e:
                logger.warning(f"Could not remove flag file: {e}")
        
        # Check if the command executed successfully
        if result.returncode != 0:
            logger.error(f"ImageJ returned non-zero exit code: {result.returncode}")
            return False, needs_more_bins
        
        return True, needs_more_bins
        
    except Exception as e:
        logger.error(f"Error running ImageJ: {e}")
        return False, False

def check_macro_file(macro_file):
    """
    Check if the dedicated macro file exists and is readable.
    
    Args:
        macro_file (str): Path to the macro file
        
    Returns:
        bool: True if macro file is accessible, False otherwise
    """
    macro_path = Path(macro_file)
    
    if not macro_path.exists():
        logger.error(f"Macro file does not exist: {macro_file}")
        return False
    
    if not macro_path.is_file():
        logger.error(f"Macro path is not a file: {macro_file}")
        return False
    
    try:
        with open(macro_path, 'r') as f:
            content = f.read()
            # Check if it contains the expected parameter declarations
            if '#@ String input_dir' not in content:
                logger.warning(f"Macro file may not be compatible - missing input_dir parameter")
            if '#@ String output_dir' not in content:
                logger.warning(f"Macro file may not be compatible - missing output_dir parameter")
            if '#@ String flag_file' not in content:
                logger.warning(f"Macro file may not be compatible - missing flag_file parameter")
        
        logger.info(f"Macro file validated: {macro_file}")
        return True
        
    except Exception as e:
        logger.error(f"Cannot read macro file {macro_file}: {e}")
        return False

def main():
    """Main function to threshold grouped cell images."""
    parser = argparse.ArgumentParser(description='Threshold grouped cell images using ImageJ with dedicated macro')
    
    parser.add_argument('--input-dir', '-i', required=True,
                        help='Directory containing grouped cell images')
    parser.add_argument('--output-dir', '-o', required=True,
                        help='Directory to save thresholded mask images')
    parser.add_argument('--imagej', required=True,
                        help='Path to ImageJ executable')
    parser.add_argument('--macro', default='percell/macros/threshold_grouped_cells.ijm',
                       help='Path to the dedicated ImageJ macro file (default: percell/macros/threshold_grouped_cells.ijm)')
    parser.add_argument('--auto-close', action='store_true',
                        help='Close ImageJ when the macro completes')
    parser.add_argument('--channels', nargs='+', help='Channels to process (e.g., ch00 ch02)')
    
    args = parser.parse_args()
    
    # Parse channels argument
    channels = None
    if args.channels:
        # Handle both space-separated and single string formats
        if len(args.channels) == 1 and ' ' in args.channels[0]:
            channels = args.channels[0].split()
        else:
            channels = args.channels
        logger.info(f"Processing channels: {channels}")
    else:
        logger.info("No channels specified, processing all channels")
    
    # Create output directory if it doesn't exist
    LocalFileSystemAdapter().ensure_dir(Path(args.output_dir))
    
    # Check macro file
    if not check_macro_file(args.macro):
        logger.error("Macro file validation failed")
        return 1
    
    # Create temporary macro with embedded parameters
    logger.info("Creating macro with embedded parameters...")
    temp_macro_file, flag_file = create_macro_with_parameters(
        args.macro,
        args.input_dir,
        args.output_dir,
        channels,
        args.auto_close
    )
    
    if not temp_macro_file:
        logger.error("Failed to create macro with parameters")
        return 1
    
    try:
        # Run the ImageJ macro
        logger.info("Starting thresholding process...")
        success, needs_more_bins = run_imagej_macro(args.imagej, temp_macro_file, flag_file, args.auto_close)
        
        if success:
            logger.info("Thresholding of grouped cells completed successfully")
            
            # If the user requested more bins, signal this to the workflow
            if needs_more_bins:
                logger.info("User requested more bins for better cell grouping")
                # Exit with a special code (5) to signal the workflow that more bins are needed
                return 5
            
            return 0
        else:
            logger.error("Thresholding of grouped cells failed")
            return 1
    
    finally:
        # Clean up temporary macro file
        try:
            os.unlink(temp_macro_file)
            logger.debug(f"Cleaned up temporary macro file: {temp_macro_file}")
        except Exception as e:
            logger.warning(f"Could not clean up temporary macro file {temp_macro_file}: {e}")

if __name__ == "__main__":
    sys.exit(main()) 