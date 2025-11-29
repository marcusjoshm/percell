# Percell Windows Compatibility Refactoring Guide

## Overview
This document provides comprehensive instructions for refactoring the percell microscopy analysis tool to support Windows alongside Mac/Linux. The refactoring will be performed using Claude Code.

## Prerequisites
- Windows 10/11 development machine
- Python 3.8+ installed
- Git for Windows
- Claude Code installed and configured
- Access to the percell repository

## Phase 1: Project Analysis and Setup

### 1.1 Initial Repository Analysis
```bash
# Clone the repository
git clone https://github.com/marcusjoshm/percell.git
cd percell

# Create a new branch for Windows compatibility
git checkout -b windows-compatibility
```

### 1.2 Identify Platform-Specific Components
Review and catalog all platform-specific elements:
- Shell scripts (`.sh` files)
- Path separators and file paths
- Virtual environment references
- System commands
- Symbolic links
- Installation scripts

## Phase 2: Core Refactoring Tasks

### 2.1 Create Cross-Platform Path Handler

Create `percell/utils/path_utils.py`:
```python
"""
Cross-platform path utilities for percell
"""
import os
import platform
from pathlib import Path

def get_platform():
    """Return the current platform"""
    return platform.system()

def is_windows():
    """Check if running on Windows"""
    return get_platform() == 'Windows'

def is_mac():
    """Check if running on macOS"""
    return get_platform() == 'Darwin'

def is_linux():
    """Check if running on Linux"""
    return get_platform() == 'Linux'

def get_venv_activate_path():
    """Get the virtual environment activation script path"""
    if is_windows():
        return Path('venv') / 'Scripts' / 'activate.bat'
    else:
        return Path('venv') / 'bin' / 'activate'

def get_venv_python():
    """Get the virtual environment Python executable path"""
    if is_windows():
        return Path('venv') / 'Scripts' / 'python.exe'
    else:
        return Path('venv') / 'bin' / 'python'

def get_user_home():
    """Get user home directory in a cross-platform way"""
    return Path.home()

def normalize_path(path_str):
    """Normalize path for the current platform"""
    return str(Path(path_str))

def find_imagej():
    """Find ImageJ/Fiji installation path"""
    possible_paths = []
    
    if is_windows():
        possible_paths.extend([
            Path('C:/Program Files/Fiji.app'),
            Path('C:/Program Files (x86)/Fiji.app'),
            Path('C:/Fiji.app'),
            Path(os.environ.get('LOCALAPPDATA', '')) / 'Fiji.app',
            Path.home() / 'Fiji.app',
        ])
    elif is_mac():
        possible_paths.extend([
            Path('/Applications/Fiji.app'),
            Path.home() / 'Applications/Fiji.app',
        ])
    else:  # Linux
        possible_paths.extend([
            Path('/opt/Fiji.app'),
            Path.home() / 'Fiji.app',
            Path('/usr/local/Fiji.app'),
        ])
    
    for path in possible_paths:
        if path.exists():
            return path
    
    return None
```

### 2.2 Create Windows Installation Script

Create `install.bat`:
```batch
@echo off
setlocal enabledelayedexpansion

echo ===============================================
echo Percell Installation for Windows
echo ===============================================
echo.

REM Check Python installation
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.8+ and add it to PATH
    exit /b 1
)

REM Create virtual environment
echo Creating virtual environment...
python -m venv venv
if errorlevel 1 (
    echo ERROR: Failed to create virtual environment
    exit /b 1
)

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat

REM Upgrade pip
echo Upgrading pip...
python -m pip install --upgrade pip

REM Install requirements
if exist requirements.txt (
    echo Installing dependencies...
    pip install -r requirements.txt
)

REM Install package in development mode
echo Installing percell in development mode...
pip install -e .

REM Run Python setup script
echo Configuring percell...
python percell\setup\install_windows.py

echo.
echo ===============================================
echo Installation complete!
echo ===============================================
echo.
echo To use percell:
echo 1. Activate the virtual environment: venv\Scripts\activate
echo 2. Run: percell
echo.
pause
```

