#!/usr/bin/env python3
"""
Percell Release Script

This script helps with the release process for publishing to PyPI.
It handles version bumping, building, testing, and publishing.
"""

import os
import sys
import subprocess
import argparse
from pathlib import Path
import re


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


def get_current_version():
    """Get the current version from pyproject.toml."""
    with open("pyproject.toml", "r") as f:
        content = f.read()
        match = re.search(r'version = "([^"]+)"', content)
        if match:
            return match.group(1)
    raise ValueError("Could not find version in pyproject.toml")


def update_version(new_version):
    """Update version in pyproject.toml and setup.py."""
    # Update pyproject.toml
    with open("pyproject.toml", "r") as f:
        content = f.read()
    
    content = re.sub(r'version = "[^"]+"', f'version = "{new_version}"', content)
    
    with open("pyproject.toml", "w") as f:
        f.write(content)
    
    # Update setup.py
    with open("setup.py", "r") as f:
        content = f.read()
    
    content = re.sub(r'version="[^"]+"', f'version="{new_version}"', content)
    
    with open("setup.py", "w") as f:
        f.write(content)
    
    print(f"✓ Updated version to {new_version}")


def bump_version(current_version, bump_type):
    """Bump version based on type (major, minor, patch)."""
    parts = current_version.split('.')
    if len(parts) != 3:
        raise ValueError(f"Invalid version format: {current_version}")
    
    major, minor, patch = map(int, parts)
    
    if bump_type == "major":
        major += 1
        minor = 0
        patch = 0
    elif bump_type == "minor":
        minor += 1
        patch = 0
    elif bump_type == "patch":
        patch += 1
    else:
        raise ValueError(f"Invalid bump type: {bump_type}")
    
    return f"{major}.{minor}.{patch}"


def clean_build():
    """Clean previous build artifacts."""
    print("Cleaning previous build artifacts...")
    run_command("rm -rf build/ dist/ *.egg-info/", check=False)
    print("✓ Cleaned build artifacts")


def build_package():
    """Build the package."""
    print("Building package...")
    run_command("python -m build")
    print("✓ Package built successfully")


def check_package():
    """Check the built package."""
    print("Checking package...")
    run_command("twine check dist/*")
    print("✓ Package check passed")


def test_install():
    """Test installing the package."""
    print("Testing package installation...")
    
    # Create a temporary virtual environment
    run_command("python -m venv test_env")
    
    try:
        # Install the package
        if os.name == 'nt':  # Windows
            run_command("test_env\\Scripts\\pip install dist/*.whl")
            run_command("test_env\\Scripts\\percell --help")
        else:  # Unix-like
            run_command("test_env/bin/pip install dist/*.whl")
            run_command("test_env/bin/percell --help")
        
        print("✓ Package installation test passed")
    finally:
        # Clean up test environment
        run_command("rm -rf test_env", check=False)


def publish_to_testpypi():
    """Publish to TestPyPI."""
    print("Publishing to TestPyPI...")
    run_command("twine upload --repository testpypi dist/*")
    print("✓ Published to TestPyPI")
    print("Test installation with: pip install --index-url https://test.pypi.org/simple/ percell")


def publish_to_pypi():
    """Publish to PyPI."""
    print("Publishing to PyPI...")
    run_command("twine upload dist/*")
    print("✓ Published to PyPI")
    print("Users can now install with: pip install percell")


def create_git_tag(version):
    """Create and push a git tag."""
    print(f"Creating git tag v{version}...")
    run_command(f"git add pyproject.toml setup.py")
    run_command(f"git commit -m 'Bump version to {version}'")
    run_command(f"git tag v{version}")
    run_command(f"git push origin main")
    run_command(f"git push origin v{version}")
    print(f"✓ Created and pushed tag v{version}")


def main():
    parser = argparse.ArgumentParser(description="Release Percell package")
    parser.add_argument("--bump", choices=["major", "minor", "patch"], 
                       help="Bump version type")
    parser.add_argument("--version", help="Set specific version")
    parser.add_argument("--test", action="store_true", 
                       help="Publish to TestPyPI only")
    parser.add_argument("--publish", action="store_true", 
                       help="Publish to PyPI")
    parser.add_argument("--no-test", action="store_true", 
                       help="Skip installation test")
    parser.add_argument("--no-tag", action="store_true", 
                       help="Skip git tag creation")
    
    args = parser.parse_args()
    
    print("🚀 Percell Release Script")
    print("=" * 40)
    
    # Get current version
    current_version = get_current_version()
    print(f"Current version: {current_version}")
    
    # Determine new version
    if args.version:
        new_version = args.version
    elif args.bump:
        new_version = bump_version(current_version, args.bump)
    else:
        print("Error: Must specify either --bump or --version")
        sys.exit(1)
    
    print(f"New version: {new_version}")
    
    # Confirm before proceeding
    if not args.publish and not args.test:
        response = input(f"Proceed with version {new_version}? (y/N): ")
        if response.lower() != 'y':
            print("Release cancelled")
            sys.exit(0)
    
    # Update version
    update_version(new_version)
    
    # Clean and build
    clean_build()
    build_package()
    check_package()
    
    # Test installation
    if not args.no_test:
        test_install()
    
    # Create git tag
    if not args.no_tag:
        create_git_tag(new_version)
    
    # Publish
    if args.test:
        publish_to_testpypi()
    elif args.publish:
        publish_to_pypi()
    else:
        print(f"\n✅ Release preparation complete!")
        print(f"Version {new_version} is ready for release.")
        print(f"To publish to TestPyPI: python release.py --test")
        print(f"To publish to PyPI: python release.py --publish")


if __name__ == "__main__":
    main()
