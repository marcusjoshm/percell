#!/usr/bin/env python3
"""
Plugin Template Generator for PerCell

Generates a template plugin file that developers can use as a starting point.
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Optional


def generate_plugin_template(
    plugin_name: str,
    output_dir: Optional[Path] = None,
    description: Optional[str] = None,
    author: Optional[str] = None
) -> Path:
    """Generate a plugin template.
    
    Args:
        plugin_name: Name of the plugin
        output_dir: Output directory (defaults to percell/plugins)
        description: Optional plugin description
        author: Optional author name
        
    Returns:
        Path to generated plugin file
    """
    if output_dir is None:
        output_dir = Path(__file__).parent
    
    plugin_name_clean = plugin_name.lower().replace(' ', '_').replace('-', '_')
    class_name = ''.join(word.capitalize() for word in plugin_name_clean.split('_')) + 'Plugin'
    
    description = description or f"Plugin: {plugin_name}"
    author = author or "Your Name"
    
    template = f'''"""
{plugin_name.title()} Plugin for PerCell

{description}
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Optional

from percell.plugins.base import PerCellPlugin, PluginMetadata
from percell.ports.driving.user_interface_port import UserInterfacePort

# Plugin metadata
METADATA = PluginMetadata(
    name="{plugin_name_clean}",
    version="1.0.0",
    description="{description}",
    author="{author}",
    requires_input_dir=False,  # Set to True if plugin needs input directory
    requires_output_dir=False,  # Set to True if plugin needs output directory
    requires_config=False,      # Set to True if plugin needs configuration service
    category="custom",
    menu_title="{plugin_name.title()}",
    menu_description="{description}"
)


class {class_name}(PerCellPlugin):
    """{plugin_name} plugin implementation."""
    
    def __init__(self):
        """Initialize plugin."""
        super().__init__(METADATA)
    
    def execute(
        self,
        ui: UserInterfacePort,
        args: argparse.Namespace
    ) -> Optional[argparse.Namespace]:
        """Execute the plugin.
        
        Args:
            ui: User interface for interaction
            args: Command line arguments namespace
            
        Returns:
            Updated args namespace or None to exit
        """
        ui.info(f"🔧 Running {{self.metadata.name}} plugin")
        ui.info("=" * 60)
        
        try:
            # Get directories from args or prompt
            input_dir = getattr(args, 'input', None)
            output_dir = getattr(args, 'output', None)
            
            if self.metadata.requires_input_dir and not input_dir:
                input_dir = ui.prompt("Enter input directory path: ").strip()
                if not Path(input_dir).exists():
                    ui.error(f"Input directory does not exist: {{input_dir}}")
                    return args
            
            if self.metadata.requires_output_dir and not output_dir:
                output_dir = ui.prompt("Enter output directory path: ").strip()
                try:
                    Path(output_dir).mkdir(parents=True, exist_ok=True)
                except Exception as e:
                    ui.error(f"Cannot create output directory: {{e}}")
                    return args
            
            # TODO: Implement your plugin logic here
            ui.info("Plugin logic goes here...")
            
            # Example: Access PerCell services
            # config = self.config
            # imagej = self.get_imagej()
            # fs = self.get_filesystem()
            # imgproc = self.get_image_processor()
            # cellpose = self.get_cellpose()
            
            ui.info("\\n✅ Plugin execution completed successfully!")
            ui.prompt("Press Enter to return to main menu...")
            
            return args
            
        except Exception as e:
            ui.error(f"Error executing plugin: {{e}}")
            import traceback
            ui.error(traceback.format_exc())
            ui.prompt("Press Enter to continue...")
            return args
'''
    
    plugin_file = output_dir / f"{plugin_name_clean}.py"
    with open(plugin_file, 'w') as f:
        f.write(template)
    
    return plugin_file


def main():
    """Main entry point for template generator."""
    parser = argparse.ArgumentParser(
        description="Generate a PerCell plugin template"
    )
    parser.add_argument(
        "name",
        type=str,
        help="Plugin name"
    )
    parser.add_argument(
        "--description",
        type=str,
        help="Plugin description"
    )
    parser.add_argument(
        "--author",
        type=str,
        help="Author name"
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="Output directory (defaults to percell/plugins)"
    )
    
    args = parser.parse_args()
    
    try:
        plugin_file = generate_plugin_template(
            args.name,
            args.output,
            args.description,
            args.author
        )
        print(f"✅ Generated plugin template: {plugin_file}")
        print(f"\\n📝 Next steps:")
        print(f"   1. Edit {plugin_file} to implement your plugin logic")
        print(f"   2. Update METADATA with your plugin information")
        print(f"   3. Test your plugin by running PerCell")
        return 0
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    import sys
    sys.exit(main())