Create `install.ps1` (PowerShell alternative):
```powershell
# Percell Installation Script for Windows (PowerShell)

Write-Host "===============================================" -ForegroundColor Cyan
Write-Host "Percell Installation for Windows" -ForegroundColor Cyan
Write-Host "===============================================" -ForegroundColor Cyan
Write-Host ""

# Check Python installation
try {
    $pythonVersion = python --version 2>&1
    Write-Host "Found Python: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "ERROR: Python is not installed or not in PATH" -ForegroundColor Red
    Write-Host "Please install Python 3.8+ and add it to PATH" -ForegroundColor Yellow
    exit 1
}

# Create virtual environment
Write-Host "Creating virtual environment..." -ForegroundColor Yellow
python -m venv venv
if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: Failed to create virtual environment" -ForegroundColor Red
    exit 1
}

# Activate virtual environment
Write-Host "Activating virtual environment..." -ForegroundColor Yellow
& ".\venv\Scripts\Activate.ps1"

# Upgrade pip
Write-Host "Upgrading pip..." -ForegroundColor Yellow
python -m pip install --upgrade pip

# Install requirements
if (Test-Path "requirements.txt") {
    Write-Host "Installing dependencies..." -ForegroundColor Yellow
    pip install -r requirements.txt
}

# Install package in development mode
Write-Host "Installing percell in development mode..." -ForegroundColor Yellow
pip install -e .

# Run Python setup script
Write-Host "Configuring percell..." -ForegroundColor Yellow
python percell\setup\install_windows.py

Write-Host ""
Write-Host "===============================================" -ForegroundColor Green
Write-Host "Installation complete!" -ForegroundColor Green
Write-Host "===============================================" -ForegroundColor Green
Write-Host ""
Write-Host "To use percell:" -ForegroundColor Cyan
Write-Host "1. Activate the virtual environment: .\venv\Scripts\Activate" -ForegroundColor White
Write-Host "2. Run: percell" -ForegroundColor White
Write-Host ""
```

### 2.3 Create Windows-Compatible Python Setup Script

Create `percell/setup/install_windows.py`:
```python
#!/usr/bin/env python
"""
Windows-specific installation and setup for percell
"""
import os
import sys
import json
import shutil
import subprocess
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from percell.utils.path_utils import find_imagej, is_windows

def create_config():
    """Create configuration file with Windows paths"""
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
    imagej_path = find_imagej()
    if imagej_path:
        config["paths"]["imagej"] = str(imagej_path)
        print(f"✓ Found ImageJ/Fiji at: {imagej_path}")
    else:
        print("⚠ ImageJ/Fiji not found. Please set path manually in config/config.json")
    
    # Check for Cellpose environment
    conda_envs = Path.home() / "Anaconda3" / "envs"
    if conda_envs.exists():
        cellpose_env = conda_envs / "cellpose"
        if cellpose_env.exists():
            config["paths"]["cellpose_env"] = str(cellpose_env)
            print(f"✓ Found Cellpose environment at: {cellpose_env}")
    
    # Save config
    config_dir = Path("config")
    config_dir.mkdir(exist_ok=True)
    config_file = config_dir / "config.json"
    
    with open(config_file, 'w') as f:
        json.dump(config, f, indent=4)
    
    print(f"✓ Configuration saved to: {config_file}")
    return config_file

def create_batch_wrapper():
    """Create batch file wrapper for percell command"""
    wrapper_content = """@echo off
setlocal
set "SCRIPT_DIR=%~dp0"
call "%SCRIPT_DIR%venv\\Scripts\\activate.bat"
python -m percell.main %*
"""
    
    wrapper_path = Path("percell.bat")
    with open(wrapper_path, 'w') as f:
        f.write(wrapper_content)
    
    print(f"✓ Created batch wrapper: {wrapper_path}")
    
    # Try to add to PATH (requires admin rights)
    print("\nTo run 'percell' from anywhere, add this directory to your PATH:")
    print(f"  {Path.cwd()}")

def create_replace_spaces_script():
    """Create Windows script to replace spaces in filenames"""
    script_content = """@echo off
setlocal enabledelayedexpansion

echo ========================================================
echo Space to Underscore Converter - Windows Version
echo ========================================================
echo.

if "%~1"=="" (
    echo Usage: replace_spaces.bat "path\to\directory"
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
        ren "%%f" "!new_name!"
    )
)

echo.
echo Processing directories...
for /f "tokens=*" %%d in ('dir "%target_dir%" /ad /b /s ^| sort /r') do (
    set "old_name=%%~nxd"
    set "new_name=!old_name: =_!"
    if not "!old_name!"=="!new_name!" (
        echo Renaming: %%~nxd
        ren "%%d" "!new_name!"
    )
)

echo.
echo [SUCCESS] Operation completed successfully!
pause
"""
    
    script_dir = Path("scripts")
    script_dir.mkdir(exist_ok=True)
    script_path = script_dir / "replace_spaces.bat"
    
    with open(script_path, 'w') as f:
        f.write(script_content)
    
    print(f"✓ Created space replacement script: {script_path}")

def verify_installation():
    """Verify the installation is working"""
    try:
        # Test import
        import percell
        print("✓ Percell package imported successfully")
        
        # Test dependencies
        required_packages = ['numpy', 'pandas', 'scikit-image', 'matplotlib']
        for package in required_packages:
            try:
                __import__(package)
                print(f"✓ {package} is installed")
            except ImportError:
                print(f"⚠ {package} is not installed")
        
        return True
    except Exception as e:
        print(f"✗ Installation verification failed: {e}")
        return False

def main():
    """Main installation routine for Windows"""
    print("\n=== Percell Windows Setup ===\n")
    
    if not is_windows():
        print("This script is for Windows only!")
        sys.exit(1)
    
    # Create configuration
    config_file = create_config()
    
    # Create batch wrapper
    create_batch_wrapper()
    
    # Create utility scripts
    create_replace_spaces_script()
    
    # Verify installation
    print("\n=== Verifying Installation ===\n")
    if verify_installation():
        print("\n✓ Installation completed successfully!")
    else:
        print("\n⚠ Installation completed with warnings")
        print("Please check the messages above and install missing components")
    
    print("\n=== Next Steps ===")
    print("1. Review the configuration file: config/config.json")
    print("2. Set any missing paths (ImageJ, Cellpose environment)")
    print("3. Run 'percell' or 'percell.bat' to start the application")

if __name__ == "__main__":
    main()
```

