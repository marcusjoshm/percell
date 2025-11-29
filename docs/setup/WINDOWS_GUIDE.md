# PerCell Windows User Guide

Complete guide for installing and using PerCell on Windows 10/11.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Installation](#installation)
3. [Running PerCell](#running-percell)
4. [File Path Handling](#file-path-handling)
5. [Terminal Usage](#terminal-usage)
6. [Troubleshooting](#troubleshooting)
7. [Tips and Best Practices](#tips-and-best-practices)

## Prerequisites

### Required Software

#### 1. Python 3.8 or Higher

**Download**: [python.org/downloads](https://www.python.org/downloads/)

**Installation Steps**:
1. Download the latest Python 3.8+ installer for Windows
2. Run the installer
3. ⚠️ **IMPORTANT**: Check "Add Python to PATH" during installation
4. Complete the installation

**Verify Installation**:
```cmd
python --version
```
Should show: `Python 3.8.x` or higher

#### 2. Git for Windows (Optional but Recommended)

**Download**: [git-scm.com/download/win](https://git-scm.com/download/win)

**Alternative**: Download PerCell as a ZIP file from GitHub

### Optional Software

#### ImageJ/Fiji

**Download**: [fiji.sc](https://fiji.sc/)

**Recommended Installation Location**:
```
C:\Program Files\Fiji.app
```

This location will be auto-detected by PerCell during installation.

## Installation

### Step 1: Download PerCell

**Option A: Using Git (Recommended)**
```cmd
git clone https://github.com/marcusjoshm/percell.git
cd percell
```

**Option B: Download ZIP**
1. Visit [github.com/marcusjoshm/percell](https://github.com/marcusjoshm/percell)
2. Click "Code" → "Download ZIP"
3. Extract to desired location
4. Open Command Prompt and navigate to extracted folder

### Step 2: Run Installer

**Option 1: Command Prompt (Recommended)**
```cmd
install.bat
```

**Option 2: PowerShell**

If you see "script execution disabled" error:
```powershell
# Enable script execution first
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

# Then run installer
powershell -ExecutionPolicy Bypass -File install.ps1
```

### Step 3: Wait for Installation

The installer will:
- ✅ Check Python installation
- ✅ Create virtual environment (`venv`)
- ✅ Install all dependencies
- ✅ Install PerCell package
- ✅ Auto-detect ImageJ/Fiji
- ✅ Create configuration files
- ✅ Create launcher (`percell.bat`)
- ✅ Verify installation

**Installation Time**: 5-10 minutes depending on internet speed

### Step 4: Verify Installation

After installation completes, you should see:
```
===============================================
Installation complete!
===============================================

To use Percell:
1. Run directly with Python: python -m percell.main.main
2. Or use the batch wrapper: percell.bat
...
```

## Running PerCell

### Method 1: Batch Wrapper (Easiest)

From the percell directory:
```cmd
percell.bat
```

**Advantages**:
- Simple double-click or command
- Auto-activates virtual environment
- Consistent experience

### Method 2: Virtual Environment

```cmd
# Navigate to percell directory
cd C:\path\to\percell

# Activate virtual environment
venv\Scripts\activate

# Run PerCell
python -m percell.main.main
```

**When to use**: Debugging or development

### Method 3: Direct Python Call

```cmd
cd C:\path\to\percell
python -m percell.main.main
```

**When to use**: Quick access without activation

## File Path Handling

### Understanding Windows Paths

Windows uses **backslashes** (`\`) in file paths:
```
C:\Users\YourName\Documents\Data
```

### Path Formats in PerCell

PerCell accepts both formats:
- **Backslashes**: `C:\Users\YourName\Data`
- **Forward slashes**: `C:/Users/YourName/Data`

### Tips for Entering Paths

#### 1. Drag and Drop
Instead of typing paths manually, drag folders from File Explorer into Command Prompt/PowerShell window. The path will be auto-inserted.

#### 2. Copy Path from File Explorer
1. Hold `Shift` and right-click on folder
2. Select "Copy as path"
3. Paste into terminal

#### 3. Use Tab Completion
Start typing a path and press `Tab` to auto-complete.

### Spaces in File Paths

**Problem**: Spaces in paths can cause issues
```
C:\My Documents\Experiment Data  # Has spaces
```

**Solution 1**: Use quotes
```cmd
"C:\My Documents\Experiment Data"
```

**Solution 2**: Use PerCell's utility to remove spaces
```cmd
scripts\replace_spaces.bat "C:\My Documents\Experiment Data"
```

This converts:
```
Experiment Data → Experiment_Data
My File.tif → My_File.tif
```

## Terminal Usage

### Opening a Terminal

**Command Prompt (cmd)**:
- Press `Win + R`
- Type `cmd`
- Press Enter

**PowerShell**:
- Press `Win + X`
- Select "Windows PowerShell"

**Windows Terminal** (Windows 11):
- Press `Win + R`
- Type `wt`
- Press Enter

### Basic Commands

**Navigate to directory**:
```cmd
cd C:\path\to\directory
```

**Go up one level**:
```cmd
cd ..
```

**List files and folders**:
```cmd
dir
```

**Show current directory**:
```cmd
cd
```

**Clear screen**:
```cmd
cls
```

### Virtual Environment Commands

**Activate environment**:
```cmd
venv\Scripts\activate
```

**Deactivate environment**:
```cmd
deactivate
```

**Check if activated**:
Look for `(venv)` at the start of your command prompt:
```cmd
(venv) C:\percell>
```

## Troubleshooting

### Python Not Found

**Error**: `'python' is not recognized as an internal or external command`

**Solution**:
1. Verify Python is installed:
   - Search for "Python" in Start Menu
   - If not found, reinstall from [python.org](https://www.python.org/)

2. Add Python to PATH manually:
   - Search "Environment Variables" in Start Menu
   - Click "Edit the system environment variables"
   - Click "Environment Variables"
   - Under "System variables", find "Path"
   - Add Python directories:
     ```
     C:\Users\YourName\AppData\Local\Programs\Python\Python3X
     C:\Users\YourName\AppData\Local\Programs\Python\Python3X\Scripts
     ```

### Script Execution Disabled (PowerShell)

**Error**: `cannot be loaded because running scripts is disabled`

**Solution**:
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### Long Path Errors

**Error**: Path length exceeds 260 characters

**Solution** (Requires Administrator):
```powershell
# Open PowerShell as Administrator
# Enable long path support
New-ItemProperty -Path "HKLM:\SYSTEM\CurrentControlSet\Control\FileSystem" -Name "LongPathsEnabled" -Value 1 -PropertyType DWORD -Force

# Restart computer
```

### ImageJ/Fiji Not Detected

**Error**: "ImageJ/Fiji not found in common locations"

**Solution 1**: Install to default location
```
C:\Program Files\Fiji.app
```

**Solution 2**: Manual configuration
1. Open `percell\config\config.json`
2. Find the `imagej_path` field
3. Set it to your Fiji location:
   ```json
   "imagej_path": "C:\\Program Files\\Fiji.app\\ImageJ-win64.exe"
   ```
   Note the double backslashes (`\\`)

### Virtual Environment Creation Failed

**Error**: Failed to create virtual environment

**Possible causes**:
1. Insufficient permissions
2. Antivirus blocking
3. Insufficient disk space

**Solutions**:
```cmd
# Try manual creation
python -m venv venv

# If that fails, check Python installation
python -m pip --version
```

### Module Not Found Errors

**Error**: `ModuleNotFoundError: No module named 'numpy'` (or similar)

**Solution**:
```cmd
# Activate environment
venv\Scripts\activate

# Reinstall dependencies
pip install -e .
```

### Antivirus Blocking Installation

Some antivirus software may block:
- Virtual environment creation
- Package installation
- Script execution

**Solution**:
1. Temporarily disable antivirus
2. Run installation
3. Add `percell` folder to antivirus exceptions
4. Re-enable antivirus

## Tips and Best Practices

### 1. Keep Paths Simple

✅ Good:
```
C:\Data\Experiment_1\
C:\Analysis\Results\
```

❌ Avoid:
```
C:\My Documents\Research Files\Experiment #1\
C:\Users\Name\Desktop\New Folder (2)\
```

### 2. Organize Your Data

Recommended structure:
```
C:\Microscopy\
├── RawData\
│   ├── Experiment_1\
│   └── Experiment_2\
└── Analysis\
    ├── Experiment_1_Results\
    └── Experiment_2_Results\
```

### 3. Use Batch Scripts

Create a custom launcher batch file:

**my_percell.bat**:
```batch
@echo off
cd C:\path\to\percell
call venv\Scripts\activate
python -m percell.main.main
pause
```

### 4. Set Up Desktop Shortcut

1. Right-click `percell.bat`
2. Select "Create shortcut"
3. Move shortcut to Desktop
4. Rename to "PerCell"

### 5. Regular Backups

Before major analysis:
```cmd
# Create backup
xcopy C:\Data\Experiment_1 C:\Backups\Experiment_1_backup /E /I
```

### 6. Monitor Disk Space

PerCell generates many intermediate files. Use the cleanup utility:
```
Utilities → Cleanup
```

### 7. Keep Software Updated

Periodically update PerCell:
```cmd
cd C:\path\to\percell
git pull origin main
pip install -e .
```

## Common Workflows

### Workflow 1: New Analysis

```cmd
# 1. Navigate to percell
cd C:\percell

# 2. Run PerCell
percell.bat

# 3. In PerCell menu:
#    - Configuration → I/O
#    - Set input: C:\Data\MyExperiment
#    - Set output: C:\Analysis\MyExperiment_Results
#    - Workflows → Default Workflow
```

### Workflow 2: Continue Existing Analysis

```cmd
# Same as Workflow 1, but use:
# - Configuration → Analysis Parameters
# - Then specific menu options as needed
```

### Workflow 3: Batch Processing Multiple Datasets

Create a batch script:

**analyze_all.bat**:
```batch
@echo off
cd C:\percell
call venv\Scripts\activate

for %%d in (C:\Data\*) do (
    echo Processing %%d
    python -m percell.main.main --input "%%d" --output "C:\Analysis\%%~nd_results" --complete-workflow
)
```

## Performance Tips

### 1. Use SSD Storage
Store data and output on SSD drives for faster processing.

### 2. Close Unnecessary Programs
Free up RAM before running analysis.

### 3. Process in Batches
For large datasets, process in smaller batches.

### 4. Monitor Resource Usage
Use Task Manager to monitor CPU/RAM usage.

### 5. Disable Windows Indexing
For data directories:
1. Right-click folder → Properties
2. Uncheck "Allow files in this folder to have contents indexed"

## Additional Resources

- **PerCell Documentation**: `/docs` directory
- **GitHub Issues**: [github.com/marcusjoshm/percell/issues](https://github.com/marcusjoshm/percell/issues)
- **ImageJ Documentation**: [imagej.net/software/fiji](https://imagej.net/software/fiji/)
- **Python Windows FAQ**: [docs.python.org/3/faq/windows.html](https://docs.python.org/3/faq/windows.html)

## Getting Help

If you encounter issues:

1. **Check this guide** - Most common issues are covered
2. **Check README.md** - General troubleshooting section
3. **Search GitHub Issues** - Someone may have had the same problem
4. **Create new issue** - Include:
   - Windows version (Win 10/11)
   - Python version
   - Full error message
   - Steps to reproduce

---

**Questions or feedback?** Open an issue on GitHub or start a discussion!
