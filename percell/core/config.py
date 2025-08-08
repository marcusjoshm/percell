"""
Configuration Management for Microscopy Single-Cell Analysis Pipeline

Handles configuration loading, validation, and management for the microscopy analysis pipeline.
"""

import json
import os
from pathlib import Path
from typing import Dict, Any, Optional, List
import logging


class ConfigError(Exception):
    """Custom exception for configuration-related errors."""
    pass


class Config:
    """
    Configuration manager for microscopy analysis pipeline.
    
    Handles loading, validation, and access to configuration settings.
    """
    
    def __init__(self, config_path: str):
        """
        Initialize configuration.
        
        Args:
            config_path: Path to configuration file
        """
        self.config_path = Path(config_path)
        self.config_data = {}
        self.load()
    
    def load(self) -> None:
        """Load configuration from file."""
        try:
            if not self.config_path.exists():
                raise ConfigError(f"Configuration file not found: {self.config_path}")
            
            with open(self.config_path, 'r') as f:
                self.config_data = json.load(f)
                
        except json.JSONDecodeError as e:
            raise ConfigError(f"Invalid JSON in configuration file: {e}")
        except Exception as e:
            raise ConfigError(f"Error loading configuration: {e}")
    
    def save(self) -> None:
        """Save configuration to file."""
        try:
            with open(self.config_path, 'w') as f:
                json.dump(self.config_data, f, indent=2)
        except Exception as e:
            raise ConfigError(f"Error saving configuration: {e}")
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Get configuration value.
        
        Args:
            key: Configuration key (supports dot notation)
            default: Default value if key not found
            
        Returns:
            Configuration value
        """
        keys = key.split('.')
        value = self.config_data
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        
        return value
    
    def set(self, key: str, value: Any) -> None:
        """
        Set configuration value.
        
        Args:
            key: Configuration key (supports dot notation)
            value: Value to set
        """
        keys = key.split('.')
        current = self.config_data
        
        # Navigate to the parent of the target key
        for k in keys[:-1]:
            if k not in current:
                current[k] = {}
            current = current[k]
        
        # Set the value
        current[keys[-1]] = value
    
    def validate(self) -> bool:
        """
        Validate configuration.
        
        Returns:
            True if configuration is valid
        """
        required_keys = [
            'imagej_path',
            'cellpose_path',
            'python_path'
        ]
        
        missing_keys = []
        for key in required_keys:
            if not self.get(key):
                missing_keys.append(key)
        
        if missing_keys:
            raise ConfigError(f"Missing required configuration keys: {missing_keys}")
        
        return True
    
    def to_dict(self) -> Dict[str, Any]:
        """Get configuration as dictionary."""
        return self.config_data.copy()
    
    def update(self, updates: Dict[str, Any]) -> None:
        """
        Update configuration with new values.
        
        Args:
            updates: Dictionary of updates
        """
        for key, value in updates.items():
            self.set(key, value)
    
    def get_software_paths(self) -> Dict[str, str]:
        """
        Get software paths from configuration.
        
        Returns:
            Dictionary of software paths
        """
        return {
            'imagej': self.get('imagej_path', ''),
            'cellpose': self.get('cellpose_path', ''),
            'python': self.get('python_path', ''),
            'fiji': self.get('fiji_path', '')
        }
    
    def get_analysis_settings(self) -> Dict[str, Any]:
        """
        Get analysis settings from configuration.
        
        Returns:
            Dictionary of analysis settings
        """
        return {
            'default_bins': self.get('analysis.default_bins', 5),
            'segmentation_model': self.get('analysis.segmentation_model', 'cyto'),
            'cell_diameter': self.get('analysis.cell_diameter', 100),
            'niter_dynamics': self.get('analysis.niter_dynamics', 250),
            'flow_threshold': self.get('analysis.flow_threshold', 0.4),
            'cellprob_threshold': self.get('analysis.cellprob_threshold', 0)
        }
    
    def get_output_settings(self) -> Dict[str, Any]:
        """
        Get output settings from configuration.
        
        Returns:
            Dictionary of output settings
        """
        return {
            'create_subdirectories': self.get('output.create_subdirectories', True),
            'save_intermediate': self.get('output.save_intermediate', True),
            'compression': self.get('output.compression', 'lzw'),
            'overwrite': self.get('output.overwrite', False)
        }


def create_default_config(config_path: str) -> Config:
    """
    Create a default configuration file.
    
    Args:
        config_path: Path to save configuration file
        
    Returns:
        Config instance with default settings
    """
    default_config = {
        "imagej_path": "",
        "cellpose_path": "",
        "python_path": "",
        "fiji_path": "",
        "analysis": {
            "default_bins": 5,
            "segmentation_model": "cyto",
            "cell_diameter": 100,
            "niter_dynamics": 250,
            "flow_threshold": 0.4,
            "cellprob_threshold": 0
        },
        "output": {
            "create_subdirectories": True,
            "save_intermediate": True,
            "compression": "lzw",
            "overwrite": False
        },
        "directories": {
            "input": "",
            "output": "",
            "recent_inputs": [],
            "recent_outputs": []
        },
        "data_selection": {
            "selected_datatype": None,
            "selected_conditions": [],
            "selected_timepoints": [],
            "selected_regions": [],
            "segmentation_channel": None,
            "analysis_channels": [],
            "experiment_metadata": {
                "conditions": [],
                "regions": [],
                "timepoints": [],
                "channels": [],
                "region_to_channels": {},
                "datatype_inferred": None,
                "directory_timepoints": []
            }
        }
    }
    
    config_path = Path(config_path)
    config_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(config_path, 'w') as f:
        json.dump(default_config, f, indent=2)
    
    return Config(str(config_path))


def validate_software_paths(config: Config) -> Dict[str, bool]:
    """
    Validate software paths in configuration.
    
    Args:
        config: Configuration instance
        
    Returns:
        Dictionary mapping software names to validation results
    """
    software_paths = config.get_software_paths()
    validation_results = {}
    
    for software, path in software_paths.items():
        if not path:
            validation_results[software] = False
            continue
        
        path_obj = Path(path)
        if software == 'python':
            # Check if Python executable exists
            validation_results[software] = path_obj.exists() and path_obj.is_file()
        else:
            # Check if directory exists
            validation_results[software] = path_obj.exists() and path_obj.is_dir()
    
    return validation_results


def detect_software_paths() -> Dict[str, str]:
    """
    Detect common software installation paths.
    
    Returns:
        Dictionary of detected software paths
    """
    detected_paths = {}
    
    # Common ImageJ/Fiji paths
    possible_imagej_paths = [
        "/Applications/ImageJ.app",
        "/Applications/Fiji.app",
        "/usr/local/ImageJ",
        "/opt/ImageJ"
    ]
    
    for path in possible_imagej_paths:
        if Path(path).exists():
            detected_paths['imagej'] = path
            break
    
    # Common Python paths
    import sys
    detected_paths['python'] = sys.executable
    
    # Cellpose is typically installed via pip, so we'll check if it's importable
    # Use subprocess to avoid NumPy compatibility issues
    import subprocess
    try:
        result = subprocess.run(
            [sys.executable, "-c", "import cellpose; print(cellpose.__file__)"],
            capture_output=True,
            text=True,
            timeout=10
        )
        if result.returncode == 0:
            cellpose_path = result.stdout.strip()
            detected_paths['cellpose'] = str(Path(cellpose_path).parent)
        else:
            # Check if the error is just a NumPy compatibility warning
            stderr_output = result.stderr if result.stderr else ""
            if "numpy" in stderr_output.lower() and "compatibility" in stderr_output.lower():
                # NumPy compatibility warning - try to get the path anyway
                try:
                    # Try a different approach to get cellpose path
                    result2 = subprocess.run(
                        [sys.executable, "-c", "import cellpose; print(cellpose.__file__)"],
                        capture_output=True,
                        text=True,
                        timeout=10
                    )
                    if result2.returncode == 0:
                        cellpose_path = result2.stdout.strip()
                        detected_paths['cellpose'] = str(Path(cellpose_path).parent)
                    else:
                        detected_paths['cellpose'] = ""
                except subprocess.SubprocessError:
                    detected_paths['cellpose'] = ""
            else:
                detected_paths['cellpose'] = ""
    except (subprocess.SubprocessError, subprocess.TimeoutExpired):
        detected_paths['cellpose'] = ""
    
    return detected_paths 