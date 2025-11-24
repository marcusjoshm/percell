#!/usr/bin/env python3
"""
Script to Plugin Converter for PerCell

This tool converts existing Python scripts into PerCell plugins.
It analyzes the script and generates a plugin with proper integration.
"""

from __future__ import annotations

import ast
import re
import sys
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple
import argparse


class ScriptAnalyzer(ast.NodeVisitor):
    """Analyzes Python scripts to extract information for plugin conversion."""
    
    def __init__(self):
        """Initialize analyzer."""
        self.imports: Set[str] = set()
        self.functions: List[Tuple[str, ast.FunctionDef]] = []
        self.main_function: Optional[ast.FunctionDef] = None
        self.has_argparse = False
        self.has_pathlib = False
        self.has_ui_interaction = False
        self.file_operations: Set[str] = set()
        self.requires_input_dir = False
        self.requires_output_dir = False
        self.requires_config = False
        
    def visit_Import(self, node: ast.Import) -> None:
        """Visit import statements."""
        for alias in node.names:
            self.imports.add(alias.name)
            if alias.name == 'argparse':
                self.has_argparse = True
            if alias.name == 'pathlib' or alias.name == 'Path':
                self.has_pathlib = True
    
    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        """Visit from imports."""
        if node.module:
            self.imports.add(node.module)
            if node.module == 'argparse':
                self.has_argparse = True
            if node.module == 'pathlib':
                self.has_pathlib = True
            for alias in node.names:
                if alias.name == 'Path':
                    self.has_pathlib = True
    
    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        """Visit function definitions."""
        self.functions.append((node.name, node))
        
        # Check for main function patterns
        if node.name == 'main' or node.name.startswith('run_') or node.name.endswith('_workflow'):
            self.main_function = node
        
        # Analyze function body for patterns
        self._analyze_function_body(node)
    
    def _analyze_function_body(self, node: ast.FunctionDef) -> None:
        """Analyze function body for common patterns."""
        for child in ast.walk(node):
            # Check for file operations
            if isinstance(child, ast.Call):
                if isinstance(child.func, ast.Attribute):
                    if child.func.attr in ('open', 'read', 'write', 'mkdir', 'exists', 'glob', 'rglob'):
                        self.file_operations.add(child.func.attr)
            
            # Check for input/output directory patterns
            if isinstance(child, ast.Str) or (isinstance(child, ast.Constant) and isinstance(child.value, str)):
                value = child.value if isinstance(child, ast.Constant) else child.s
                if 'input' in value.lower() and 'dir' in value.lower():
                    self.requires_input_dir = True
                if 'output' in value.lower() and 'dir' in value.lower():
                    self.requires_output_dir = True
            
            # Check for config patterns
            if isinstance(child, ast.Name):
                if child.id in ('config', 'configuration', 'settings'):
                    self.requires_config = True


