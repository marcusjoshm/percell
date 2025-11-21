"""Filesystem filtering utilities for handling cross-platform compatibility.

This module provides utilities to filter out unwanted files created by different
operating systems or filesystems, particularly those created by macOS on exFAT volumes.

When macOS writes to non-native filesystems like exFAT, it creates hidden metadata files
with a ._ prefix to store extended attributes and resource forks. These files should be
ignored during data processing.
"""

from pathlib import Path
from typing import List, Iterable, TypeVar, Union

T = TypeVar('T', Path, str)


def is_exfat_metadata_file(path: Union[str, Path]) -> bool:
    """Check if a file is an exFAT metadata file created by macOS.

    MacOS creates hidden "._" files on non-native filesystems (like exFAT)
    to store extended attributes and resource forks.

    Args:
        path: Path to check (can be string or Path object)

    Returns:
        True if the file is an exFAT metadata file, False otherwise

    Examples:
        >>> is_exfat_metadata_file("._myfile.tif")
        True
        >>> is_exfat_metadata_file("myfile.tif")
        False
        >>> is_exfat_metadata_file("/path/to/._myfile.tif")
        True
    """
    name = Path(path).name
    return name.startswith('._')


def is_macos_metadata_directory(path: Union[str, Path]) -> bool:
    """Check if a directory is a macOS metadata directory.

    Checks for common macOS metadata directories like __MACOSX.

    Args:
        path: Path to check (can be string or Path object)

    Returns:
        True if the directory is a macOS metadata directory, False otherwise

    Examples:
        >>> is_macos_metadata_directory("__MACOSX")
        True
        >>> is_macos_metadata_directory("mydir")
        False
    """
    name = Path(path).name
    return name == '__MACOSX'


def is_system_hidden_file(path: Union[str, Path]) -> bool:
    """Check if a file should be filtered out due to being a system/hidden file.

    This includes:
    - exFAT metadata files (._ prefix)
    - macOS metadata directories (__MACOSX)

    Args:
        path: Path to check (can be string or Path object)

    Returns:
        True if the file should be filtered out, False otherwise

    Examples:
        >>> is_system_hidden_file("._myfile.tif")
        True
        >>> is_system_hidden_file("__MACOSX/resource")
        True
        >>> is_system_hidden_file("myfile.tif")
        False
    """
    # Filter out exFAT metadata files
    if is_exfat_metadata_file(path):
        return True

    # Filter out macOS metadata directories
    if is_macos_metadata_directory(path):
        return True

    return False


def filter_system_files(paths: Iterable[T]) -> List[T]:
    """Filter out system metadata files from a collection of paths.

    Args:
        paths: Iterable of paths (can be strings or Path objects)

    Returns:
        List of paths with system metadata files filtered out

    Examples:
        >>> paths = [Path("file1.tif"), Path("._file1.tif"), Path("file2.tif")]
        >>> filtered = filter_system_files(paths)
        >>> len(filtered)
        2
    """
    return [p for p in paths if not is_system_hidden_file(p)]


def filter_exfat_metadata_files(paths: Iterable[T]) -> List[T]:
    """Filter out exFAT metadata files from a collection of paths.

    This is an alias for filter_system_files for backwards compatibility
    and semantic clarity when specifically dealing with exFAT issues.

    Args:
        paths: Iterable of paths (can be strings or Path objects)

    Returns:
        List of paths with exFAT metadata files filtered out

    Examples:
        >>> paths = ["file1.tif", "._file1.tif", "file2.tif"]
        >>> filtered = filter_exfat_metadata_files(paths)
        >>> len(filtered)
        2
    """
    return filter_system_files(paths)
