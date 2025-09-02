"""
Configuration adapter for the Percell infrastructure layer.

This module provides a concrete implementation of the ConfigurationPort
using the infrastructure configuration utilities.
"""

from __future__ import annotations

from typing import Any, Dict
from pathlib import Path

from percell.domain.ports import ConfigurationPort
from percell.infrastructure.configuration.config import Config, create_default_config


class ConfigurationAdapter(ConfigurationPort):
    """
    Configuration adapter implementing the ConfigurationPort interface.
    
    Provides configuration management functionality using the infrastructure
    configuration utilities.
    """
    
    def __init__(self, config_path: str):
        """
        Initialize the configuration adapter.
        
        Args:
            config_path: Path to the configuration file
        """
        self.config_path = config_path
        self._config: Config | None = None
    
    def get_config(self) -> Any:
        """
        Get the current configuration.
        
        Returns:
            The current configuration object
        """
        if self._config is None:
            self._config = Config(self.config_path)
        return self._config
    
    def create_default_config(self) -> Any:
        """
        Create a default configuration.
        
        Returns:
            A default configuration object
        """
        return create_default_config(self.config_path)
    
    def validate_software_paths(self, config: Any) -> bool:
        """
        Validate software paths in configuration.
        
        Args:
            config: Configuration object to validate
            
        Returns:
            True if all software paths are valid, False otherwise
        """
        if not isinstance(config, Config):
            return False
        
        # Check for required software paths
        required_paths = ['imagej_path', 'cellpose_path']
        
        for path_key in required_paths:
            path_value = config.get(path_key)
            if not path_value:
                continue
            
            path = Path(path_value)
            if not path.exists():
                return False
            if not path.is_file() and not path.is_dir():
                return False
        
        return True
    
    def detect_software_paths(self) -> Dict[str, str]:
        """
        Detect available software paths.
        
        Returns:
            Dictionary mapping software names to detected paths
        """
        detected_paths = {}
        
        # Common ImageJ/Fiji locations
        common_imagej_paths = [
            "/Applications/Fiji.app/Contents/MacOS/ImageJ-macosx",
            "/Applications/ImageJ.app/Contents/MacOS/ImageJ-macosx",
            "/usr/local/bin/imagej",
            "/opt/fiji/Fiji.app/ImageJ-linux64",
            "C:\\Program Files\\Fiji.app\\ImageJ-win64.exe",
            "C:\\Program Files\\ImageJ\\ImageJ.exe"
        ]
        
        for path in common_imagej_paths:
            if Path(path).exists():
                detected_paths['imagej_path'] = path
                break
        
        # Common Cellpose locations
        common_cellpose_paths = [
            "/usr/local/bin/cellpose",
            "/opt/cellpose/bin/cellpose",
            "C:\\Program Files\\Cellpose\\cellpose.exe"
        ]
        
        for path in common_cellpose_paths:
            if Path(path).exists():
                detected_paths['cellpose_path'] = path
                break
        
        return detected_paths