class PluginGenerator:
    """Generates PerCell plugins from analyzed scripts."""
    
    def __init__(self, script_path: Path, plugin_name: Optional[str] = None):
        """Initialize generator.
        
        Args:
            script_path: Path to source script
            plugin_name: Optional plugin name (derived from filename if not provided)
        """
        self.script_path = script_path
        self.plugin_name = plugin_name or script_path.stem.lower().replace(' ', '_')
        self.analyzer = ScriptAnalyzer()
    
    def analyze(self) -> ScriptAnalyzer:
        """Analyze the source script.
        
        Returns:
            ScriptAnalyzer instance with analysis results
        """
        with open(self.script_path, 'r') as f:
            source = f.read()
        
        tree = ast.parse(source)
        self.analyzer.visit(tree)
        
        # Additional heuristics
        if 'input' in source.lower() and 'directory' in source.lower():
            self.analyzer.requires_input_dir = True
        if 'output' in source.lower() and 'directory' in source.lower():
            self.analyzer.requires_output_dir = True
        
        return self.analyzer
    
    def generate_plugin(self, output_dir: Optional[Path] = None) -> Tuple[Path, Path]:
        """Generate plugin files.
        
        Args:
            output_dir: Output directory (defaults to percell/plugins)
            
        Returns:
            Tuple of (plugin_file_path, metadata_file_path)
        """
        if output_dir is None:
            output_dir = Path(__file__).parent
        
        # Analyze script
        analyzer = self.analyze()
        
        # Generate plugin class
        plugin_code = self._generate_plugin_code(analyzer)
        plugin_file = output_dir / f"{self.plugin_name}.py"
        
        with open(plugin_file, 'w') as f:
            f.write(plugin_code)
        
        # Generate metadata
        metadata = self._generate_metadata(analyzer)
        metadata_file = output_dir / self.plugin_name / "plugin.json"
        metadata_file.parent.mkdir(parents=True, exist_ok=True)
        
        import json
        with open(metadata_file, 'w') as f:
            json.dump(metadata, f, indent=2)
        
        return plugin_file, metadata_file
    
    def _generate_plugin_code(self, analyzer: ScriptAnalyzer) -> str:
        """Generate plugin class code.
        
        Args:
            analyzer: Analyzed script information
            
        Returns:
            Generated plugin code
        """
        # Read original script
        with open(self.script_path, 'r') as f:
            original_code = f.read()
        
        # Extract main function or create wrapper
        main_function_code = self._extract_main_function(original_code, analyzer)
        
        # Generate imports
        imports = self._generate_imports(analyzer)
        
        # Generate plugin class
        plugin_class = f'''"""
{self.plugin_name.title()} Plugin for PerCell

Auto-generated from {self.script_path.name}
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Optional

from percell.plugins.base import PerCellPlugin, PluginMetadata
from percell.ports.driving.user_interface_port import UserInterfacePort

# Original script imports
{imports}

# Plugin metadata
METADATA = PluginMetadata(
    name="{self.plugin_name}",
    version="1.0.0",
    description="Auto-generated plugin from {self.script_path.name}",
    author="Auto-generated",
    requires_input_dir={str(analyzer.requires_input_dir).lower()},
    requires_output_dir={str(analyzer.requires_output_dir).lower()},
    requires_config={str(analyzer.requires_config).lower()},
    category="converted",
    menu_title="{self.plugin_name.replace('_', ' ').title()}",
    menu_description="Auto-generated from {self.script_path.name}"
)


class {self.plugin_name.title().replace('_', '')}Plugin(PerCellPlugin):
    """Plugin generated from {self.script_path.name}."""
    
    def __init__(self):
        """Initialize plugin."""
        super().__init__(METADATA)
    
    def execute(
        self,
        ui: UserInterfacePort,
        args: argparse.Namespace
    ) -> Optional[argparse.Namespace]:
        """Execute the plugin."""
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
            
            # Set directories in args for script compatibility
            args.input = input_dir
            args.output = output_dir
            
            # Execute main function
            {main_function_code}
            
            ui.info("\\nPlugin execution completed successfully!")
            ui.prompt("Press Enter to return to main menu...")
            
            return args
            
        except Exception as e:
            ui.error(f"Error executing plugin: {{e}}")
            import traceback
            ui.error(traceback.format_exc())
            ui.prompt("Press Enter to continue...")
            return args
'''
        
        return plugin_class
    
    def _extract_main_function(self, original_code: str, analyzer: ScriptAnalyzer) -> str:
        """Extract or create main function code.
        
        Args:
            original_code: Original script code
            analyzer: Analyzed script information
            
        Returns:
            Main function code to execute
        """
        if analyzer.main_function:
            # Extract the main function body
            func_lines = original_code.split('\n')
            # This is simplified - in practice, you'd want to properly extract the function
            return f"# Execute main function from original script\\n            # TODO: Integrate main function logic"
        
        # Look for if __name__ == '__main__' block
        if "__name__" in original_code and "__main__" in original_code:
            return f"# Execute main block from original script\\n            # TODO: Integrate main block logic"
        
        # Default: try to call a function with common names
        for func_name, _ in analyzer.functions:
            if func_name in ('main', 'run', 'execute', 'process'):
                return f"# Call {func_name} function\\n            # TODO: Call {func_name}(ui, args)"
        
        return "# TODO: Integrate script logic here"
    
    def _generate_imports(self, analyzer: ScriptAnalyzer) -> str:
        """Generate import statements.
        
        Args:
            analyzer: Analyzed script information
            
        Returns:
            Import statements
        """
        imports = []
        
        # Common PerCell imports
        percell_imports = [
            "from percell.domain.services.configuration_service import ConfigurationService",
            "from percell.domain.services.image_metadata_service import ImageMetadataService",
        ]
        
        # Add based on detected usage
        if 'numpy' in analyzer.imports or 'np' in str(analyzer.imports):
            imports.append("import numpy as np")
        if 'pandas' in analyzer.imports or 'pd' in str(analyzer.imports):
            imports.append("import pandas as pd")
        if 'tifffile' in analyzer.imports:
            imports.append("import tifffile")
        if 'PIL' in analyzer.imports or 'Image' in str(analyzer.imports):
            imports.append("from PIL import Image")
        
        # Add original script imports (filtered)
        for imp in sorted(analyzer.imports):
            if not imp.startswith('percell'):
                if imp not in ('argparse', 'sys', 'os'):  # These are handled separately
                    imports.append(f"import {imp}")
        
        return "\\n".join(imports) if imports else "# No additional imports needed"
    
    def _generate_metadata(self, analyzer: ScriptAnalyzer) -> Dict:
        """Generate plugin metadata.
        
        Args:
            analyzer: Analyzed script information
            
        Returns:
            Metadata dictionary
        """
        return {
            "name": self.plugin_name,
            "version": "1.0.0",
            "description": f"Auto-generated plugin from {self.script_path.name}",
            "author": "Auto-generated",
            "dependencies": sorted(list(analyzer.imports)),
            "requires_config": analyzer.requires_config,
            "requires_input_dir": analyzer.requires_input_dir,
            "requires_output_dir": analyzer.requires_output_dir,
            "category": "converted",
            "menu_title": self.plugin_name.replace('_', ' ').title(),
            "menu_description": f"Auto-generated from {self.script_path.name}"
        }


