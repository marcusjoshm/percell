"""
Cross-platform path utilities for percell

This module provides platform-aware path handling to support Windows, macOS, and Linux.
"""
import os
import platform
from pathlib import Path
from typing import Optional


def get_platform() -> str:
    """
    Return the current platform name.

    Returns:
        str: 'Windows', 'Darwin' (macOS), or 'Linux'
    """
    return platform.system()


def is_windows() -> bool:
    """
    Check if running on Windows.

    Returns:
        bool: True if on Windows, False otherwise
    """
    return get_platform() == 'Windows'


def is_mac() -> bool:
    """
    Check if running on macOS.

    Returns:
        bool: True if on macOS, False otherwise
    """
    return get_platform() == 'Darwin'


def is_linux() -> bool:
    """
    Check if running on Linux.

    Returns:
        bool: True if on Linux, False otherwise
    """
    return get_platform() == 'Linux'


def get_venv_activate_path(venv_name: str = "venv") -> Path:
    """
    Get the virtual environment activation script path for the current platform.

    Args:
        venv_name: Name of the virtual environment directory (default: "venv")

    Returns:
        Path: Path to the activation script

    Examples:
        Windows: venv/Scripts/activate.bat
        Unix: venv/bin/activate
    """
    venv_path = Path(venv_name)

    if is_windows():
        return venv_path / 'Scripts' / 'activate.bat'
    else:
        return venv_path / 'bin' / 'activate'


def get_venv_python(venv_name: str = "venv") -> Path:
    """
    Get the virtual environment Python executable path for the current platform.

    Args:
        venv_name: Name of the virtual environment directory (default: "venv")

    Returns:
        Path: Path to the Python executable

    Examples:
        Windows: venv/Scripts/python.exe
        Unix: venv/bin/python
    """
    venv_path = Path(venv_name)

    if is_windows():
        return venv_path / 'Scripts' / 'python.exe'
    else:
        return venv_path / 'bin' / 'python'


def get_user_home() -> Path:
    """
    Get user home directory in a cross-platform way.

    Returns:
        Path: Path to the user's home directory
    """
    return Path.home()


def normalize_path(path_str: str | Path) -> str:
    """
    Normalize path for the current platform.

    Converts path to use the appropriate separators for the current OS.

    Args:
        path_str: Path to normalize (string or Path object)

    Returns:
        str: Normalized path string
    """
    return str(Path(path_str))


def find_imagej() -> Optional[Path]:
    """
    Find ImageJ/Fiji installation path on the current platform.

    Searches common installation locations for ImageJ or Fiji.

    Returns:
        Path: Path to ImageJ/Fiji installation if found, None otherwise
    """
    possible_paths = []

    if is_windows():
        # Windows common installation locations
        possible_paths.extend([
            # Fiji installations
            Path('C:/Program Files/Fiji.app'),
            Path('C:/Program Files (x86)/Fiji.app'),
            Path('C:/Fiji.app'),
            Path(os.environ.get('LOCALAPPDATA', '')) / 'Fiji.app',
            Path(os.environ.get('PROGRAMFILES', 'C:/Program Files')) / 'Fiji.app',
            Path(os.environ.get('PROGRAMFILES(X86)', 'C:/Program Files (x86)')) / 'Fiji.app',
            Path.home() / 'Fiji.app',
            # ImageJ installations
            Path('C:/Program Files/ImageJ'),
            Path('C:/Program Files (x86)/ImageJ'),
            Path(os.environ.get('PROGRAMFILES', 'C:/Program Files')) / 'ImageJ',
            Path.home() / 'ImageJ',
        ])
    elif is_mac():
        # macOS common installation locations
        possible_paths.extend([
            # Fiji installations
            Path('/Applications/Fiji.app'),
            Path.home() / 'Applications/Fiji.app',
            # ImageJ installations
            Path('/Applications/ImageJ.app'),
            Path.home() / 'Applications/ImageJ.app',
            Path('/Applications/ImageJ'),
            Path.home() / 'Applications/ImageJ',
        ])
    else:  # Linux
        # Linux common installation locations
        possible_paths.extend([
            # Fiji installations
            Path('/opt/Fiji.app'),
            Path.home() / 'Fiji.app',
            Path('/usr/local/Fiji.app'),
            Path.home() / 'opt/Fiji.app',
            # ImageJ installations
            Path('/opt/ImageJ'),
            Path.home() / 'ImageJ',
            Path('/usr/local/ImageJ'),
            Path.home() / 'opt/ImageJ',
        ])

    # Search for existing paths
    for path in possible_paths:
        if path.exists():
            return path

    return None


def get_imagej_executable() -> Optional[Path]:
    """
    Get the ImageJ executable path for the current platform.

    Returns:
        Path: Path to ImageJ executable if found, None otherwise
    """
    imagej_base = find_imagej()

    if not imagej_base:
        return None

    if is_windows():
        # Windows executable patterns
        possible_exes = [
            imagej_base / 'ImageJ-win64.exe',
            imagej_base / 'ImageJ-win32.exe',
            imagej_base / 'ImageJ.exe',
        ]
    elif is_mac():
        # macOS executable patterns
        possible_exes = [
            imagej_base / 'Contents/MacOS/ImageJ-macosx',
            imagej_base / 'Contents/MacOS/ImageJ',
        ]
    else:  # Linux
        # Linux executable patterns
        possible_exes = [
            imagej_base / 'ImageJ-linux64',
            imagej_base / 'ImageJ-linux32',
            imagej_base / 'ImageJ',
        ]

    # Find first existing executable
    for exe in possible_exes:
        if exe.exists():
            return exe

    return None


def get_venv_scripts_dir(venv_name: str = "venv") -> Path:
    """
    Get the scripts/bin directory for the virtual environment.

    Args:
        venv_name: Name of the virtual environment directory (default: "venv")

    Returns:
        Path: Path to Scripts (Windows) or bin (Unix) directory
    """
    venv_path = Path(venv_name)

    if is_windows():
        return venv_path / 'Scripts'
    else:
        return venv_path / 'bin'
