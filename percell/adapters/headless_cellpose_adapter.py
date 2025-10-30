"""
Headless Cellpose Adapter

Adapter that runs Cellpose segmentation in headless mode (no GUI)
and generates ImageJ-formatted ROI files directly.
"""

from __future__ import annotations

import logging
import subprocess
import sys
from pathlib import Path
from typing import List, Optional

from percell.domain.exceptions import CellposeError
from percell.domain.models import SegmentationParameters
from percell.ports.driven.cellpose_integration_port import CellposeIntegrationPort


logger = logging.getLogger(__name__)


class HeadlessCellposeAdapter(CellposeIntegrationPort):
    """
    Adapter that runs Cellpose in headless mode using the custom script.

    This adapter:
    1. Runs Cellpose segmentation without GUI
    2. Generates masks and ImageJ ROI files automatically
    3. Supports all standard Cellpose parameters
    4. Can use GPU acceleration if available
    """

    def __init__(
        self,
        python_executable: Path,
        script_path: Optional[Path] = None,
    ) -> None:
        """
        Initialize the headless Cellpose adapter.

        Args:
            python_executable: Path to Python interpreter with cellpose installed
            script_path: Path to headless_cellpose_segmentation.py script.
                        If None, auto-discovers from package location.
        """
        if not python_executable:
            raise ValueError("python_executable must be provided")

        self._python = Path(python_executable)

        if script_path is None:
            # Auto-discover script location
            from percell import __file__ as package_init
            package_dir = Path(package_init).parent
            script_path = package_dir / "scripts" / "headless_cellpose_segmentation.py"

        self._script_path = Path(script_path)

        logger.info(
            f"HeadlessCellposeAdapter initialized with python: {self._python}"
        )
        logger.info(f"Script path: {self._script_path}")
        logger.info(f"Python exists: {self._python.exists()}")
        logger.info(f"Script exists: {self._script_path.exists()}")

    def run_segmentation(
        self,
        images: List[Path],
        output_dir: Path,
        params: SegmentationParameters,
        gpu: bool = False,
        min_area: int = 10,
        save_masks: bool = True,
    ) -> List[Path]:
        """
        Run headless Cellpose segmentation on images.

        Args:
            images: List of image paths to segment
            output_dir: Directory to save masks and ROIs
            params: Segmentation parameters (diameter, thresholds, model)
            gpu: Use GPU acceleration if available
            min_area: Minimum ROI area in pixels
            save_masks: Save segmentation masks as TIFF files

        Returns:
            List of paths to generated ROI zip files

        Raises:
            CellposeError: If segmentation fails
        """
        if not self._script_path.exists():
            raise CellposeError(
                f"Headless segmentation script not found: {self._script_path}"
            )

        if not images:
            logger.warning("No images provided for segmentation")
            return []

        output_dir.mkdir(parents=True, exist_ok=True)

        # Group images by parent directory to maintain structure
        images_by_dir = {}
        for img in images:
            parent = img.parent
            if parent not in images_by_dir:
                images_by_dir[parent] = []
            images_by_dir[parent].append(img)

        generated_rois: List[Path] = []

        # Process each directory
        for input_dir, dir_images in images_by_dir.items():
            logger.info(
                f"Processing {len(dir_images)} images from {input_dir.name}"
            )

            # Save ROIs in the SAME directory as the input images
            # (not in a separate output directory)
            # This matches the expected workflow where ROIs live next to binned images
            logger.info(f"ROIs will be saved in: {input_dir}")

            # Build command
            cmd = [
                str(self._python),
                str(self._script_path),
                "--input_dir", str(input_dir),
                "--output_dir", str(input_dir),  # Save in same dir as inputs
                "--model_type", params.model_type,
                "--diameter", str(params.cell_diameter),
                "--flow_threshold", str(params.flow_threshold),
                "--cellprob_threshold", str(params.probability_threshold),
                "--min_area", str(min_area),
            ]

            if gpu:
                cmd.append("--gpu")

            if not save_masks:
                cmd.append("--no_save_masks")

            logger.info(f"Running headless Cellpose: {' '.join(cmd[:6])}...")

            try:
                # Run the script
                proc = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    check=False,
                )

                if proc.returncode != 0:
                    logger.error(
                        f"Headless Cellpose failed for {input_dir.name}: "
                        f"{proc.stderr}"
                    )
                    continue

                # Log output
                if proc.stdout:
                    for line in proc.stdout.splitlines():
                        if "Successfully" in line or "Found" in line:
                            logger.info(line)

                # Collect generated ROI files from the input directory
                roi_files = list(input_dir.glob("*_rois.zip"))
                generated_rois.extend(roi_files)
                logger.info(f"Generated {len(roi_files)} ROI files")

            except Exception as exc:
                error_msg = f"Error running headless Cellpose: {exc}"
                logger.error(error_msg)
                raise CellposeError(error_msg) from exc

        logger.info(f"Total ROI files generated: {len(generated_rois)}")
        return generated_rois

    def check_dependencies(self) -> bool:
        """
        Check if all dependencies are available.

        Returns:
            True if all dependencies are installed, False otherwise
        """
        try:
            # Check if Python executable exists
            if not self._python.exists():
                logger.error(f"Python executable not found: {self._python}")
                return False

            # Check if script exists
            if not self._script_path.exists():
                logger.error(f"Script not found: {self._script_path}")
                return False

            # Check if cellpose is installed
            cmd = [
                str(self._python),
                "-c",
                "import cellpose, roifile, skimage, tifffile"
            ]
            proc = subprocess.run(cmd, capture_output=True, check=False)

            if proc.returncode != 0:
                logger.error(
                    "Missing dependencies. Install with: "
                    "pip install cellpose roifile scikit-image tifffile"
                )
                return False

            return True

        except Exception as e:
            logger.error(f"Error checking dependencies: {e}")
            return False
