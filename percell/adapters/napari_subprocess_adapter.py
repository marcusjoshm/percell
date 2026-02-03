from __future__ import annotations

from pathlib import Path
from typing import List, Optional
import subprocess
import sys
import logging

from percell.ports.driven.napari_integration_port import NapariIntegrationPort


logger = logging.getLogger(__name__)


class NapariSubprocessAdapter(NapariIntegrationPort):
    """Adapter that invokes Napari via a Python subprocess.

    Expects a Python interpreter with Napari installed to be available.
    """

    def __init__(self, python_executable: Path) -> None:
        if not python_executable:
            raise ValueError("python_executable must be provided")
        self._python = Path(python_executable)
        logger.info(f"NapariSubprocessAdapter initialized with python path: "
                    f"{self._python}")
        logger.info(f"Python path exists: {self._python.exists()}")

    def launch_viewer(
        self,
        images: Optional[List[Path]] = None,
        masks: Optional[List[Path]] = None,
        working_dir: Optional[Path] = None,
    ) -> None:
        """Launch Napari viewer with optional images and masks.

        Args:
            images: List of image file paths to load as separate layers
            masks: List of mask/label file paths to load as separate layers
            working_dir: Directory to start napari in (for file browser)
        """
        try:
            # Use custom napari launcher script for mask preprocessing
            launcher_script = Path(__file__).parent / "napari_launcher.py"
            cmd = [str(self._python), str(launcher_script)]

            # Add image files
            if images:
                existing_images = [str(img) for img in images if img.exists()]
                if existing_images:
                    cmd.extend(["--images"] + existing_images)

            # Add mask files
            if masks:
                existing_masks = [str(mask) for mask in masks if mask.exists()]
                if existing_masks:
                    cmd.extend(["--masks"] + existing_masks)

            # Add working directory
            if working_dir:
                cmd.extend(["--working-dir", str(working_dir)])

            # Change to working directory if specified
            cwd = str(working_dir) if working_dir else None

            logger.info("Launching Napari viewer")

            # Allow interactive session to inherit terminal IO
            subprocess.run(cmd, stdin=sys.stdin, stdout=sys.stdout,
                          stderr=sys.stderr, cwd=cwd)
            logger.info("Napari viewer closed")

        except Exception as exc:
            logger.error("Error launching Napari viewer: %s", exc)