#!/usr/bin/env python
"""
Launch Segmentation Tools - Cross-Platform Version

This script launches both Cellpose and ImageJ for interactive segmentation work.
Replaces the bash script with a cross-platform Python implementation.
"""
import os
import sys
import subprocess
import time
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from percell.utils.path_utils import (
    is_windows,
    get_venv_python,
    get_imagej_executable,
)


class SegmentationToolsLauncher:
    """Handles launching ImageJ and Cellpose for interactive segmentation."""

    def __init__(self, preprocessed_dir: str | Path):
        """
        Initialize the launcher.

        Args:
            preprocessed_dir: Path to the preprocessed images directory
        """
        self.preprocessed_dir = Path(preprocessed_dir)
        self.workspace_dir = Path.cwd()
        self.cellpose_env = self.workspace_dir / "cellpose_venv"
        self.imagej_path = None
        self.imagej_process = None
        self.cellpose_process = None

    def handle_error(self, message: str):
        """Handle errors by printing message and exiting."""
        print(f"Error: {message}", file=sys.stderr)
        sys.exit(1)

    def find_imagej(self) -> Path:
        """
        Find ImageJ executable.

        Returns:
            Path to ImageJ executable

        Raises:
            SystemExit if ImageJ not found
        """
        imagej_exe = get_imagej_executable()

        if imagej_exe:
            return imagej_exe

        self.handle_error(
            "ImageJ/Fiji not found. Please install Fiji from https://fiji.sc/ "
            "or set the path in your configuration file."
        )

    def get_cellpose_python(self) -> Path:
        """
        Get the Python executable from the Cellpose virtual environment.

        Returns:
            Path to Python executable in Cellpose environment

        Raises:
            SystemExit if environment not found
        """
        if not self.cellpose_env.exists():
            self.handle_error(
                f"Cellpose virtual environment not found at {self.cellpose_env}\n"
                f"Please create it with:\n"
                f"  python -m venv {self.cellpose_env}\n"
                f"  {get_venv_python(self.cellpose_env)} -m pip install cellpose[gui]"
            )

        python_exe = get_venv_python(str(self.cellpose_env.name))

        if not python_exe.exists():
            self.handle_error(
                f"Python executable not found in Cellpose environment: {python_exe}"
            )

        return python_exe

    def check_and_install_package(self, python_exe: Path, package: str, version: str = None):
        """
        Check if a package is installed, and install if missing.

        Args:
            python_exe: Path to Python executable
            package: Package name to check/install
            version: Optional specific version (e.g., "4.0.4")
        """
        # Check if package is installed
        check_cmd = [str(python_exe), "-c", f"import {package}"]

        try:
            result = subprocess.run(
                check_cmd,
                capture_output=True,
                text=True,
                timeout=10
            )

            if result.returncode == 0:
                print(f"✓ {package} is already installed")
                return
            else:
                # Check if it's just a NumPy compatibility warning
                if "numpy" in result.stderr and "compatibility" in result.stderr:
                    print(f"✓ {package} detected with NumPy compatibility warning - this is normal")
                    return

        except subprocess.TimeoutExpired:
            print(f"Warning: Timeout checking {package}, will attempt to install")

        # Package not found, install it
        print(f"Installing {package}...")
        package_spec = f"{package}=={version}" if version else package

        install_cmd = [str(python_exe), "-m", "pip", "install", package_spec]

        try:
            subprocess.run(install_cmd, check=True)
            print(f"✓ {package} installed successfully")
        except subprocess.CalledProcessError as e:
            self.handle_error(f"Failed to install {package}: {e}")

    def launch_imagej(self):
        """Launch ImageJ in the background."""
        print("Starting ImageJ...")

        self.imagej_path = self.find_imagej()

        try:
            # On Windows, we need to handle the executable differently
            if is_windows():
                # Use CREATE_NEW_PROCESS_GROUP to allow it to run independently
                self.imagej_process = subprocess.Popen(
                    [str(self.imagej_path)],
                    creationflags=subprocess.CREATE_NEW_PROCESS_GROUP
                )
            else:
                self.imagej_process = subprocess.Popen([str(self.imagej_path)])

            # Give ImageJ a moment to start
            time.sleep(2)

            # Check if it's still running
            if self.imagej_process.poll() is not None:
                self.handle_error("ImageJ failed to start")

            print(f"✓ ImageJ launched (PID: {self.imagej_process.pid})")

        except Exception as e:
            self.handle_error(f"Failed to start ImageJ: {e}")

    def launch_cellpose(self):
        """Launch Cellpose GUI in the background."""
        print("Starting Cellpose GUI...")

        # Get Cellpose Python executable
        cellpose_python = self.get_cellpose_python()

        # Check and install dependencies
        self.check_and_install_package(cellpose_python, "numpy")
        self.check_and_install_package(cellpose_python, "cellpose", "4.0.4")

        try:
            # Launch Cellpose GUI
            cellpose_cmd = [str(cellpose_python), "-m", "cellpose"]

            if is_windows():
                # On Windows, use CREATE_NEW_PROCESS_GROUP
                self.cellpose_process = subprocess.Popen(
                    cellpose_cmd,
                    creationflags=subprocess.CREATE_NEW_PROCESS_GROUP
                )
            else:
                self.cellpose_process = subprocess.Popen(cellpose_cmd)

            # Give Cellpose a moment to start
            time.sleep(2)

            # Check if it's still running
            if self.cellpose_process.poll() is not None:
                self.handle_error("Cellpose failed to start")

            print(f"✓ Cellpose GUI launched (PID: {self.cellpose_process.pid})")

        except Exception as e:
            # Clean up ImageJ if Cellpose fails
            if self.imagej_process:
                self.cleanup()
            self.handle_error(f"Failed to start Cellpose: {e}")

    def print_instructions(self):
        """Print user instructions."""
        separator = "=" * 75
        print(f"\n{separator}\n")
        print("Cellpose and FIJI are now running. Please follow these steps:")
        print()
        print("In Cellpose:")
        print(f"1. Navigate to: {self.preprocessed_dir}")
        print("2. Open and segment your images")
        print("3. Save segmentations as .zip files in the same directory")
        print()
        print("In FIJI:")
        print("1. Open the same images for comparison if needed")
        print("2. Use the ROI Manager to view and adjust segmentations")
        print("3. Save any modified ROIs")
        print()
        print("When finished with both applications, press Enter to continue the workflow...")
        print(f"\n{separator}\n")

    def wait_for_user(self):
        """Wait for user to press Enter."""
        try:
            input()
        except KeyboardInterrupt:
            print("\nInterrupted by user")

    def cleanup(self):
        """Close background processes."""
        print("Closing Cellpose and FIJI...")

        if self.cellpose_process:
            try:
                self.cellpose_process.terminate()
                self.cellpose_process.wait(timeout=5)
                print("✓ Cellpose closed")
            except subprocess.TimeoutExpired:
                self.cellpose_process.kill()
                print("✓ Cellpose force-closed")
            except Exception as e:
                print(f"Warning: Error closing Cellpose: {e}")

        if self.imagej_process:
            try:
                self.imagej_process.terminate()
                self.imagej_process.wait(timeout=5)
                print("✓ ImageJ closed")
            except subprocess.TimeoutExpired:
                self.imagej_process.kill()
                print("✓ ImageJ force-closed")
            except Exception as e:
                print(f"Warning: Error closing ImageJ: {e}")

    def run(self):
        """Main execution flow."""
        print("Launching segmentation tools for interactive cell segmentation...")
        print(f"Preprocessed images directory: {self.preprocessed_dir}")
        print()

        # Launch both tools
        self.launch_imagej()
        self.launch_cellpose()

        # Print instructions
        self.print_instructions()

        # Wait for user
        self.wait_for_user()

        # Cleanup
        self.cleanup()

        print("Segmentation tools closed. Continuing workflow...")


def main():
    """Main entry point."""
    if len(sys.argv) != 2:
        print("Usage: python launch_segmentation_tools.py <preprocessed_directory>")
        sys.exit(1)

    preprocessed_dir = sys.argv[1]

    if not Path(preprocessed_dir).exists():
        print(f"Error: Preprocessed directory does not exist: {preprocessed_dir}")
        sys.exit(1)

    launcher = SegmentationToolsLauncher(preprocessed_dir)
    launcher.run()


if __name__ == "__main__":
    main()
