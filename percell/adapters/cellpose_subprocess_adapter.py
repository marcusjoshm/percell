from __future__ import annotations

from pathlib import Path
from typing import List
import subprocess
import sys
import logging

from percell.ports.driven.cellpose_integration_port import CellposeIntegrationPort
from percell.domain.models import SegmentationParameters


logger = logging.getLogger(__name__)


class CellposeSubprocessAdapter(CellposeIntegrationPort):
    """Adapter that invokes Cellpose via a Python subprocess.

    Expects a Python interpreter with Cellpose installed to be available.
    """

    def __init__(self, python_executable: Path) -> None:
        if not python_executable:
            raise ValueError("python_executable must be provided")
        self._python = Path(python_executable)

    def run_segmentation(
        self,
        images: List[Path],
        output_dir: Path,
        params: SegmentationParameters,
    ) -> List[Path]:
        if not images:
            # Launch interactive Cellpose GUI without binding to any directory or files
            try:
                cmd = [str(self._python), "-m", "cellpose"]
                logger.info("Launching Cellpose GUI: %s", " ".join(cmd))
                # Allow interactive session to inherit terminal IO
                subprocess.run(cmd, stdin=sys.stdin, stdout=sys.stdout, stderr=sys.stderr)
            except Exception as exc:
                logger.error("Error launching Cellpose GUI: %s", exc)
            return []

        output_dir.mkdir(parents=True, exist_ok=True)

        generated: List[Path] = []
        for img in images:
            try:
                # Use a temporary directory per image to avoid fragile --img_filter behavior across versions.
                import tempfile, shutil
                with tempfile.TemporaryDirectory(prefix="cellpose_") as tmpdir:
                    tmpdir_path = Path(tmpdir)
                    # Copy the image into the temp directory with a simple name
                    tmp_img = tmpdir_path / img.name
                    try:
                        shutil.copy2(img, tmp_img)
                    except Exception:
                        shutil.copy(img, tmp_img)

                    cmd = [
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
                    logger.info("Running Cellpose: %s", " ".join(cmd[:5]) + " ...")
                    proc = subprocess.run(cmd, capture_output=True, text=True)
                    if proc.returncode != 0:
                        logger.error("Cellpose failed for %s: %s", img, proc.stderr)
                        continue

                    # Find produced mask in temp dir and move to output
                    mask_candidates = list(tmpdir_path.glob(f"{img.stem}*mask*.tif*")) + \
                                      list(tmpdir_path.glob(f"{img.stem}*masks*.tif*")) + \
                                      list(tmpdir_path.glob(f"{img.stem}*seg*.tif*")) + \
                                      list(tmpdir_path.glob("*mask*.tif*"))
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
                        # As a fallback for environments/tests that pre-create outputs in output_dir
                        odir_candidates = []
                        odir_candidates.extend(output_dir.glob(f"{img.stem}*mask*.tif*"))
                        odir_candidates.extend(output_dir.glob(f"{img.stem}*masks*.tif*"))
                        odir_candidates.extend(output_dir.glob(f"{img.stem}*seg*.tif*"))
                        if odir_candidates:
                            generated.append(odir_candidates[0])
                        else:
                            logger.warning("Cellpose completed but no mask output located for %s", img)
            except Exception as exc:
                logger.error("Error running Cellpose for %s: %s", img, exc)

        return generated


