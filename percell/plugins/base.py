"""
Base Plugin Interface for PerCell

This module provides the base classes and interfaces for creating PerCell plugins.
Plugins can integrate seamlessly with PerCell's services and infrastructure.
"""

from __future__ import annotations

import argparse
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Optional, List, Callable
import json
import importlib.util
import inspect

from percell.ports.driving.user_interface_port import UserInterfacePort


@dataclass
class PluginMetadata:
    """Metadata describing a PerCell plugin."""
    
    name: str
    version: str
    description: str
    author: str
    author_email: Optional[str] = None
    dependencies: List[str] = field(default_factory=list)
    requires_config: bool = False
    requires_input_dir: bool = False
    requires_output_dir: bool = False
    category: str = "general"
    menu_title: Optional[str] = None
    menu_description: Optional[str] = None
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> PluginMetadata:
        """Create PluginMetadata from dictionary."""
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "version": self.version,
            "description": self.description,
            "author": self.author,
            "author_email": self.author_email,
            "dependencies": self.dependencies,
            "requires_config": self.requires_config,
            "requires_input_dir": self.requires_input_dir,
            "requires_output_dir": self.requires_output_dir,
            "category": self.category,
            "menu_title": self.menu_title,
            "menu_description": self.menu_description,
        }


class PerCellPlugin(ABC):
    """Base class for PerCell plugins.
    
    Plugins should inherit from this class and implement the required methods.
    The plugin system will automatically discover and register plugins.
    """
    
    def __init__(self, metadata: PluginMetadata):
        """Initialize plugin with metadata.
        
        Args:
            metadata: Plugin metadata describing the plugin
        """
        self.metadata = metadata
        self._config: Optional[Any] = None
        self._container: Optional[Any] = None
    
    @property
    def name(self) -> str:
        """Get plugin name."""
        return self.metadata.name
    
    @property
    def version(self) -> str:
        """Get plugin version."""
        return self.metadata.version
    
    @property
    def description(self) -> str:
        """Get plugin description."""
        return self.metadata.description
    
    def set_config(self, config: Any) -> None:
        """Set configuration service.
        
        Args:
            config: ConfigurationService instance
        """
        self._config = config
    
    def set_container(self, container: Any) -> None:
        """Set dependency injection container.
        
        Args:
            container: Container instance with adapters and services
        """
        self._container = container
    
    @property
    def config(self) -> Any:
        """Get configuration service.
        
        Returns:
            ConfigurationService instance
            
        Raises:
            RuntimeError: If config not set
        """
        if self._config is None:
            raise RuntimeError(f"Config not set for plugin {self.name}")
        return self._config
    
    @property
    def container(self) -> Any:
        """Get dependency injection container.
        
        Returns:
            Container instance
            
        Raises:
            RuntimeError: If container not set
        """
        if self._container is None:
            raise RuntimeError(f"Container not set for plugin {self.name}")
        return self._container
    
    def get_imagej(self):
        """Get ImageJ adapter from container."""
        return getattr(self.container, 'imagej', None) if self.container else None
    
    def get_filesystem(self):
        """Get filesystem adapter from container."""
        return getattr(self.container, 'fs', None) if self.container else None
    
    def get_image_processor(self):
        """Get image processing adapter from container."""
        return getattr(self.container, 'imgproc', None) if self.container else None
    
    def get_cellpose(self):
        """Get Cellpose adapter from container."""
        return getattr(self.container, 'cellpose', None) if self.container else None
    
    @abstractmethod
    def execute(
        self,
        ui: UserInterfacePort,
        args: argparse.Namespace
    ) -> Optional[argparse.Namespace]:
        """Execute the plugin.
        
        This is the main entry point for plugin execution. Plugins should
        implement their logic here.
        
        Args:
            ui: User interface for interaction
            args: Command line arguments namespace
            
        Returns:
            Updated args namespace or None to exit
        """
        pass
    
    def validate(self, ui: UserInterfacePort, args: argparse.Namespace) -> bool:
        """Validate plugin requirements before execution.
        
        Override this method to add custom validation logic.
        
        Args:
            ui: User interface for interaction
            args: Command line arguments namespace
            
        Returns:
            True if validation passes, False otherwise
        """
        if self.metadata.requires_input_dir:
            input_dir = getattr(args, 'input', None)
            if not input_dir:
                ui.error(f"Plugin {self.name} requires an input directory")
                return False
            if not Path(input_dir).exists():
                ui.error(f"Input directory does not exist: {input_dir}")
                return False
        
        if self.metadata.requires_output_dir:
            output_dir = getattr(args, 'output', None)
            if not output_dir:
                ui.error(f"Plugin {self.name} requires an output directory")
                return False
        
        if self.metadata.requires_config:
            if self._config is None:
                ui.error(f"Plugin {self.name} requires configuration service")
                return False
        
        return True
    
    def get_menu_title(self) -> str:
        """Get menu title for this plugin."""
        return self.metadata.menu_title or self.metadata.name.replace('_', ' ').title()
    
    def get_menu_description(self) -> str:
        """Get menu description for this plugin."""
        return self.metadata.menu_description or self.metadata.description


class LegacyPluginAdapter(PerCellPlugin):
    """Adapter for legacy plugin functions.
    
    This allows existing plugin functions to work with the new plugin system
    without requiring code changes.
    """
    
    def __init__(self, metadata: PluginMetadata, plugin_function: Callable):
        """Initialize adapter with legacy function.
        
        Args:
            metadata: Plugin metadata
            plugin_function: Legacy plugin function (ui, args) -> args
        """
        super().__init__(metadata)
        self.plugin_function = plugin_function
    
    def execute(
        self,
        ui: UserInterfacePort,
        args: argparse.Namespace
    ) -> Optional[argparse.Namespace]:
        """Execute legacy plugin function."""
        return self.plugin_function(ui, args)