### 2.4 Update Main Application Entry Point

Modify `percell/main.py` to handle Windows:
```python
"""
Main entry point for percell application
Cross-platform compatible version
"""
import sys
import os
from pathlib import Path

# Add utils to path
sys.path.insert(0, str(Path(__file__).parent))

from utils.path_utils import is_windows, get_platform
from single_cell_workflow import main as workflow_main

def setup_windows_console():
    """Setup Windows console for colored output"""
    if is_windows():
        try:
            import colorama
            colorama.init()
        except ImportError:
            print("Warning: colorama not installed. Colors may not display correctly.")
            print("Install with: pip install colorama")

def print_header():
    """Print application header"""
    print("=" * 60)
    print("PERCELL - Single Cell Microscopy Analysis Tool")
    print(f"Platform: {get_platform()}")
    print("=" * 60)
    print()

def main():
    """Main entry point"""
    setup_windows_console()
    print_header()
    
    try:
        # Run the main workflow
        workflow_main()
    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"\nError: {e}")
        if is_windows():
            input("\nPress Enter to exit...")
        sys.exit(1)

if __name__ == "__main__":
    main()
```

## Phase 3: Testing Strategy

### 3.1 Create Windows Test Suite

Create `tests/test_windows_compatibility.py`:
```python
"""
Windows compatibility tests for percell
"""
import unittest
import sys
import os
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from percell.utils.path_utils import (
    is_windows, 
    get_venv_activate_path,
    find_imagej,
    normalize_path
)

class TestWindowsCompatibility(unittest.TestCase):
    
    def test_platform_detection(self):
        """Test platform detection"""
        if sys.platform == 'win32':
            self.assertTrue(is_windows())
    
    def test_venv_paths(self):
        """Test virtual environment path resolution"""
        activate = get_venv_activate_path()
        if is_windows():
            self.assertTrue('Scripts' in str(activate))
        else:
            self.assertTrue('bin' in str(activate))
    
    def test_path_normalization(self):
        """Test path normalization"""
        test_path = "path/to/file.txt"
        normalized = normalize_path(test_path)
        if is_windows():
            self.assertTrue('\\' in normalized or '/' in normalized)
    
    def test_imagej_detection(self):
        """Test ImageJ/Fiji detection"""
        imagej_path = find_imagej()
        if imagej_path:
            self.assertTrue(imagej_path.exists())
            print(f"Found ImageJ at: {imagej_path}")
        else:
            print("ImageJ not found (this is okay if not installed)")

if __name__ == '__main__':
    unittest.main()
```

