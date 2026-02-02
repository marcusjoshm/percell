"""
Auto Image Preprocessing Plugin for PerCell

This plugin provides comprehensive microscopy image processing functionality.
Wrapped to use the new plugin architecture while maintaining backward compatibility.
"""

from __future__ import annotations

import argparse
from typing import Optional

from percell.plugins.base import PerCellPlugin, PluginMetadata
from percell.ports.driving.user_interface_port import UserInterfacePort

# Import the original plugin function
from percell.plugins._auto_image_preprocessing_legacy import (
    run_auto_image_preprocessing_workflow
)

# Plugin metadata
_PLUGIN_METADATA = PluginMetadata(
    name="a_auto_image_preprocessing",
    version="1.0.0",
    description="z-stack, max projection, merge",
    author="PerCell Team",
    requires_input_dir=False,  # Plugin prompts for directories
    requires_output_dir=False,  # Plugin prompts for directories
    requires_config=False,
    category="preprocessing",
    menu_title="Auto Image Preprocessing",
    menu_description="z-stack, max projection, merge"
)

# For backwards compatibility
METADATA = _PLUGIN_METADATA


class AutoImagePreprocessingPlugin(PerCellPlugin):
    """Auto Image Preprocessing plugin."""

    # Class-level METADATA for plugin registry discovery
    METADATA = _PLUGIN_METADATA

    def __init__(self, metadata: Optional[PluginMetadata] = None):
        """Initialize plugin."""
        super().__init__(metadata or _PLUGIN_METADATA)
    
    def execute(
        self,
        ui: UserInterfacePort,
        args: argparse.Namespace
    ) -> Optional[argparse.Namespace]:
        """Execute the auto image preprocessing workflow."""
        try:
            # Run the original workflow function
            run_auto_image_preprocessing_workflow(ui)
            
            # The original function handles its own prompts and returns
            # We just need to return args to continue menu flow
            return args
            
        except Exception as e:
            ui.error(f"Error executing plugin: {e}")
            import traceback
            ui.error(traceback.format_exc())
            ui.prompt("Press Enter to continue...")
            return None

