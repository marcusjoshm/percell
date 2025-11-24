#!/usr/bin/env python
"""
Launch Napari Viewer - Cross-Platform Version

This script launches Napari for interactive image visualization and analysis.
Replaces the bash script with a cross-platform Python implementation.
"""
import os
import sys
import subprocess
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from percell.utils.path_utils import get_venv_python


class NapariLauncher:
    """Handles launching Napari viewer."""

    def __init__(self, images_dir: str | Path = None):
        """
        Initialize the launcher.

        Args:
            images_dir: Optional path to images directory to open
        """
        self.images_dir = Path(images_dir) if images_dir else None
        self.workspace_dir = Path.cwd()
        self.napari_env = self.workspace_dir / "venv"

    def handle_error(self, message: str):
        """Handle errors by printing message and exiting."""
        print(f"Error: {message}", file=sys.stderr)
        sys.exit(1)

    def get_napari_python(self) -> Path:
        """
        Get the Python executable from the Napari virtual environment.

        Returns:
            Path to Python executable in environment

        Raises:
            SystemExit if environment not found
        """
        if not self.napari_env.exists():
            self.handle_error(
                f"Virtual environment not found at {self.napari_env}\n"
                f"Please create it with:\n"
                f"  python -m venv {self.napari_env}\n"
                f"  {get_venv_python(str(self.napari_env.name))} -m pip install napari[all]"
            )

        python_exe = get_venv_python(str(self.napari_env.name))

        if not python_exe.exists():
            self.handle_error(
                f"Python executable not found in environment: {python_exe}"
            )

        return python_exe

    def check_and_install_napari(self, python_exe: Path):
        """
        Check if napari is installed, and install if missing.

        Args:
            python_exe: Path to Python executable
        """
        # Check if napari is installed
        check_cmd = [str(python_exe), "-c", "import napari"]

        try:
            result = subprocess.run(
                check_cmd,
                capture_output=True,
                text=True,
                timeout=10
            )

            if result.returncode == 0:
                print("✓ napari is already installed")
                return

        except subprocess.TimeoutExpired:
            print("Warning: Timeout checking napari, will attempt to install")

        # napari not found, install it
        print("Installing napari...")
        install_cmd = [str(python_exe), "-m", "pip", "install", "napari[all]"]

        try:
            subprocess.run(install_cmd, check=True)
            print("✓ napari installed successfully")
        except subprocess.CalledProcessError as e:
            self.handle_error(f"Failed to install napari: {e}")

    def print_instructions(self):
        """Print user instructions."""
        separator = "=" * 75
        print(f"\n{separator}\n")
        print("Napari is now running for interactive image visualization and analysis.")
        print()
        print("Key features:")
        print("1. Load images: File > Open Files or drag and drop")
        print("2. View multi-dimensional data with layer controls")
        print("3. Overlay labels/masks for segmentation analysis")
        print("4. Use plugins for specialized analysis workflows")
        print("5. Interactive measurements and annotations")
        print()
        print("When finished with visualization, close the Napari window to continue...")
        print(f"\n{separator}\n")

    def launch_napari(self):
        """Launch Napari viewer."""
        print("Launching Napari for interactive image visualization...")

        if self.images_dir:
            if not self.images_dir.exists():
                print(f"Warning: Images directory does not exist: {self.images_dir}")
                print("Launching Napari without specific directory...")
                self.images_dir = None
            else:
                print(f"Images directory: {self.images_dir}")

        # Get Python executable
        napari_python = self.get_napari_python()

        # Check and install napari
        self.check_and_install_napari(napari_python)

        # Print instructions
        self.print_instructions()

        # Start Napari viewer
        print("Starting Napari viewer...")

        # Build command
        napari_cmd = [str(napari_python), "-m", "napari"]

        # Add images directory if specified
        if self.images_dir:
            napari_cmd.append(str(self.images_dir))

        try:
            # Launch Napari (runs in foreground)
            result = subprocess.run(napari_cmd)

            if result.returncode != 0:
                self.handle_error("Napari exited with an error")

            print("Napari viewer closed. Continuing workflow...")

        except KeyboardInterrupt:
            print("\nNapari interrupted by user")
            sys.exit(0)
        except Exception as e:
            self.handle_error(f"Failed to start Napari: {e}")

    def run(self):
        """Main execution flow."""
        self.launch_napari()


def main():
    """Main entry point."""
    images_dir = None

    if len(sys.argv) > 1:
        images_dir = sys.argv[1]

    launcher = NapariLauncher(images_dir)
    launcher.run()


if __name__ == "__main__":
    main()
