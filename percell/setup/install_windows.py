#!/usr/bin/env python
"""
Windows-specific installation and setup for percell

This script handles Windows-specific configuration during installation:
- Detects ImageJ/Fiji installation
- Detects Cellpose environment
- Creates configuration file with Windows paths
- Creates batch wrapper for running percell
- Creates utility scripts for Windows
"""
import os
import sys
import json
import shutil
import subprocess
from pathlib import Path

# Add parent directory to path to allow imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from percell.utils.path_utils import (
    find_imagej,
    get_imagej_executable,
    is_windows,
    get_venv_python,
)


def create_config():
    """
    Create configuration file with Windows paths.

    Attempts to auto-detect ImageJ/Fiji and Cellpose installations.
    """
    config = {
        "platform": "windows",
        "paths": {
            "imagej": None,
            "cellpose_env": None,
            "input": None,
            "output": None
        },
        "settings": {
            "use_gpu": False,
            "cellpose_model": "cyto",
            "debug_mode": False
        }
    }

    # Try to find ImageJ/Fiji
    print("Searching for ImageJ/Fiji installation...")
    imagej_exe = get_imagej_executable()
    if imagej_exe:
        config["paths"]["imagej"] = str(imagej_exe)
        print(f"✓ Found ImageJ/Fiji at: {imagej_exe}")
    else:
        imagej_base = find_imagej()
        if imagej_base:
            config["paths"]["imagej"] = str(imagej_base)
            print(f"✓ Found ImageJ/Fiji directory at: {imagej_base}")
            print("  (Note: Executable not found, you may need to specify it manually)")
        else:
            print("⚠ ImageJ/Fiji not found. Please set path manually in config/config.json")
            print("  Common installation locations:")
            print("  - C:\\Program Files\\Fiji.app")
            print("  - C:\\Program Files (x86)\\Fiji.app")
            print("  - C:\\Fiji.app")

    # Check for Cellpose environment
    print("\nSearching for Cellpose environment...")
    conda_locations = [
        Path.home() / "Anaconda3" / "envs",
        Path.home() / "miniconda3" / "envs",
        Path("C:\\") / "ProgramData" / "Anaconda3" / "envs",
        Path("C:\\") / "ProgramData" / "miniconda3" / "envs",
    ]

    cellpose_found = False
    for conda_envs in conda_locations:
        if conda_envs.exists():
            cellpose_env = conda_envs / "cellpose"
            if cellpose_env.exists():
                python_exe = cellpose_env / "python.exe"
                if python_exe.exists():
                    config["paths"]["cellpose_env"] = str(python_exe)
                    print(f"✓ Found Cellpose environment at: {cellpose_env}")
                    cellpose_found = True
                    break

    if not cellpose_found:
        print("⚠ Cellpose environment not found.")
        print("  To install Cellpose, create a conda environment:")
        print("  conda create -n cellpose python=3.9")
        print("  conda activate cellpose")
        print("  pip install cellpose[gui]")

    # Save config
    config_dir = Path("config")
    config_dir.mkdir(exist_ok=True)
    config_file = config_dir / "config_windows.json"

    with open(config_file, 'w') as f:
        json.dump(config, f, indent=4)

    print(f"\n✓ Configuration saved to: {config_file}")
    return config_file


def create_batch_wrapper():
    """
    Create batch file wrapper for percell command.

    This allows users to run 'percell' or 'percell.bat' from the project directory.
    """
    wrapper_content = """@echo off
setlocal
set "SCRIPT_DIR=%~dp0"
call "%SCRIPT_DIR%venv\\Scripts\\activate.bat"
python -m percell.main.main %*
"""

    wrapper_path = Path("percell.bat")
    with open(wrapper_path, 'w') as f:
        f.write(wrapper_content)

    print(f"✓ Created batch wrapper: {wrapper_path}")

    # Try to add to PATH (requires admin rights)
    print("\nTo run 'percell' from anywhere, add this directory to your PATH:")
    print(f"  {Path.cwd()}")
    print("\nOr run from this directory: .\\percell.bat")


