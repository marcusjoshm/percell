"""
ImageJ adapter implementing ImageProcessingService.

This adapter provides concrete implementations for ImageJ/Fiji macro execution
using the subprocess module.
"""

import subprocess
import os
from typing import Dict, Optional
from pathlib import Path

from percell.domain.ports import ImageProcessingService
from percell.domain.exceptions import ImageProcessingError


class ImageJAdapter(ImageProcessingService):
    """Concrete implementation of ImageProcessingService using ImageJ/Fiji."""
    
    def __init__(self, imagej_path: str):
        """
        Initialize the ImageJ adapter.
        
        Args:
            imagej_path: Path to the ImageJ/Fiji executable
        """
        self.imagej_path = Path(imagej_path) if imagej_path else None
        
        # For testing purposes, allow empty paths
        if imagej_path and imagej_path.strip():
            if not self.imagej_path.exists():
                raise ImageProcessingError(f"ImageJ path does not exist: {imagej_path}")
            if not self.imagej_path.is_file():
                raise ImageProcessingError(f"ImageJ path is not a file: {imagej_path}")
    
    def run_macro(
        self, 
        macro_path: str, 
        params: Optional[Dict[str, str]] = None, 
        *, 
        headless: bool = False
    ) -> int:
        """
        Run an ImageJ/Fiji macro and return the process return code.
        
        Args:
            macro_path: Path to the macro file
            params: Optional parameters to pass to the macro
            headless: Whether to run in headless mode
            
        Returns:
            Process return code (0 for success, non-zero for failure)
            
        Raises:
            ImageProcessingError: If macro execution fails
        """
        try:
            # Check if ImageJ path is configured
            if not self.imagej_path:
                raise ImageProcessingError("ImageJ path not configured")
            
            # Validate macro path
            macro_path_obj = Path(macro_path)
            if not macro_path_obj.exists():
                raise ImageProcessingError(f"Macro file does not exist: {macro_path}")
            
            # Build command
            command = [str(self.imagej_path)]
            
            # Add headless mode if specified
            if headless:
                command.append("--headless")
            
            # Add macro path
            command.append(macro_path)
            
            # Add parameters if provided
            if params:
                for key, value in params.items():
                    command.extend([key, value])
            
            # Run the command
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                check=False
            )
            
            # Check for errors
            if result.returncode != 0:
                error_msg = f"ImageJ macro failed with return code {result.returncode}"
                if result.stderr:
                    error_msg += f"\nStderr: {result.stderr}"
                if result.stdout:
                    error_msg += f"\nStdout: {result.stdout}"
                raise ImageProcessingError(error_msg)
            
            return result.returncode
            
        except subprocess.SubprocessError as e:
            raise ImageProcessingError(f"Failed to execute ImageJ macro: {str(e)}") from e
        except Exception as e:
            raise ImageProcessingError(f"Unexpected error running ImageJ macro: {str(e)}") from e
