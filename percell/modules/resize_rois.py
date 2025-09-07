#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Resize ROIs Script for Single Cell Analysis Workflow

This script takes ROIs from the preprocessed directory, uses ImageJ to resize them 
to match the original images, and saves them to the ROI directory.

This version uses a dedicated macro file with parameter passing instead of 
creating permanent temporary macro files.
"""

import os
import sys
import argparse
import logging
import tempfile
from pathlib import Path
from percell.adapters.local_filesystem_adapter import LocalFileSystemAdapter
from percell.adapters.imagej_macro_adapter import ImageJMacroAdapter

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("ROIResizer")
fs = LocalFileSystemAdapter()

def create_macro_with_parameters(macro_template_file, input_dir, output_dir, channel, auto_close=False):
    """
    Create a temporary macro file with parameters embedded from the dedicated macro template.
    
    Args:
        macro_template_file (str): Path to the dedicated macro template file
        input_dir (str): Input directory containing binned images and ROIs
        output_dir (str): Output directory for resized ROIs
        channel (str): Segmentation channel to process (e.g., ch00)
        auto_close (bool): Whether to add auto-close functionality
        
    Returns:
        str: Path to the created temporary macro file
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
        input_dir = str(input_dir).replace('\\', '/')
        output_dir = str(output_dir).replace('\\', '/')
        
        # Add parameter definitions at the beginning
        parameter_definitions = f"""
// Parameters embedded from Python script
input_dir = "{input_dir}";
output_dir = "{output_dir}";
channel = "{channel}";
auto_close = {str(auto_close).lower()};
"""
        
        # Combine parameters with the filtered template content
        macro_content = parameter_definitions + '\n'.join(filtered_lines)
        
        # Create temporary macro file
        temp_macro = tempfile.NamedTemporaryFile(mode='w', suffix='.ijm', delete=False)
        temp_macro.write(macro_content)
        temp_macro.close()
        
        logger.info(f"Created temporary macro file: {temp_macro.name}")
        return temp_macro.name
        
    except Exception as e:
        logger.error(f"Error creating macro with parameters: {e}")
        return None

def run_imagej_macro(imagej_path, macro_file, auto_close=False):
    """
    Run ImageJ with the dedicated macro using -macro mode.
    
    Args:
        imagej_path (str): Path to the ImageJ executable
        macro_file (str): Path to the dedicated ImageJ macro file
        auto_close (bool): Whether the macro will automatically close ImageJ
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        adapter = ImageJMacroAdapter(Path(imagej_path))
        logger.info(f"Running ImageJ macro via adapter: {macro_file}")
        rc = adapter.run_macro(Path(macro_file), [])
        if rc != 0:
            logger.error(f"ImageJ returned non-zero exit code: {rc}")
            return False
        return True
    except Exception as e:
        logger.error(f"Error running ImageJ: {e}")
        return False

def validate_inputs(input_dir, output_dir, channel):
    """
    Validate input parameters.
    
    Args:
        input_dir (str): Input directory path
        output_dir (str): Output directory path  
        channel (str): Channel specification
        
    Returns:
        bool: True if all inputs are valid, False otherwise
    """
    # Check input directory exists
    if not os.path.exists(input_dir):
        logger.error(f"Input directory does not exist: {input_dir}")
        return False
    
    # Check input directory has content
    if not os.listdir(input_dir):
        logger.error(f"Input directory is empty: {input_dir}")
        return False
    
    # Validate channel format
    if not channel.startswith('ch'):
        logger.error(f"Channel should start with 'ch' (e.g., 'ch00'): {channel}")
        return False
    
    # Create output directory if it doesn't exist
    try:
        fs.ensure_dir(Path(output_dir))
        logger.info(f"Output directory ready: {output_dir}")
    except Exception as e:
        logger.error(f"Cannot create output directory {output_dir}: {e}")
        return False
    
    return True

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
            if '#@ String channel' not in content:
                logger.warning(f"Macro file may not be compatible - missing channel parameter")
        
        logger.info(f"Macro file validated: {macro_file}")
        return True
        
    except Exception as e:
        logger.error(f"Cannot read macro file {macro_file}: {e}")
        return False

def main():
    """Main function to resize ROIs."""
    parser = argparse.ArgumentParser(description='Resize ROIs from binned images using dedicated macro')
    
    parser.add_argument('--input', '-i', required=True,
                        help='Input directory containing preprocessed images and ROIs')
    parser.add_argument('--output', '-o', required=True,
                        help='Output directory for resized ROIs')
    parser.add_argument('--imagej', required=True,
                        help='Path to ImageJ executable')
    parser.add_argument('--channel', required=True,
                        help='Segmentation channel to process ROIs for (e.g., ch00)')
    parser.add_argument('--macro', default='percell/macros/resize_rois.ijm',
                        help='Path to the dedicated ImageJ macro file (default: percell/macros/resize_rois.ijm)')
    parser.add_argument('--auto-close', action='store_true',
                        help='Close ImageJ when the macro completes')
    parser.add_argument('--verbose', '-v', action='store_true',
                        help='Enable verbose logging')
    
    args = parser.parse_args()
    
    # Set logging level
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
        logger.debug("Verbose logging enabled")
    
    # Validate inputs
    if not validate_inputs(args.input, args.output, args.channel):
        logger.error("Input validation failed")
        return 1
    
    # Check macro file
    if not check_macro_file(args.macro):
        logger.error("Macro file validation failed")
        return 1
    
    # Create temporary macro with embedded parameters
    logger.info("Creating macro with embedded parameters...")
    temp_macro_file = create_macro_with_parameters(
        args.macro,
        args.input,
        args.output, 
        args.channel,
        args.auto_close
    )
    
    if not temp_macro_file:
        logger.error("Failed to create macro with parameters")
        return 1
    
    try:
        # Run the ImageJ macro
        logger.info("Starting ROI resizing process...")
        success = run_imagej_macro(args.imagej, temp_macro_file, args.auto_close)
        
        if success:
            logger.info("ROI resizing completed successfully")
            return 0
        else:
            logger.error("ROI resizing failed")
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