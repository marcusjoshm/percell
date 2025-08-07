#!/usr/bin/env python3
"""
Single-Cell-Analyzer Installation Script

This script provides a complete installation and setup for the Single-Cell-Analyzer package.
It handles:
1. Virtual environment creation
2. Package installation
3. Configuration setup
4. Software path detection
5. Package installation in development mode

Usage:
    python install.py
"""

import os
import sys
import json
import subprocess
import venv
from pathlib import Path
from typing import Dict, List, Optional
import argparse

# Colors for output
class Colors:
    RED = '\033[0;31m'
    GREEN = '\033[0;32m'
    YELLOW = '\033[1;33m'
    BLUE = '\033[0;34m'
    NC = '\033[0m'  # No Color

# Global variable for Python command
python_cmd = 'python3.11'

def print_status(message: str, color: str = Colors.GREEN):
    """Print a status message with color."""
    print(f"{color}[INFO]{Colors.NC} {message}")

def print_error(message: str):
    """Print an error message."""
    print(f"{Colors.RED}[ERROR]{Colors.NC} {message}")

def print_warning(message: str):
    """Print a warning message."""
    print(f"{Colors.YELLOW}[WARNING]{Colors.NC} {message}")

def check_python_version():
    """Check if Python 3.11 is available."""
    # Try to find Python 3.11 specifically
    python_commands = ['python3.11', 'python3.11', 'python']
    
    for cmd in python_commands:
        try:
            result = subprocess.run([cmd, "--version"], 
                                  capture_output=True, text=True, check=True)
            version = result.stdout.strip()
            
            if "3.11" in version:
                print_status(f"Found Python 3.11: {version}")
                # Update sys.executable to use Python 3.11
                global python_cmd
                python_cmd = cmd
                return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            continue
    
    print_error("Python 3.11 is not found. Please install Python 3.11 first.")
    print_warning("You can install it using:")
    print_warning("  macOS: brew install python@3.11")
    print_warning("  Ubuntu: sudo apt install python3.11")
    print_warning("  Or download from: https://www.python.org/downloads/")
    return False

def create_virtual_environment(venv_name: str = "venv") -> bool:
    """Create a virtual environment."""
    venv_path = Path(venv_name)
    
    if venv_path.exists():
        print_status(f"Virtual environment '{venv_name}' already exists")
        return True
    
    try:
        print_status(f"Creating virtual environment '{venv_name}' using {python_cmd}...")
        subprocess.run([python_cmd, "-m", "venv", venv_name], check=True)
        print_status(f"Virtual environment '{venv_name}' created successfully")
        return True
    except subprocess.CalledProcessError as e:
        print_error(f"Failed to create virtual environment: {e}")
        return False

def get_venv_python(venv_name: str = "venv") -> Path:
    """Get the Python executable path for a virtual environment."""
    venv_path = Path(venv_name)
    
    if sys.platform == "win32":
        return venv_path / "Scripts" / "python.exe"
    else:
        return venv_path / "bin" / "python"

def install_requirements(venv_name: str, requirements_file: str) -> bool:
    """Install requirements in a virtual environment."""
    venv_path = Path(venv_name)
    python_path = get_venv_python(venv_name)
    
    if not venv_path.exists():
        print_error(f"Virtual environment '{venv_name}' does not exist")
        return False
    
    try:
        print_status(f"Installing requirements from {requirements_file}...")
        
        # Upgrade pip
        subprocess.run([str(python_path), "-m", "pip", "install", "--upgrade", "pip"], 
                      check=True, capture_output=True)
        
        # Install requirements with verbose output for debugging
        result = subprocess.run([str(python_path), "-m", "pip", "install", "-r", requirements_file], 
                              capture_output=True, text=True)
        
        if result.returncode != 0:
            print_error(f"Failed to install requirements from {requirements_file}")
            print_error(f"Error output: {result.stderr}")
            return False
        
        print_status(f"Requirements installed successfully in '{venv_name}'")
        return True
    except subprocess.CalledProcessError as e:
        print_error(f"Failed to install requirements: {e}")
        if hasattr(e, 'stderr') and e.stderr:
            print_error(f"Error details: {e.stderr}")
        return False

def install_package_development_mode(venv_name: str = "venv") -> bool:
    """Install the package in development mode."""
    python_path = get_venv_python(venv_name)
    
    try:
        print_status("Installing package in development mode...")
        subprocess.run([str(python_path), "-m", "pip", "install", "-e", "."], 
                      check=True, capture_output=True)
        print_status("Package installed in development mode successfully")
        return True
    except subprocess.CalledProcessError as e:
        print_error(f"Failed to install package: {e}")
        return False

