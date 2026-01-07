"""
Plugin Registry for PerCell

This module provides plugin discovery, registration, and management.
"""

from __future__ import annotations

import importlib.util
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Type, Any
import inspect

from percell.plugins.base import PerCellPlugin, PluginMetadata, LegacyPluginAdapter

logger = logging.getLogger(__name__)


class PluginRegistry:
    """Registry for managing PerCell plugins."""
    
    def __init__(self):
        """Initialize plugin registry."""
        self._plugins: Dict[str, PerCellPlugin] = {}
        self._plugin_classes: Dict[str, Type[PerCellPlugin]] = {}
        self._metadata: Dict[str, PluginMetadata] = {}
    
    def register(
        self,
        plugin: PerCellPlugin,
        metadata: Optional[PluginMetadata] = None
    ) -> None:
        """Register a plugin instance.
        
        Args:
            plugin: Plugin instance to register
            metadata: Optional metadata (uses plugin.metadata if not provided)
        """
        metadata = metadata or plugin.metadata
        self._plugins[metadata.name] = plugin
        self._metadata[metadata.name] = metadata
        logger.info(f"Registered plugin: {metadata.name} v{metadata.version}")
    
    def register_class(
        self,
        plugin_class: Type[PerCellPlugin],
        metadata: Optional[PluginMetadata] = None
    ) -> None:
        """Register a plugin class (lazy instantiation).
        
        Args:
            plugin_class: Plugin class to register
            metadata: Optional metadata (will be extracted from class if not provided)
        """
        if metadata is None:
            # Try to extract metadata from class
            if hasattr(plugin_class, 'METADATA'):
                metadata = plugin_class.METADATA
            elif hasattr(plugin_class, 'metadata'):
                metadata = plugin_class.metadata
            else:
                # Create default metadata from class name
                name = plugin_class.__name__.replace('Plugin', '').lower()
                metadata = PluginMetadata(
                    name=name,
                    version="1.0.0",
                    description=f"Plugin: {name}",
                    author="Unknown"
                )
        
        self._plugin_classes[metadata.name] = plugin_class
        self._metadata[metadata.name] = metadata
        logger.info(f"Registered plugin class: {metadata.name}")
    
    def register_legacy_function(
        self,
        function: Any,
        metadata: PluginMetadata
    ) -> None:
        """Register a legacy plugin function.
        
        Args:
            function: Legacy plugin function (ui, args) -> args
            metadata: Plugin metadata
        """
        plugin = LegacyPluginAdapter(metadata, function)
        self.register(plugin, metadata)
    
    def get_plugin(self, name: str) -> Optional[PerCellPlugin]:
        """Get a plugin instance by name.
        
        Args:
            name: Plugin name
            
        Returns:
            Plugin instance or None if not found
        """
        # Check if already instantiated
        if name in self._plugins:
            return self._plugins[name]
        
        # Try to instantiate from class
        if name in self._plugin_classes:
            plugin_class = self._plugin_classes[name]
            metadata = self._metadata[name]
            plugin = plugin_class(metadata)
            self._plugins[name] = plugin
            return plugin
        
        return None
    
    def get_all_plugins(self) -> List[PerCellPlugin]:
        """Get all registered plugins.
        
        Returns:
            List of all plugin instances
        """
        plugins = []
        for name in self._metadata.keys():
            plugin = self.get_plugin(name)
            if plugin:
                plugins.append(plugin)
        return plugins
    
    def get_plugin_names(self) -> List[str]:
        """Get names of all registered plugins.
        
        Returns:
            List of plugin names
        """
        return list(self._metadata.keys())
    
    def get_metadata(self, name: str) -> Optional[PluginMetadata]:
        """Get metadata for a plugin.
        
        Args:
            name: Plugin name
            
        Returns:
            Plugin metadata or None if not found
        """
        return self._metadata.get(name)
    
    def discover_plugins(self, plugin_dir: Optional[Path] = None) -> None:
        """Discover and register plugins from directory.
        
        Args:
            plugin_dir: Directory to search for plugins (defaults to percell/plugins)
        """
        if plugin_dir is None:
            plugin_dir = Path(__file__).parent
        
        logger.info(f"Discovering plugins in {plugin_dir}")
        
        # Find all Python files in plugin directory
        for plugin_file in plugin_dir.glob("*.py"):
            if plugin_file.name.startswith("_") or plugin_file.name == "base.py" or plugin_file.name == "registry.py":
                continue
            
            try:
                self._load_plugin_from_file(plugin_file)
            except Exception as e:
                logger.warning(f"Failed to load plugin from {plugin_file}: {e}")
        
        # Find plugin.json files (for plugins with metadata)
        for plugin_json in plugin_dir.glob("*/plugin.json"):
            try:
                self._load_plugin_from_json(plugin_json)
            except Exception as e:
                logger.warning(f"Failed to load plugin from {plugin_json}: {e}")
    
    def _load_plugin_from_file(self, plugin_file: Path) -> None:
        """Load plugin from Python file.
        
        Args:
            plugin_file: Path to plugin Python file
        """
        spec = importlib.util.spec_from_file_location(
            plugin_file.stem,
            plugin_file
        )
        if spec is None or spec.loader is None:
            return
        
        try:
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
        except ImportError as e:
            # If it's a missing dependency, try to still discover the plugin class
            # by parsing the file directly (simpler AST-based approach)
            logger.warning(f"Import error loading {plugin_file}: {e}")
            logger.info(f"Attempting AST-based discovery for {plugin_file}")
            try:
                self._discover_plugin_from_ast(plugin_file)
            except Exception as ast_error:
                logger.warning(f"AST-based discovery also failed: {ast_error}")
            return
        except Exception as e:
            logger.warning(f"Failed to load plugin from {plugin_file}: {e}")
            return
        
        # Look for plugin classes
        for name, obj in inspect.getmembers(module):
            if (inspect.isclass(obj) and
                issubclass(obj, PerCellPlugin) and
                obj is not PerCellPlugin):
                # Skip internal base classes marked with _INTERNAL_BASE_CLASS
                if hasattr(obj, '_INTERNAL_BASE_CLASS') and obj._INTERNAL_BASE_CLASS:
                    logger.debug(f"Skipping internal base class: {name}")
                    continue

                # Check if it has METADATA attribute
                if hasattr(obj, 'METADATA'):
                    self.register_class(obj, obj.METADATA)
                else:
                    # Try to instantiate to get metadata
                    try:
                        # Create temporary metadata to instantiate
                        temp_metadata = PluginMetadata(
                            name=name.lower().replace('plugin', ''),
                            version="1.0.0",
                            description=f"Plugin: {name}",
                            author="Unknown"
                        )
                        instance = obj(temp_metadata)
                        self.register(instance)
                    except Exception as e:
                        logger.warning(f"Could not instantiate {name}: {e}")
        
        # Look for legacy plugin functions (show_*_plugin pattern)
        for name, obj in inspect.getmembers(module):
            if (inspect.isfunction(obj) and 
                name.startswith("show_") and 
                name.endswith("_plugin")):
                plugin_name = name.replace("show_", "").replace("_plugin", "")
                metadata = PluginMetadata(
                    name=plugin_name,
                    version="1.0.0",
                    description=f"Legacy plugin: {plugin_name}",
                    author="Unknown"
                )
                self.register_legacy_function(obj, metadata)
    
    def _load_plugin_from_json(self, plugin_json: Path) -> None:
        """Load plugin from plugin.json file.
        
        Args:
            plugin_json: Path to plugin.json file
        """
        with open(plugin_json, 'r') as f:
            data = json.load(f)
        
        metadata = PluginMetadata.from_dict(data)
        plugin_dir = plugin_json.parent
        
        # Try to load the plugin module
        plugin_file = plugin_dir / f"{metadata.name}.py"
        if plugin_file.exists():
            spec = importlib.util.spec_from_file_location(
                metadata.name,
                plugin_file
            )
            if spec is None or spec.loader is None:
                return
            
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            # Look for plugin class with matching name
            plugin_class_name = f"{metadata.name.title().replace('_', '')}Plugin"
            if hasattr(module, plugin_class_name):
                plugin_class = getattr(module, plugin_class_name)
                if issubclass(plugin_class, PerCellPlugin):
                    self.register_class(plugin_class, metadata)
            else:
                # Look for any PerCellPlugin subclass
                for name, obj in inspect.getmembers(module):
                    if (inspect.isclass(obj) and 
                        issubclass(obj, PerCellPlugin) and 
                        obj is not PerCellPlugin):
                        self.register_class(obj, metadata)
                        break
    
    def _discover_plugin_from_ast(self, plugin_file: Path) -> None:
        """Discover plugin class from AST without importing module.
        
        This allows discovery even when dependencies are missing.
        
        Args:
            plugin_file: Path to plugin Python file
        """
        import ast
        
        try:
            with open(plugin_file, 'r') as f:
                source = f.read()
            
            tree = ast.parse(source)
            
            # Look for class definitions that inherit from PerCellPlugin
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    # Check if it inherits from PerCellPlugin
                    for base in node.bases:
                        if isinstance(base, ast.Name) and base.id == 'PerCellPlugin':
                            # Found a plugin class!
                            plugin_name = node.name.lower().replace('plugin', '')
                            metadata = PluginMetadata(
                                name=plugin_name,
                                version="1.0.0",
                                description=f"Plugin: {node.name}",
                                author="Unknown"
                            )
                            # Try to find METADATA in the class
                            for item in node.body:
                                if isinstance(item, ast.Assign):
                                    for target in item.targets:
                                        if isinstance(target, ast.Name) and target.id == 'METADATA':
                                            # Found METADATA, but we can't evaluate it without imports
                                            # So we'll use the default metadata
                                            pass
                            
                            logger.info(f"Discovered plugin class {node.name} via AST (dependencies may be missing)")
                            # We can't register the class without importing, but we can note it
                            # The user will need to install dependencies for it to work
                            break
        except Exception as e:
            logger.debug(f"AST discovery failed for {plugin_file}: {e}")


# Global plugin registry instance
_registry: Optional[PluginRegistry] = None


def get_plugin_registry() -> PluginRegistry:
    """Get the global plugin registry instance.
    
    Returns:
        PluginRegistry instance
    """
    global _registry
    if _registry is None:
        _registry = PluginRegistry()
        _registry.discover_plugins()
    return _registry


def register_plugin(plugin: PerCellPlugin) -> None:
    """Register a plugin with the global registry.
    
    Args:
        plugin: Plugin instance to register
    """
    get_plugin_registry().register(plugin)