### 3.2 Integration Testing Checklist

1. **Installation Testing**
   - [ ] Clean Windows 10 installation
   - [ ] Clean Windows 11 installation
   - [ ] Installation with spaces in path
   - [ ] Installation without admin rights
   - [ ] Installation with existing Python environments

2. **Functionality Testing**
   - [ ] Virtual environment creation and activation
   - [ ] Package installation via pip
   - [ ] Configuration file generation
   - [ ] ImageJ/Fiji detection
   - [ ] Cellpose integration
   - [ ] File path handling with spaces
   - [ ] Batch processing of images
   - [ ] CLI interface functionality

3. **Edge Cases**
   - [ ] Unicode characters in paths
   - [ ] Network drives
   - [ ] Very long path names (>260 characters)
   - [ ] Case-sensitive vs case-insensitive filesystems

## Phase 4: Documentation Updates

### 4.1 Update README.md

Add Windows-specific sections:
```markdown
## Installation

### Windows

1. **Prerequisites**
   - Windows 10/11
   - Python 3.8 or higher
   - Git for Windows (optional, for cloning the repository)

2. **Installation Steps**
   ```cmd
   # Clone the repository (or download ZIP)
   git clone https://github.com/marcusjoshm/percell.git
   cd percell
   
   # Run the installation script
   install.bat
   
   # Or use PowerShell
   powershell -ExecutionPolicy Bypass -File install.ps1
   ```

3. **Configuration**
   - The installer will attempt to locate ImageJ/Fiji automatically
   - Review `config\config.json` and update paths if needed
   - Set up Cellpose environment (see Cellpose documentation)

4. **Running Percell**
   ```cmd
   # Activate virtual environment
   venv\Scripts\activate
   
   # Run percell
   percell
   
   # Or use the batch wrapper
   percell.bat
   ```

### Troubleshooting Windows Issues

**Issue: Scripts execution disabled**
- Run PowerShell as Administrator
- Execute: `Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser`

**Issue: Python not found**
- Ensure Python is in PATH
- Reinstall Python with "Add to PATH" option checked

**Issue: Long path errors**
- Enable long path support in Windows
- Run in Administrator PowerShell: `New-ItemProperty -Path "HKLM:\SYSTEM\CurrentControlSet\Control\FileSystem" -Name "LongPathsEnabled" -Value 1 -PropertyType DWORD -Force`
```

### 4.2 Create Windows-Specific User Guide

Create `docs/WINDOWS_GUIDE.md`:
```markdown
# Percell Windows User Guide

## Getting Started on Windows

This guide provides Windows-specific instructions for using Percell.

## Terminal Usage

### Opening Terminal
- **Command Prompt**: Press `Win+R`, type `cmd`, press Enter
- **PowerShell**: Press `Win+X`, select "Windows PowerShell"
- **Windows Terminal**: Press `Win+R`, type `wt`, press Enter (Windows 11)

### Navigation Commands
- Change directory: `cd path\to\directory`
- List files: `dir`
- Current directory: `cd` (without arguments)

## File Path Handling

### Drag and Drop
Instead of typing paths manually, you can drag files/folders from File Explorer into the terminal window.

### Path Formats
- Windows uses backslashes: `C:\Users\Username\Documents`
- Forward slashes also work in most cases: `C:/Users/Username/Documents`
- Paths with spaces need quotes: `"C:\My Documents\Data"`

## Virtual Environment

### Activation
```cmd
# Command Prompt
venv\Scripts\activate.bat

# PowerShell
.\venv\Scripts\Activate.ps1

# Git Bash
source venv/Scripts/activate
```

### Deactivation
```cmd
deactivate
```

## Common Issues and Solutions

### Issue: 'percell' is not recognized
**Solution**: Ensure virtual environment is activated or use `percell.bat`

### Issue: Permission denied errors
**Solution**: Run terminal as Administrator or check file permissions

### Issue: Module not found errors
**Solution**: Verify virtual environment is activated and packages are installed

## Performance Optimization

### GPU Support
1. Install CUDA toolkit for NVIDIA GPUs
2. Install GPU-enabled PyTorch/TensorFlow
3. Configure Cellpose for GPU usage

### Memory Management
- Close unnecessary applications
- Increase virtual memory if processing large images
- Consider processing images in batches

## Integration with Windows Tools

### Windows Subsystem for Linux (WSL)
If you prefer Unix-like environment:
1. Install WSL2
2. Clone repository in WSL
3. Use Linux installation instructions

### Visual Studio Code
1. Install Python extension
2. Open percell folder
3. Select Python interpreter from venv
4. Use integrated terminal
```

