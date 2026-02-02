from __future__ import annotations

from pathlib import Path
from typing import List, Optional
import subprocess
import sys
import logging
import tempfile
import shutil

from percell.ports.driven.cellpose_integration_port import (
    CellposeIntegrationPort,
)
from percell.domain.models import SegmentationParameters
from percell.domain.exceptions import CellposeError, FileSystemError


logger = logging.getLogger(__name__)


class CellposeSubprocessAdapter(CellposeIntegrationPort):
    """Adapter that invokes Cellpose via a Python subprocess.

    Expects a Python interpreter with Cellpose installed to be available.
    """

    def __init__(self, python_executable: Path) -> None:
        if not python_executable:
            raise ValueError("python_executable must be provided")
        self._python = Path(python_executable)
        logger.info(
            (
                f"CellposeSubprocessAdapter initialized with python path: "
                f"{self._python}"
            )
        )
        logger.info(f"Python path exists: {self._python.exists()}")

    def _launch_gui(self) -> None:
        """Launch the interactive Cellpose GUI."""
        cmd = [str(self._python), "-m", "cellpose"]
        logger.info("Launching Cellpose GUI: %s", " ".join(cmd))
        subprocess.run(
            cmd, stdin=sys.stdin, stdout=sys.stdout, stderr=sys.stderr
        )

    def _copy_image_to_temp(self, img: Path, tmp_img: Path) -> None:
        """Copy image to temporary directory, falling back to basic copy if needed."""
        try:
            shutil.copy2(img, tmp_img)
        except (OSError, IOError):
            shutil.copy(img, tmp_img)

    def _build_cellpose_command(
        self, tmpdir_path: Path, params: SegmentationParameters
    ) -> List[str]:
        """Build the Cellpose command line arguments."""
        return [
            str(self._python),
            "-m",
            "cellpose",
            "--dir", str(tmpdir_path),
            "--pretrained_model", params.model_type,
            "--diameter", str(params.cell_diameter),
            "--savedir", str(tmpdir_path),
            "--save_tif",
            "--no_npy",
            "--chan", "0",
            "--chan2", "0",
        ]

    def _find_mask_candidates(self, search_dir: Path, img_stem: str) -> List[Path]:
        """Find mask file candidates in a directory."""
        candidates = []
        candidates.extend(search_dir.glob(f"{img_stem}*mask*.tif*"))
        candidates.extend(search_dir.glob(f"{img_stem}*masks*.tif*"))
        candidates.extend(search_dir.glob(f"{img_stem}*seg*.tif*"))
        return list(candidates)

    def _move_mask_to_output(
        self, mask_src: Path, output_dir: Path, img_stem: str
    ) -> Optional[Path]:
        """Move or copy mask file to output directory."""
        output_dir.mkdir(parents=True, exist_ok=True)
        mask_dst = output_dir / f"{img_stem}_mask.tif"
        try:
            shutil.move(str(mask_src), str(mask_dst))
        except Exception:
            shutil.copy2(str(mask_src), str(mask_dst))
        return mask_dst if mask_dst.exists() else None

    def _process_single_image(
        self, img: Path, output_dir: Path, params: SegmentationParameters
    ) -> Optional[Path]:
        """Process a single image through Cellpose and return the mask path if successful."""
        with tempfile.TemporaryDirectory(prefix="cellpose_") as tmpdir:
            tmpdir_path = Path(tmpdir)
            tmp_img = tmpdir_path / img.name
            self._copy_image_to_temp(img, tmp_img)

            cmd = self._build_cellpose_command(tmpdir_path, params)
            logger.info("Running Cellpose: %s", " ".join(cmd[:5]) + " ...")
            proc = subprocess.run(cmd, capture_output=True, text=True)

            if proc.returncode != 0:
                logger.error("Cellpose failed for %s: %s", img, proc.stderr)
                return None

            # Find produced mask in temp dir
            mask_candidates = self._find_mask_candidates(tmpdir_path, img.stem)
            # Also check for generic mask files
            mask_candidates.extend(tmpdir_path.glob("*mask*.tif*"))

            if mask_candidates:
                return self._move_mask_to_output(mask_candidates[0], output_dir, img.stem)

            # Fallback: check output_dir for pre-created outputs
            odir_candidates = self._find_mask_candidates(output_dir, img.stem)
            if odir_candidates:
                return odir_candidates[0]

            logger.warning(
                "Cellpose completed but no mask output located for %s", img
            )
            return None

    def run_segmentation(
        self,
        images: List[Path],
        output_dir: Path,
        params: SegmentationParameters,
    ) -> List[Path]:
        if not images:
            try:
                self._launch_gui()
            except (subprocess.SubprocessError, OSError) as exc:
                error_msg = f"Error launching Cellpose GUI: {exc}"
                logger.error(error_msg)
                raise CellposeError(error_msg) from exc
            return []

        output_dir.mkdir(parents=True, exist_ok=True)
        generated: List[Path] = []

        for img in images:
            try:
                result = self._process_single_image(img, output_dir, params)
                if result:
                    generated.append(result)
            except Exception as exc:
                logger.error("Error running Cellpose for %s: %s", img, exc)

        return generated
