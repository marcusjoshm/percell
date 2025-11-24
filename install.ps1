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
    Write-Host ""
    Write-Host "Download from: https://www.python.org/downloads/" -ForegroundColor Yellow
    Write-Host ""
    Read-Host "Press Enter to exit"
    exit 1
}

Write-Host ""

# Create virtual environment
Write-Host "Creating virtual environment..." -ForegroundColor Yellow
python -m venv venv
if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: Failed to create virtual environment" -ForegroundColor Red
    Read-Host "Press Enter to exit"
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
    Write-Host "Installing dependencies from requirements.txt..." -ForegroundColor Yellow
    pip install -r requirements.txt
} else {
    Write-Host "Warning: requirements.txt not found, skipping..." -ForegroundColor Yellow
}

# Install package in development mode
Write-Host "Installing percell in development mode..." -ForegroundColor Yellow
pip install -e .

# Run Python setup script
if (Test-Path "percell\setup\install_windows.py") {
    Write-Host "Configuring percell for Windows..." -ForegroundColor Yellow
    python percell\setup\install_windows.py
} else {
    Write-Host "Warning: Windows setup script not found, skipping platform-specific configuration..." -ForegroundColor Yellow
}

Write-Host ""
Write-Host "===============================================" -ForegroundColor Green
Write-Host "Installation complete!" -ForegroundColor Green
Write-Host "===============================================" -ForegroundColor Green
Write-Host ""
Write-Host "To use percell:" -ForegroundColor Cyan
Write-Host "1. Activate the virtual environment: .\venv\Scripts\Activate" -ForegroundColor White
Write-Host "2. Run: python -m percell.main.main" -ForegroundColor White
Write-Host ""
Write-Host "Or use the launcher script: .\percell.bat" -ForegroundColor White
Write-Host ""
Read-Host "Press Enter to exit"
