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
    echo.
    echo Download from: https://www.python.org/downloads/
    pause
    exit /b 1
)

echo Python found:
python --version
echo.

REM Create virtual environment
echo Creating virtual environment...
python -m venv venv
if errorlevel 1 (
    echo ERROR: Failed to create virtual environment
    pause
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
    echo Installing dependencies from requirements.txt...
    pip install -r requirements.txt
) else (
    echo Warning: requirements.txt not found, skipping...
)

REM Install package in development mode
echo Installing percell in development mode...
pip install -e .

REM Run Python setup script
if exist percell\setup\install_windows.py (
    echo Configuring percell for Windows...
    python percell\setup\install_windows.py
) else (
    echo Warning: Windows setup script not found, skipping platform-specific configuration...
)

echo.
echo ===============================================
echo Installation complete!
echo ===============================================
echo.
echo To use percell:
echo 1. Activate the virtual environment: venv\Scripts\activate
echo 2. Run: python -m percell.main.main
echo.
echo Or use the launcher script: percell.bat
echo.
pause
