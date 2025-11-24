"""
Percell Plugins Module

This module provides plugin functionality for extending Percell's capabilities.

Plugins can be created in several ways:
1. Create a class inheriting from PerCellPlugin
2. Use the template generator: python -m percell.plugins.template_generator MyPlugin
3. Convert existing scripts: python -m percell.plugins.converter script.py

Plugins are automatically discovered and registered when PerCell starts.
"""

from percell.plugins.base import PerCellPlugin, PluginMetadata, LegacyPluginAdapter
from percell.plugins.registry import (
    PluginRegistry,
    get_plugin_registry,
    register_plugin
)

__all__ = [
    'PerCellPlugin',
    'PluginMetadata',
    'LegacyPluginAdapter',
    'PluginRegistry',
    'get_plugin_registry',
    'register_plugin',
]
