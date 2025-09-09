#!/usr/bin/env python3
"""
Percell Package Installation Script

This script provides an easy way to install the percell package from the built distribution.
It handles both local installation and global installation options.
"""

import os
import sys
import subprocess
import argparse
from pathlib import Path


def run_command(cmd, check=True, capture_output=False):
    """Run a command and handle errors."""
    try:
        if capture_output:
            result = subprocess.run(cmd, shell=True, check=check, 
                                  capture_output=True, text=True)
            return result.stdout.strip()
        else:
            subprocess.run(cmd, shell=True, check=check)
            return None
    except subprocess.CalledProcessError as e:
        print(f"Error running command: {cmd}")
        print(f"Error: {e}")
        if capture_output and e.stdout:
            print(f"Output: {e.stdout}")
        if capture_output and e.stderr:
            print(f"Error output: {e.stderr}")
        sys.exit(1)


def check_python_version():
    """Check if Python version is compatible."""
    if sys.version_info < (3, 8):
        print("Error: Percell requires Python 3.8 or higher")
        print(f"Current version: {sys.version}")
        sys.exit(1)
    print(f"✓ Python version: {sys.version.split()[0]}")


def find_distribution_files():
    """Find the built distribution files."""
    dist_dir = Path("dist")
    if not dist_dir.exists():
        print("Error: No 'dist' directory found. Please run 'python -m build' first.")
        sys.exit(1)
    
    wheel_files = list(dist_dir.glob("*.whl"))
    if not wheel_files:
        print("Error: No wheel files found in dist/ directory")
        sys.exit(1)
    
    # Use the most recent wheel file
    wheel_file = max(wheel_files, key=lambda x: x.stat().st_mtime)
    print(f"✓ Found distribution file: {wheel_file}")
    return wheel_file


def install_package(wheel_file, user=False, editable=False):
    """Install the package."""
    if editable:
        print("Installing in editable mode from source...")
        cmd = f"pip install -e ."
    else:
        print(f"Installing from wheel: {wheel_file}")
        cmd = f"pip install {wheel_file}"
    
    if user:
        cmd += " --user"
    
    print(f"Running: {cmd}")
    run_command(cmd)
    print("✓ Package installed successfully!")


def verify_installation():
    """Verify that the installation worked."""
    print("\nVerifying installation...")
    
    # Check if percell command is available
    try:
        result = run_command("which percell", capture_output=True)
        print(f"✓ Percell command found at: {result}")
    except:
        print("⚠ Warning: percell command not found in PATH")
        print("You may need to add the installation directory to your PATH")
    
    # Test the command
    try:
        result = run_command("percell --help", capture_output=True)
        if "Microscopy Per Cell Analysis Pipeline" in result:
            print("✓ Percell command is working correctly!")
        else:
            print("⚠ Warning: percell command output unexpected")
    except:
        print("⚠ Warning: Could not run percell command")


def main():
    parser = argparse.ArgumentParser(description="Install Percell package")
    parser.add_argument("--user", action="store_true", 
                       help="Install for current user only")
    parser.add_argument("--editable", "-e", action="store_true",
                       help="Install in editable mode from source")
    parser.add_argument("--no-verify", action="store_true",
                       help="Skip installation verification")
    
    args = parser.parse_args()
    
    print("🔬 Percell Package Installer")
    print("=" * 40)
    
    # Check Python version
    check_python_version()
    
    # Find distribution files (unless editable mode)
    if not args.editable:
        wheel_file = find_distribution_files()
    else:
        wheel_file = None
    
    # Install the package
    install_package(wheel_file, user=args.user, editable=args.editable)
    
    # Verify installation
    if not args.no_verify:
        verify_installation()
    
    print("\n🎉 Installation complete!")
    print("\nYou can now run 'percell' from any directory.")
    print("Try: percell --help")


if __name__ == "__main__":
    main()