## Phase 5: Claude Code Implementation Strategy

### 5.1 Preparation for Claude Code

Create a structured prompt file `claude_code_prompts.md`:
```markdown
# Claude Code Refactoring Prompts

## Initial Setup
"I need to refactor the percell microscopy analysis tool for Windows compatibility. The codebase is currently Mac/Linux only. Please analyze the repository structure and identify all platform-specific code."

## Refactoring Tasks

### Task 1: Path Handling
"Refactor all file path handling in the codebase to use pathlib.Path for cross-platform compatibility. Replace Unix-specific path separators with platform-agnostic solutions."

### Task 2: Shell Scripts
"Convert the bash shell scripts (install, replace_spaces.sh, fix_global_install.sh) to Windows batch files and PowerShell scripts while maintaining the same functionality."

### Task 3: Virtual Environment
"Update all virtual environment references to work with both Unix (venv/bin) and Windows (venv\Scripts) structures."

### Task 4: Configuration
"Modify the configuration system to detect and handle Windows-specific paths for ImageJ, Cellpose, and data directories."

### Task 5: Testing
"Create comprehensive test cases for Windows compatibility, including path handling, script execution, and package installation."
```

### 5.2 Claude Code Workflow

1. **Initial Analysis**
   ```
   claude-code analyze percell/
   ```

2. **Iterative Refactoring**
   ```
   claude-code refactor --platform windows --preserve-compatibility
   ```

3. **Testing**
   ```
   claude-code test --platform windows
   ```

4. **Documentation Generation**
   ```
   claude-code document --platform windows
   ```

## Phase 6: Deployment and Distribution

### 6.1 Create Windows Installer

Consider creating an installer using:
- **PyInstaller**: Create standalone executable
- **NSIS**: Create professional Windows installer
- **MSI**: Create Windows Installer package

Example PyInstaller spec file `percell.spec`:
```python
# percell.spec
a = Analysis(
    ['percell/main.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('config', 'config'),
        ('scripts', 'scripts'),
    ],
    hiddenimports=['skimage', 'matplotlib', 'cellpose'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='percell',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='assets/icon.ico'
)
```

### 6.2 Continuous Integration

Add Windows testing to CI/CD pipeline (`.github/workflows/windows.yml`):
```yaml
name: Windows CI

on: [push, pull_request]

jobs:
  test:
    runs-on: windows-latest
    strategy:
      matrix:
        python-version: [3.8, 3.9, 3.10, 3.11]
    
    steps:
    - uses: actions/checkout@v2
    
    - name: Set up Python
      uses: actions/setup-python@v2
      with:
        python-version: ${{ matrix.python-version }}
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt
        pip install -e .
    
    - name: Run tests
      run: |
        python -m pytest tests/
    
    - name: Test installation script
      run: |
        ./install.bat
```

## Checklist for Claude Code Session

- [ ] Analyze entire codebase for platform dependencies
- [ ] Create path_utils.py module
- [ ] Convert shell scripts to Windows equivalents
- [ ] Update main.py for cross-platform support
- [ ] Modify setup.py for Windows entry points
- [ ] Update configuration handling
- [ ] Create Windows-specific tests
- [ ] Update all documentation
- [ ] Test on clean Windows installation
- [ ] Verify ImageJ/Cellpose integration
- [ ] Package for distribution
- [ ] Create installation video/tutorial

## Additional Considerations

1. **Unicode and Encoding**: Ensure all file I/O uses explicit encoding (utf-8)
2. **Line Endings**: Configure Git to handle CRLF/LF conversion
3. **Permissions**: Handle Windows file permissions appropriately
4. **Antivirus**: Test with common antivirus software
5. **Dependencies**: Verify all Python packages support Windows
6. **Performance**: Profile and optimize for Windows file system

## Success Metrics

- Installation completes without errors on Windows 10/11
- All core features work identically on Windows/Mac/Linux
- Performance is comparable across platforms
- Documentation is clear and platform-specific where needed
- CI/CD passes on all platforms
- User can process microscopy data without platform-specific issues
