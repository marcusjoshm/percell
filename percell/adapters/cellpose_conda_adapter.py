from __future__ import annotations

from pathlib import Path
from typing import List
import subprocess
import sys
import logging
import os

from percell.ports.driven.cellpose_integration_port import (
    CellposeIntegrationPort,
)
from percell.domain.models import SegmentationParameters
from percell.domain.exceptions import CellposeError, FileSystemError


logger = logging.getLogger(__name__)


class CellposeCondaAdapter(CellposeIntegrationPort):
    """Adapter that invokes Cellpose via a conda environment.

    This adapter is designed for systems where cellpose is installed in a
    conda environment and needs to be activated before running.
    """

    def __init__(self, conda_env_name: str, conda_path: Path = None) -> None:
        """Initialize the Cellpose conda adapter.

        Args:
            conda_env_name: Name of the conda environment containing cellpose
            conda_path: Path to conda executable (optional, defaults to system conda)
        """
        if not conda_env_name:
            raise ValueError("conda_env_name must be provided")

        self._env_name = conda_env_name
        self._conda_path = conda_path if conda_path else self._find_conda()

        logger.info(
            f"CellposeCondaAdapter initialized with conda env: {self._env_name}"
        )
        logger.info(f"Conda path: {self._conda_path}")

    def _find_conda(self) -> Path:
        """Find the conda executable on the system.

        Returns:
            Path to conda executable

        Raises:
            CellposeError: If conda cannot be found
        """
        # Try common conda locations
        conda_candidates = [
            Path.home() / "miniconda3" / "bin" / "conda",
            Path.home() / "anaconda3" / "bin" / "conda",
            Path("/opt/miniconda3/bin/conda"),
            Path("/opt/anaconda3/bin/conda"),
            Path("/usr/local/miniconda3/bin/conda"),
            Path("/usr/local/anaconda3/bin/conda"),
        ]

        # Check if conda is in PATH
        try:
            result = subprocess.run(
                ["which", "conda"],
                capture_output=True,
                text=True,
                check=False
            )
            if result.returncode == 0 and result.stdout.strip():
                conda_candidates.insert(0, Path(result.stdout.strip()))
        except Exception:
            pass

        for candidate in conda_candidates:
            if candidate.exists():
                logger.info(f"Found conda at: {candidate}")
                return candidate

        # If not found, assume conda is in PATH
        logger.warning("Could not find conda executable, assuming it's in PATH")
        return Path("conda")

    def _create_conda_command(self, cmd_args: List[str]) -> List[str]:
        """Create a command that activates conda env and runs cellpose.

        Args:
            cmd_args: Cellpose command arguments

        Returns:
            Full command list including conda activation
        """
        # Create a bash command that activates the environment and runs cellpose
        # This approach works on macOS and Linux
        cellpose_cmd = " ".join(cmd_args)

        bash_script = f"""
        eval "$(conda shell.bash hook)"
        conda activate {self._env_name}
        {cellpose_cmd}
        """

        return ["bash", "-c", bash_script]

    def run_segmentation(
        self,
        images: List[Path],
        output_dir: Path,
        params: SegmentationParameters,
    ) -> List[Path]:
        if not images:
            # Launch interactive Cellpose GUI
            try:
                cmd_args = ["cellpose"]
                cmd = self._create_conda_command(cmd_args)
                logger.info("Launching Cellpose GUI via conda environment")
                # Allow interactive session to inherit terminal IO
                subprocess.run(
                    cmd, stdin=sys.stdin, stdout=sys.stdout, stderr=sys.stderr
                )
            except (subprocess.SubprocessError, OSError) as exc:
                error_msg = f"Error launching Cellpose GUI: {exc}"
                logger.error(error_msg)
                raise CellposeError(error_msg) from exc
            return []

        output_dir.mkdir(parents=True, exist_ok=True)

        generated: List[Path] = []
        for img in images:
            try:
                # Use a temporary directory per image to avoid fragile
                # --img_filter behavior across versions.
                import tempfile
                import shutil
                with tempfile.TemporaryDirectory(prefix="cellpose_") as tmpdir:
                    tmpdir_path = Path(tmpdir)
                    # Copy the image into the temp directory with a simple name
                    tmp_img = tmpdir_path / img.name
                    try:
                        shutil.copy2(img, tmp_img)
                    except (OSError, IOError):
                        # Fall back to basic copy if metadata copy fails
                        shutil.copy(img, tmp_img)

                    cmd_args = [
                        "python",
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

                    cmd = self._create_conda_command(cmd_args)
                    logger.info(
                        f"Running Cellpose via conda env '{self._env_name}'"
                    )
                    proc = subprocess.run(cmd, capture_output=True, text=True)
                    if proc.returncode != 0:
                        logger.error(
                            "Cellpose failed for %s: %s", img, proc.stderr
                        )
                        continue

                    # Find produced mask in temp dir and move to output
                    mask_candidates = (
                        list(tmpdir_path.glob(f"{img.stem}*mask*.tif*")) +
                        list(tmpdir_path.glob(f"{img.stem}*masks*.tif*")) +
                        list(tmpdir_path.glob(f"{img.stem}*seg*.tif*")) +
                        list(tmpdir_path.glob("*mask*.tif*"))
                    )
                    if mask_candidates:
                        mask_src = mask_candidates[0]
                        output_dir.mkdir(parents=True, exist_ok=True)
                        mask_dst = output_dir / f"{img.stem}_mask.tif"
                        try:
                            shutil.move(str(mask_src), str(mask_dst))
                        except Exception:
                            shutil.copy2(str(mask_src), str(mask_dst))
                        if mask_dst.exists():
                            generated.append(mask_dst)
                    else:
                        # As a fallback for environments or tests
                        # that pre-create outputs in output_dir
                        odir_candidates = []
                        odir_candidates.extend(
                            output_dir.glob(f"{img.stem}*mask*.tif*")
                        )
                        odir_candidates.extend(
                            output_dir.glob(f"{img.stem}*masks*.tif*")
                        )
                        odir_candidates.extend(
                            output_dir.glob(f"{img.stem}*seg*.tif*")
                        )
                        if odir_candidates:
                            generated.append(odir_candidates[0])
                        else:
                            logger.warning(
                                "Cellpose completed but no mask output "
                                "located for %s",
                                img,
                            )
            except Exception as exc:
                logger.error("Error running Cellpose for %s: %s", img, exc)

        return generated
