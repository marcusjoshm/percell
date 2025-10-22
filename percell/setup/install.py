#!/usr/bin/env python3
"""
Percell Installation Script

This script provides a complete installation and setup for the Percell package.
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

        # Upgrade pip with verbose output
        print_status("Upgrading pip...")
        pip_upgrade_result = subprocess.run([str(python_path), "-m", "pip", "install", "--upgrade", "pip"],
                      capture_output=True, text=True, check=True)
        if pip_upgrade_result.stdout:
            print(f"  {pip_upgrade_result.stdout.strip()}")

        # Count requirements for progress tracking
        with open(requirements_file, 'r') as f:
            requirements_lines = [line.strip() for line in f if line.strip() and not line.strip().startswith('#')]
            req_count = len(requirements_lines)

        print_status(f"Installing {req_count} requirements with verbose output...")

        # Install requirements with verbose output and progress
        result = subprocess.run([str(python_path), "-m", "pip", "install", "-v", "-r", requirements_file],
                              text=True)

        if result.returncode != 0:
            print_error(f"Failed to install requirements from {requirements_file}")
            print_error("Installation failed - check the output above for details")
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
        print_status("Installing percell package in development mode...")
        print_status("This will install all dependencies from pyproject.toml...")

        # Install with verbose output
        result = subprocess.run([str(python_path), "-m", "pip", "install", "-v", "-e", "."],
                      text=True)

        if result.returncode != 0:
            print_error("Failed to install percell package in development mode")
            print_error("Installation failed - check the output above for details")
            return False

        print_status("Percell package installed in development mode successfully")
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
        if not install_requirements("cellpose_venv", "percell/setup/requirements_cellpose.txt"):
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
    """Print guidance about Cellpose installation (platform-aware)."""
    import sys
    from percell.utils.path_utils import get_venv_activate_path

    print("\n" + "="*80)
    print_warning("Cellpose Installation Guidance")
    print("="*80)
    print("\nCellpose is used for interactive cell segmentation.")
    print("If you need to perform cell segmentation, you can:")

    activate_cmd = str(get_venv_activate_path("cellpose_venv"))
    if sys.platform == 'win32':
        activate_cmd = activate_cmd.replace('/', '\\')

    print("\n1. Try installing Cellpose manually:")
    if sys.platform == 'win32':
        print(f"   {activate_cmd}")
    else:
        print(f"   source {activate_cmd}")
    print("   pip install cellpose[gui]==4.0.4")

    print("\n2. Or use the --skip-cellpose flag to skip this step:")
    print("   python install.py --skip-cellpose")

    print("\n3. Or install Cellpose later when needed:")
    if sys.platform == 'win32':
        print(f"   {activate_cmd}")
    else:
        print(f"   source {activate_cmd}")
    print("   pip install -r percell/setup/requirements_cellpose.txt")
    print("="*60)

def detect_software_paths() -> Dict[str, str]:
    """Detect software paths for configuration using cross-platform utilities."""
    paths = {}

    # Use cross-platform ImageJ detection from path_utils
    from percell.utils.path_utils import get_imagej_executable

    imagej_exe = get_imagej_executable()
    if imagej_exe:
        paths["imagej_path"] = str(imagej_exe)
        print_status(f"Found ImageJ/Fiji at: {imagej_exe}")
    else:
        print_warning("ImageJ/Fiji not found in common locations")
        print_warning("Please install ImageJ/Fiji and set the path manually in config/config.json")
        paths["imagej_path"] = ""
    
    # Get Python path from main virtual environment
    main_python = get_venv_python("venv")
    if main_python.exists():
        paths["python_path"] = str(main_python)
        print_status(f"Found Python at: {main_python}")
    else:
        print_warning("Main Python virtual environment not found")
        paths["python_path"] = ""
    
    # Check for Cellpose in the cellpose_venv
    cellpose_python = get_venv_python("cellpose_venv")
    if cellpose_python.exists():
        paths["cellpose_path"] = str(cellpose_python)
        print_status(f"Found Cellpose Python at: {cellpose_python}")
        
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
    else:
        print_warning("Cellpose virtual environment not found")
        paths["cellpose_path"] = ""
        paths["cellpose_available"] = "false"
    
    return paths

def create_config_file() -> bool:
    """Create or update the configuration file with detected paths.
    Writes to package config at percell/config/config.json only.
    """
    pkg_config_path = Path("percell/config/config.json")
    pkg_template_path = Path("percell/config/config.template.json")
    legacy_template_path = Path("config/config.template.json")

    try:
        # Load base config from existing file or template (prefer package template)
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

        # Detect software paths
        detected_paths = detect_software_paths()
        
        # Update top-level required fields
        base_config["imagej_path"] = detected_paths.get("imagej_path", "")
        base_config["cellpose_path"] = detected_paths.get("cellpose_path", "")
        base_config["python_path"] = detected_paths.get("python_path", "")
        
        # Update directories section
        if "directories" not in base_config:
            base_config["directories"] = {}
        base_config["directories"].update(detected_paths)

        # Write package config only
        pkg_config_path.parent.mkdir(parents=True, exist_ok=True)
        with open(pkg_config_path, 'w') as f:
            json.dump(base_config, f, indent=2)
        print_status(f"Configuration file written to: {pkg_config_path}")

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
            ("numpy", "import numpy; print(f'NumPy {numpy.__version__}')"),
            ("pandas", "import pandas; print(f'Pandas {pandas.__version__}')"),
            ("napari", "import napari; print(f'Napari {napari.__version__}')"),
            ("percell", "import percell; print('Percell package imported successfully')")
        ]

        for import_name, import_statement in test_imports:
            print_status(f"Testing {import_name} import...")
            result = subprocess.run([str(python_path), "-c", import_statement],
                                  capture_output=True, text=True)
            if result.returncode != 0:
                print_error(f"Failed to import {import_name}")
                if result.stderr:
                    print_error(f"Error: {result.stderr.strip()}")
                return False
            else:
                if result.stdout:
                    print(f"  ✓ {result.stdout.strip()}")

        print_status("All imports verified successfully")

        # Test command-line tool
        print_status("Testing percell command-line tool...")
        result = subprocess.run([str(python_path), "-m", "percell.main.main", "--help"],
                              capture_output=True, text=True)
        if result.returncode == 0:
            print_status("Command-line tool verified successfully")
            print("  ✓ Percell CLI is working")
        else:
            print_warning("Command-line tool test failed")
            if result.stderr:
                print_warning(f"Error: {result.stderr.strip()}")

        return True
    except Exception as e:
        print_error(f"Verification failed: {e}")
        return False

def create_global_symlink() -> bool:
    """Create a global symbolic link for the percell command (Unix/Linux/macOS only)."""
    import sys

    # Skip on Windows - not applicable
    if sys.platform == 'win32':
        print_status("Skipping global symlink creation (not applicable on Windows)")
        print_status("On Windows, use: python -m percell.main.main")
        print_status("Or add the project directory to your PATH to use percell.bat")
        return True

    try:
        # Get the current directory (project root)
        project_root = Path.cwd()
        from percell.utils.path_utils import get_venv_scripts_dir
        venv_scripts = get_venv_scripts_dir("venv")
        venv_percell = project_root / venv_scripts / "percell"
        global_percell = Path("/usr/local/bin/percell")

        if not venv_percell.exists():
            print_error(f"Percell command not found in virtual environment: {venv_percell}")
            return False

        # Create the symbolic link
        if global_percell.exists():
            print_status("Removing existing global percell link")
            global_percell.unlink()

        print_status("Creating global symbolic link...")
        global_percell.symlink_to(venv_percell)
        print_status(f"Global percell command created at: {global_percell}")
        return True
    except PermissionError:
        print_warning("Permission denied creating global symlink. You may need to run with sudo.")
        print_warning("You can create the symlink manually:")
        print_warning(f"sudo ln -sf {venv_percell} /usr/local/bin/percell")
        return False
    except Exception as e:
        print_error(f"Failed to create global symlink: {e}")
        return False

def print_usage_instructions():
    """Print usage instructions (platform-aware)."""
    import sys
    from percell.utils.path_utils import get_venv_activate_path

    print("\n" + "="*80)
    print_status("Installation completed successfully!", Colors.BLUE)
    print("="*80)
    print("\nTo use Percell:")

    if sys.platform == 'win32':
        # Windows instructions
        print("\n1. Run directly with Python:")
        print("   python -m percell.main.main")
        print("\n2. Or use the batch wrapper:")
        print("   percell.bat")
        print("\n3. Or activate the virtual environment:")
        venv_activate = str(get_venv_activate_path("venv")).replace('/', '\\')
        print(f"   {venv_activate}")
        print("   python -m percell.main.main")
        print("\n4. For Cellpose operations, activate the Cellpose environment:")
        cellpose_activate = str(get_venv_activate_path("cellpose_venv")).replace('/', '\\')
        print(f"   {cellpose_activate}")
    else:
        # Unix/Linux/macOS instructions
        print("\n1. Global command (recommended):")
        print("   percell")
        print("\n2. Or activate the virtual environment:")
        print("   source venv/bin/activate")
        print("   percell")
        print("\n3. For Cellpose operations, activate the Cellpose environment:")
        print("   source cellpose_venv/bin/activate")
    print("\nFor more information, see the README.md file.")
    print("="*80)

def main():
    """Main installation function."""
    parser = argparse.ArgumentParser(description="Install Percell")
    parser.add_argument("--skip-cellpose", action="store_true",
                       help="Skip Cellpose virtual environment setup")
    parser.add_argument("--skip-config", action="store_true",
                       help="Skip configuration file creation")
    parser.add_argument("--force", action="store_true",
                       help="Force reinstallation even if environments exist")
    parser.add_argument("--verbose", "-v", action="store_true",
                       help="Enable verbose output during installation")

    args = parser.parse_args()
    
    print("Percell Installation Script")
    print("="*50)

    if args.verbose:
        print_status("Verbose mode enabled - showing detailed installation progress")
        print_status(f"Current working directory: {Path.cwd()}")
        print_status(f"Python executable: {sys.executable}")
        print("")

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
    if not install_requirements("venv", "percell/setup/requirements.txt"):
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
    
    # Create global symlink
    if not create_global_symlink():
        print_warning("Global symlink creation failed, but you can still use percell from the venv")
    
    # Check Cellpose availability and provide guidance
    if not args.skip_cellpose and Path("cellpose_venv").exists():
        if not check_cellpose_availability():
            print_cellpose_guidance()
    
    # Print usage instructions
    print_usage_instructions()

if __name__ == "__main__":
    main() 