def convert_script(
    script_path: Path,
    plugin_name: Optional[str] = None,
    output_dir: Optional[Path] = None
) -> Tuple[Path, Path]:
    """Convert a Python script to a PerCell plugin.
    
    Args:
        script_path: Path to source script
        plugin_name: Optional plugin name
        output_dir: Optional output directory
        
    Returns:
        Tuple of (plugin_file_path, metadata_file_path)
    """
    generator = PluginGenerator(script_path, plugin_name)
    return generator.generate_plugin(output_dir)


def main():
    """Main entry point for converter."""
    parser = argparse.ArgumentParser(
        description="Convert Python scripts to PerCell plugins"
    )
    parser.add_argument(
        "script",
        type=Path,
        help="Path to Python script to convert"
    )
    parser.add_argument(
        "--name",
        type=str,
        help="Plugin name (defaults to script filename)"
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="Output directory (defaults to percell/plugins)"
    )
    
    args = parser.parse_args()
    
    if not args.script.exists():
        print(f"Error: Script not found: {args.script}")
        return 1
    
    try:
        plugin_file, metadata_file = convert_script(
            args.script,
            args.name,
            args.output
        )
        print(f"✅ Generated plugin: {plugin_file}")
        print(f"✅ Generated metadata: {metadata_file}")
        print(f"\\n⚠️  Note: You may need to manually integrate the script logic into the plugin.")
        return 0
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())

