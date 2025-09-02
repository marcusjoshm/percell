#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Directory Management Service for Single Cell Analysis Workflow

This service handles interactive setup and management of input and output directories
with recent path memory functionality and configuration persistence.
"""

import os
import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from percell.domain.ports import FileSystemPort, LoggingPort, ConfigurationPort


class DirectoryManagementService:
    """
    Service for managing input and output directories with configuration persistence.
    
    This service combines the functionality of both directory_setup.py and set_directories.py,
    providing a unified interface for directory management.
    """
    
    def __init__(
        self,
        filesystem_port: FileSystemPort,
        logging_port: LoggingPort,
        configuration_port: ConfigurationPort
    ):
        """
        Initialize the Directory Management Service.
        
        Args:
            filesystem_port: Port for file system operations
            logging_port: Port for logging operations
            configuration_port: Port for configuration operations
        """
        self.filesystem_port = filesystem_port
        self.logging_port = logging_port
        self.configuration_port = configuration_port
        self.logger = self.logging_port.get_logger("DirectoryManagementService")
    
    def validate_directory_path(self, path: str, create_if_missing: bool = False) -> bool:
        """
        Validate if a directory path exists and is accessible.
        
        Args:
            path: Directory path to validate
            create_if_missing: Whether to create directory if it doesn't exist
            
        Returns:
            True if path is valid, False otherwise
        """
        try:
            if not path:
                return False
            
            if self.filesystem_port.path_exists(path):
                return self.filesystem_port.is_directory(path)
            elif create_if_missing:
                self.filesystem_port.create_directories(path)
                return True
            else:
                return False
                
        except Exception as e:
            self.logger.error(f"Error validating directory path {path}: {e}")
            return False
    
    def get_recent_directories(self, directory_type: str) -> List[str]:
        """
        Get recent directories from configuration.
        
        Args:
            directory_type: Either 'input' or 'output'
            
        Returns:
            List of recent directory paths
        """
        try:
            config = self.configuration_port.get_configuration()
            
            if 'directories' not in config:
                return []
            
            recent_key = f"recent_{directory_type}s"
            return config['directories'].get(recent_key, [])
            
        except Exception as e:
            self.logger.error(f"Error getting recent directories: {e}")
            return []
    
    def add_recent_directory(self, directory_type: str, path: str, max_recent: int = 5) -> None:
        """
        Add a directory to recent directories list.
        
        Args:
            directory_type: Either 'input' or 'output'
            path: Directory path to add
            max_recent: Maximum number of recent directories to keep
        """
        try:
            config = self.configuration_port.get_configuration()
            
            if 'directories' not in config:
                config['directories'] = {}
            
            recent_key = f"recent_{directory_type}s"
            if recent_key not in config['directories']:
                config['directories'][recent_key] = []
            
            # Remove if already exists
            if path in config['directories'][recent_key]:
                config['directories'][recent_key].remove(path)
            
            # Add to beginning
            config['directories'][recent_key].insert(0, path)
            
            # Keep only the most recent ones
            config['directories'][recent_key] = config['directories'][recent_key][:max_recent]
            
            # Update configuration
            self.configuration_port.update_configuration(config)
            
        except Exception as e:
            self.logger.error(f"Error adding recent directory: {e}")
    
    def get_default_directories(self) -> Tuple[str, str]:
        """
        Get default directories from configuration.
        
        Returns:
            Tuple of (input_path, output_path)
        """
        try:
            config = self.configuration_port.get_configuration()
            
            if 'directories' not in config:
                return "", ""
            
            input_path = config['directories'].get('input', '')
            output_path = config['directories'].get('output', '')
            
            return input_path, output_path
            
        except Exception as e:
            self.logger.error(f"Error getting default directories: {e}")
            return "", ""
    
    def check_default_directories(self) -> Dict[str, Any]:
        """
        Check if default directories are set and valid.
        
        Returns:
            Dictionary with validation results
        """
        try:
            input_path, output_path = self.get_default_directories()
            
            if not input_path or not output_path:
                return {
                    'valid': False,
                    'input_path': input_path,
                    'output_path': output_path,
                    'message': 'Default directories not set'
                }
            
            # Validate paths
            input_valid = self.validate_directory_path(input_path, create_if_missing=False)
            output_valid = self.validate_directory_path(output_path, create_if_missing=True)
            
            if input_valid and output_valid:
                return {
                    'valid': True,
                    'input_path': input_path,
                    'output_path': output_path,
                    'message': 'Default directories are valid'
                }
            else:
                return {
                    'valid': False,
                    'input_path': input_path,
                    'output_path': output_path,
                    'input_valid': input_valid,
                    'output_valid': output_valid,
                    'message': 'One or more default directories are invalid'
                }
                
        except Exception as e:
            return {
                'valid': False,
                'error': f'Error checking default directories: {e}'
            }
    
    def set_default_directories(self, input_path: str, output_path: str) -> Dict[str, Any]:
        """
        Set default input and output directories.
        
        Args:
            input_path: Input directory path
            output_path: Output directory path
            
        Returns:
            Dictionary with operation results
        """
        try:
            # Validate paths
            input_valid = self.validate_directory_path(input_path, create_if_missing=False)
            output_valid = self.validate_directory_path(output_path, create_if_missing=True)
            
            if not input_valid:
                return {
                    'success': False,
                    'error': f'Input directory "{input_path}" does not exist or is not accessible'
                }
            
            if not output_valid:
                return {
                    'success': False,
                    'error': f'Cannot create or access output directory "{output_path}"'
                }
            
            # Update configuration
            config = self.configuration_port.get_configuration()
            
            if 'directories' not in config:
                config['directories'] = {}
            
            config['directories']['input'] = input_path
            config['directories']['output'] = output_path
            
            # Add to recent directories
            self.add_recent_directory('input', input_path)
            self.add_recent_directory('output', output_path)
            
            # Update configuration
            self.configuration_port.update_configuration(config)
            
            self.logger.info(f"Default directories set successfully: input={input_path}, output={output_path}")
            
            return {
                'success': True,
                'input_path': input_path,
                'output_path': output_path,
                'message': 'Default directories set successfully'
            }
            
        except Exception as e:
            error_msg = f'Error setting default directories: {e}'
            self.logger.error(error_msg)
            return {
                'success': False,
                'error': error_msg
            }
    
    def get_paths_interactively(
        self,
        args_input: Optional[str] = None,
        args_output: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get input and output paths interactively if not provided.
        
        Args:
            args_input: Input path from command line args
            args_output: Output path from command line args
            
        Returns:
            Dictionary with operation results
        """
        try:
            # Get recent directories
            recent_inputs = self.get_recent_directories('input')
            recent_outputs = self.get_recent_directories('output')
            
            # Get default paths from config
            default_input, default_output = self.get_default_directories()
            
            # Get input path
            if not args_input:
                input_path = self._prompt_for_directory('input', recent_inputs, default_input)
                if not input_path:
                    return {
                        'success': False,
                        'error': 'No input directory specified'
                    }
            else:
                input_path = args_input
                if not self.validate_directory_path(input_path, create_if_missing=False):
                    self.logger.warning(f"Input directory '{input_path}' does not exist or is not accessible")
                    input_path = self._prompt_for_directory('input', recent_inputs, default_input)
                    if not input_path:
                        return {
                            'success': False,
                            'error': 'No valid input directory specified'
                        }
            
            # Get output path
            if not args_output:
                output_path = self._prompt_for_directory('output', recent_outputs, default_output)
                if not output_path:
                    return {
                        'success': False,
                        'error': 'No output directory specified'
                    }
            else:
                output_path = args_output
                if not self.validate_directory_path(output_path, create_if_missing=True):
                    self.logger.warning(f"Cannot create or access output directory '{output_path}'")
                    output_path = self._prompt_for_directory('output', recent_outputs, default_output)
                    if not output_path:
                        return {
                            'success': False,
                            'error': 'No valid output directory specified'
                        }
            
            # Add to recent directories
            self.add_recent_directory('input', input_path)
            self.add_recent_directory('output', output_path)
            
            return {
                'success': True,
                'input_path': input_path,
                'output_path': output_path,
                'message': 'Paths retrieved successfully'
            }
            
        except Exception as e:
            error_msg = f'Error getting paths interactively: {e}'
            self.logger.error(error_msg)
            return {
                'success': False,
                'error': error_msg
            }
    
    def _prompt_for_directory(self, directory_type: str, recent_dirs: List[str], default_path: str = "") -> Optional[str]:
        """
        Prompt user for directory path with recent options.
        
        Args:
            directory_type: Type of directory ('input' or 'output')
            recent_dirs: List of recent directories
            default_path: Default path if provided
            
        Returns:
            Selected directory path, or None if cancelled
        """
        try:
            # In a service context, this would typically return the default
            # or be handled by the CLI layer for interactive input
            if default_path and self.validate_directory_path(default_path, create_if_missing=(directory_type == 'output')):
                return default_path
            
            # Return first recent directory if available and valid
            for recent_dir in recent_dirs:
                if self.validate_directory_path(recent_dir, create_if_missing=(directory_type == 'output')):
                    return recent_dir
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error prompting for directory: {e}")
            return None
    
    def save_recent_directories_automatically(self, input_path: str, output_path: str) -> Dict[str, Any]:
        """
        Automatically save the most recently used directories as defaults.
        
        Args:
            input_path: Input directory path
            output_path: Output directory path
            
        Returns:
            Dictionary with operation results
        """
        try:
            # Validate paths first
            input_valid = self.validate_directory_path(input_path, create_if_missing=False)
            output_valid = self.validate_directory_path(output_path, create_if_missing=True)
            
            if not input_valid or not output_valid:
                return {
                    'success': False,
                    'error': 'One or more directories are invalid'
                }
            
            # Set as defaults
            result = self.set_default_directories(input_path, output_path)
            
            if result['success']:
                self.logger.info(f"Automatically saved directories as defaults: input={input_path}, output={output_path}")
                return {
                    'success': True,
                    'input_path': input_path,
                    'output_path': output_path,
                    'message': 'Directories automatically saved as defaults'
                }
            else:
                return result
                
        except Exception as e:
            error_msg = f'Error saving directory defaults: {e}'
            self.logger.error(error_msg)
            return {
                'success': False,
                'error': error_msg
            }
    
    def list_recent_directories(self) -> Dict[str, Any]:
        """
        List all recent directories from configuration.
        
        Returns:
            Dictionary with recent directories
        """
        try:
            recent_inputs = self.get_recent_directories('input')
            recent_outputs = self.get_recent_directories('output')
            default_input, default_output = self.get_default_directories()
            
            return {
                'success': True,
                'recent_inputs': recent_inputs,
                'recent_outputs': recent_outputs,
                'default_input': default_input,
                'default_output': default_output,
                'message': 'Recent directories retrieved successfully'
            }
            
        except Exception as e:
            error_msg = f'Error listing recent directories: {e}'
            self.logger.error(error_msg)
            return {
                'success': False,
                'error': error_msg
            }
    
    def clear_recent_directories(self, directory_type: Optional[str] = None) -> Dict[str, Any]:
        """
        Clear recent directories.
        
        Args:
            directory_type: Type of directory to clear ('input', 'output', or None for both)
            
        Returns:
            Dictionary with operation results
        """
        try:
            config = self.configuration_port.get_configuration()
            
            if 'directories' not in config:
                return {
                    'success': True,
                    'message': 'No directories to clear'
                }
            
            if directory_type is None:
                # Clear both
                if 'recent_inputs' in config['directories']:
                    del config['directories']['recent_inputs']
                if 'recent_outputs' in config['directories']:
                    del config['directories']['recent_outputs']
                message = 'All recent directories cleared'
            else:
                # Clear specific type
                recent_key = f"recent_{directory_type}s"
                if recent_key in config['directories']:
                    del config['directories'][recent_key]
                message = f'Recent {directory_type} directories cleared'
            
            # Update configuration
            self.configuration_port.update_configuration(config)
            
            self.logger.info(message)
            return {
                'success': True,
                'message': message
            }
            
        except Exception as e:
            error_msg = f'Error clearing recent directories: {e}'
            self.logger.error(error_msg)
            return {
                'success': False,
                'error': error_msg
            }
    
    def validate_workflow_directories(self, input_path: str, output_path: str) -> Dict[str, Any]:
        """
        Validate directories for workflow execution.
        
        Args:
            input_path: Input directory path
            output_path: Output directory path
            
        Returns:
            Dictionary with validation results
        """
        try:
            # Check input directory
            input_valid = self.validate_directory_path(input_path, create_if_missing=False)
            if not input_valid:
                return {
                    'valid': False,
                    'error': f'Input directory "{input_path}" does not exist or is not accessible'
                }
            
            # Check output directory
            output_valid = self.validate_directory_path(output_path, create_if_missing=True)
            if not output_valid:
                return {
                    'valid': False,
                    'error': f'Cannot create or access output directory "{output_path}"'
                }
            
            # Check if output directory is writable
            try:
                test_file = os.path.join(output_path, '.test_write')
                self.filesystem_port.write_file(test_file, 'test')
                self.filesystem_port.delete_file(test_file)
            except Exception as e:
                return {
                    'valid': False,
                    'error': f'Output directory "{output_path}" is not writable: {e}'
                }
            
            return {
                'valid': True,
                'input_path': input_path,
                'output_path': output_path,
                'message': 'Workflow directories validated successfully'
            }
            
        except Exception as e:
            error_msg = f'Error validating workflow directories: {e}'
            self.logger.error(error_msg)
            return {
                'valid': False,
                'error': error_msg
            }