def create_cellpose_venv() -> bool:
    """Create and configure the Cellpose virtual environment."""
    try:
        # Create Cellpose virtual environment
        if not create_virtual_environment("cellpose_venv"):
            return False
        
        # Install Cellpose requirements
        if not install_requirements("cellpose_venv", "requirements_cellpose.txt"):
            print_warning("Cellpose installation failed. This is optional and the main workflow will still work.")
            print_warning("You can install Cellpose manually later if needed for segmentation.")
            return False
        
        print_status("Cellpose virtual environment setup complete")
        return True
    except Exception as e:
        print_error(f"Failed to setup Cellpose environment: {e}")
        print_warning("Cellpose installation failed. This is optional and the main workflow will still work.")
        return False

def check_cellpose_availability() -> bool:
    """Check if Cellpose is available in the cellpose_venv."""
    cellpose_python = get_venv_python("cellpose_venv")
    
    try:
        result = subprocess.run([str(cellpose_python), "-c", "import cellpose; print('Cellpose available')"], 
                              capture_output=True, text=True)
        return result.returncode == 0
    except Exception:
        return False

def print_cellpose_guidance():
    """Print guidance about Cellpose installation."""
    print("\n" + "="*60)
    print_warning("Cellpose Installation Guidance")
    print("="*60)
    print("\nCellpose is used for interactive cell segmentation.")
    print("If you need to perform cell segmentation, you can:")
    print("\n1. Try installing Cellpose manually:")
    print("   source cellpose_venv/bin/activate")
    print("   pip install cellpose[gui]==4.0.4")
    print("\n2. Or use the --skip-cellpose flag to skip this step:")
    print("   python install.py --skip-cellpose")
    print("\n3. Or install Cellpose later when needed:")
    print("   source cellpose_venv/bin/activate")
    print("   pip install -r requirements_cellpose.txt")
    print("="*60)

