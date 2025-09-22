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
            cmd = [str(self._python), "-m", "napari"]

            # Add all image files as separate image layers
            if images:
                for img in images:
                    if img.exists():
                        cmd.append(str(img))
                        logger.info(f"Adding image layer: {img.name}")

            # Add all mask files as separate image layers (not labels)
            if masks:
                for mask in masks:
                    if mask.exists():
                        cmd.append(str(mask))
                        logger.info(f"Adding mask layer: {mask.name}")

            # Change to working directory if specified
            cwd = str(working_dir) if working_dir else None

            logger.info("Launching Napari viewer with command: %s", " ".join(cmd))
            logger.info("Working directory: %s", cwd)
            logger.info("Total files to load: images=%d, masks=%d",
                       len(images) if images else 0, len(masks) if masks else 0)

            # Allow interactive session to inherit terminal IO
            result = subprocess.run(cmd, stdin=sys.stdin, stdout=sys.stdout,
                                  stderr=sys.stderr, cwd=cwd)
            logger.info("Napari subprocess completed with return code: %d", result.returncode)

        except Exception as exc:
            logger.error("Error launching Napari viewer: %s", exc)