def create_replace_spaces_script():
    """
    Create Windows script to replace spaces in filenames.

    Many scientific tools have issues with spaces in filenames.
    This utility helps fix that on Windows.
    """
    script_content = """@echo off
setlocal enabledelayedexpansion

echo ========================================================
echo Space to Underscore Converter - Windows Version
echo ========================================================
echo.

if "%~1"=="" (
    echo Usage: replace_spaces.bat "path\\to\\directory"
    echo.
    echo Drag and drop a folder onto this script or provide path as argument
    pause
    exit /b 1
)

set "target_dir=%~1"
echo Target directory: %target_dir%
echo.

set /p confirm="This will rename all files and folders with spaces. Continue? (y/n): "
if /i not "%confirm%"=="y" (
    echo Operation cancelled.
    pause
    exit /b 0
)

echo.
echo Processing files...
for /r "%target_dir%" %%f in (*) do (
    set "old_name=%%~nxf"
    set "new_name=!old_name: =_!"
    if not "!old_name!"=="!new_name!" (
        echo Renaming: %%~nxf
        ren "%%f" "!new_name!" 2>nul
    )
)

echo.
echo Processing directories...
for /f "tokens=*" %%d in ('dir "%target_dir%" /ad /b /s ^| sort /r') do (
    set "old_name=%%~nxd"
    set "new_name=!old_name: =_!"
    if not "!old_name!"=="!new_name!" (
        echo Renaming: %%~nxd
        ren "%%d" "!new_name!" 2>nul
    )
)

echo.
echo [SUCCESS] Operation completed!
pause
"""

    script_dir = Path("scripts")
    script_dir.mkdir(exist_ok=True)
    script_path = script_dir / "replace_spaces.bat"

    with open(script_path, 'w') as f:
        f.write(script_content)

    print(f"✓ Created space replacement script: {script_path}")
    print("  Use this to fix filenames with spaces that may cause issues")


def verify_installation():
    """
    Verify the installation is working.

    Tests that percell can be imported and dependencies are available.
    """
    print("\n=== Verifying Installation ===\n")

    try:
        # Test import
        import percell
        print("✓ Percell package imported successfully")

        # Test dependencies
        required_packages = {
            'numpy': 'Numerical computing',
            'pandas': 'Data analysis',
            'skimage': 'Image processing (scikit-image)',
            'matplotlib': 'Plotting',
        }

        for package, description in required_packages.items():
            try:
                __import__(package)
                print(f"✓ {package} is installed ({description})")
            except ImportError:
                print(f"⚠ {package} is not installed ({description})")
                print(f"  Install with: pip install {package}")

        return True
    except Exception as e:
        print(f"✗ Installation verification failed: {e}")
        return False


def print_next_steps():
    """Print next steps for the user."""
    print("\n" + "=" * 60)
    print("Next Steps")
    print("=" * 60)
    print("\n1. Review the configuration file: config\\config_windows.json")
    print("   - Set any missing paths (ImageJ, Cellpose environment)")
    print("   - Configure input/output directories")
    print("\n2. If ImageJ/Fiji was not found:")
    print("   - Download from: https://fiji.sc/")
    print("   - Install to: C:\\Program Files\\Fiji.app")
    print("   - Update config with the installation path")
    print("\n3. If Cellpose is needed for segmentation:")
    print("   - Install Anaconda or Miniconda")
    print("   - Create environment: conda create -n cellpose python=3.9")
    print("   - Activate: conda activate cellpose")
    print("   - Install: pip install cellpose[gui]")
    print("\n4. To run percell:")
    print("   - Option A: .\\percell.bat")
    print("   - Option B: venv\\Scripts\\activate && python -m percell.main.main")
    print("\n5. For help with file naming issues:")
    print("   - Use: scripts\\replace_spaces.bat \"path\\to\\directory\"")
    print("   - This converts spaces to underscores")
    print("\n" + "=" * 60)


def main():
    """Main installation routine for Windows."""
    print("\n" + "=" * 60)
    print("Percell Windows Setup")
    print("=" * 60 + "\n")

    if not is_windows():
        print("⚠ This script is designed for Windows only!")
        print("You are running on:", sys.platform)
        print("\nFor Unix-based systems, use the standard install script.")
        response = input("\nContinue anyway? (y/n): ")
        if response.lower() != 'y':
            sys.exit(1)

    # Create configuration
    config_file = create_config()

    # Create batch wrapper
    print("\n=== Creating Windows Utilities ===\n")
    create_batch_wrapper()

    # Create utility scripts
    create_replace_spaces_script()

    # Verify installation
    if verify_installation():
        print("\n" + "=" * 60)
        print("✓ Installation completed successfully!")
        print("=" * 60)
    else:
        print("\n" + "=" * 60)
        print("⚠ Installation completed with warnings")
        print("=" * 60)
        print("\nPlease check the messages above and install missing components")

    # Print next steps
    print_next_steps()


if __name__ == "__main__":
    main()