def detect_software_paths() -> Dict[str, str]:
    """Detect software paths for configuration."""
    paths = {}
    
    # Common ImageJ/Fiji locations
    imagej_locations = [
        "/Applications/Fiji.app/Contents/MacOS/ImageJ-macosx",
        "/Applications/ImageJ.app/Contents/MacOS/ImageJ-macosx",
        "/usr/local/Fiji.app/Contents/MacOS/ImageJ-macosx",
        "C:\\Program Files\\Fiji.app\\ImageJ-win64.exe",
        "C:\\Program Files\\ImageJ\\ImageJ.exe"
    ]
    
    for location in imagej_locations:
        if Path(location).exists():
            paths["imagej_path"] = location
            print_status(f"Found ImageJ/Fiji at: {location}")
            break
    else:
        print_warning("ImageJ/Fiji not found in common locations")
        paths["imagej_path"] = ""
    
    # Check for Cellpose in the cellpose_venv
    cellpose_python = get_venv_python("cellpose_venv")
    try:
        result = subprocess.run([str(cellpose_python), "-c", "import cellpose; print('Cellpose available')"], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            paths["cellpose_available"] = "true"
            print_status("Cellpose is available in cellpose_venv")
        else:
            paths["cellpose_available"] = "false"
            print_warning("Cellpose not available in cellpose_venv")
    except Exception:
        paths["cellpose_available"] = "false"
        print_warning("Could not verify Cellpose installation")
    
    return paths

def create_config_file() -> bool:
    """Create or update the configuration file with detected paths.
    Writes to package config and mirrors to legacy config/ if present.
    """
    pkg_config_path = Path("single_cell_analyzer/config/config.json")
    pkg_template_path = Path("single_cell_analyzer/config/config.template.json")
    legacy_dir = Path("config")
    legacy_config_path = legacy_dir / "config.json"
    legacy_template_path = legacy_dir / "config.template.json"

    try:
        # Load base config from existing file or template (prefer package template)
        base_config = None
        if pkg_config_path.exists():
            with open(pkg_config_path, 'r') as f:
                base_config = json.load(f)
        elif pkg_template_path.exists():
            with open(pkg_template_path, 'r') as f:
                base_config = json.load(f)
        elif legacy_template_path.exists():
            with open(legacy_template_path, 'r') as f:
                base_config = json.load(f)
        else:
            print_error("No configuration template found to create config file")
            return False

        # Detect software paths and update
        detected_paths = detect_software_paths()
        if "directories" not in base_config:
            base_config["directories"] = {}
        base_config["directories"].update(detected_paths)

        # Write package config
        pkg_config_path.parent.mkdir(parents=True, exist_ok=True)
        with open(pkg_config_path, 'w') as f:
            json.dump(base_config, f, indent=2)
        print_status(f"Configuration file written to: {pkg_config_path}")

        # Mirror to legacy path if legacy config directory exists
        if legacy_dir.exists():
            legacy_config_path.parent.mkdir(parents=True, exist_ok=True)
            with open(legacy_config_path, 'w') as f:
                json.dump(base_config, f, indent=2)
            print_status(f"Configuration file mirrored to: {legacy_config_path}")

        return True
    except Exception as e:
        print_error(f"Failed to create configuration file: {e}")
        return False

def verify_installation(venv_name: str = "venv") -> bool:
    """Verify the installation by testing imports."""
    python_path = get_venv_python(venv_name)
    
    try:
        print_status("Verifying installation...")
        
        # Test basic imports
        test_imports = [
            "import numpy",
            "import pandas", 
            "import single_cell_analyzer"
        ]
        
        for import_statement in test_imports:
            result = subprocess.run([str(python_path), "-c", import_statement], 
                                  capture_output=True, text=True)
            if result.returncode != 0:
                print_error(f"Failed to import: {import_statement}")
                return False
        
        print_status("Basic imports verified successfully")
        
        # Test command-line tool
        result = subprocess.run([str(python_path), "-m", "single_cell_analyzer.scripts.main", "--help"], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            print_status("Command-line tool verified successfully")
        else:
            print_warning("Command-line tool test failed")
        
        return True
    except Exception as e:
        print_error(f"Verification failed: {e}")
        return False

def print_usage_instructions():
    """Print usage instructions."""
    print("\n" + "="*60)
    print_status("Installation completed successfully!", Colors.BLUE)
    print("="*60)
    print("\nTo use the Single-Cell-Analyzer:")
    print("\n1. Activate the virtual environment:")
    print("   source venv/bin/activate")
    print("\n2. Run the analysis tool:")
    print("   single-cell-analyzer")
    print("\n   OR")
    print("   python single_cell_analyzer/scripts/main.py")
    print("\n3. For Cellpose operations, activate the Cellpose environment:")
    print("   source cellpose_venv/bin/activate")
    print("\nFor more information, see the README.md file.")
    print("="*60)

def main():
    """Main installation function."""
    parser = argparse.ArgumentParser(description="Install Single-Cell-Analyzer")
    parser.add_argument("--skip-cellpose", action="store_true", 
                       help="Skip Cellpose virtual environment setup")
    parser.add_argument("--skip-config", action="store_true", 
                       help="Skip configuration file creation")
    parser.add_argument("--force", action="store_true", 
                       help="Force reinstallation even if environments exist")
    
    args = parser.parse_args()
    
    print("Single-Cell-Analyzer Installation Script")
    print("="*50)
    
    # Check Python version
    if not check_python_version():
        sys.exit(1)
    
    # Create main virtual environment
    if args.force and Path("venv").exists():
        print_status("Removing existing venv (--force specified)")
        import shutil
        shutil.rmtree("venv")
    
    if not create_virtual_environment("venv"):
        sys.exit(1)
    
    # Install main requirements
    if not install_requirements("venv", "requirements.txt"):
        sys.exit(1)
    
    # Install package in development mode
    if not install_package_development_mode("venv"):
        sys.exit(1)
    
    # Create Cellpose virtual environment (optional)
    if not args.skip_cellpose:
        if args.force and Path("cellpose_venv").exists():
            print_status("Removing existing cellpose_venv (--force specified)")
            import shutil
            shutil.rmtree("cellpose_venv")
        
        if not create_cellpose_venv():
            print_cellpose_guidance()
    else:
        print_status("Skipping Cellpose installation as requested")
    
    # Create configuration file
    if not args.skip_config:
        if not create_config_file():
            print_warning("Configuration file creation failed, but installation continues")
    
    # Verify installation
    if not verify_installation("venv"):
        print_warning("Installation verification failed, but installation may still work")
    
    # Check Cellpose availability and provide guidance
    if not args.skip_cellpose and Path("cellpose_venv").exists():
        if not check_cellpose_availability():
            print_cellpose_guidance()
    
    # Print usage instructions
    print_usage_instructions()

if __name__ == "__main__":
    main() 