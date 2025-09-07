from __future__ import annotations

from pathlib import Path
from typing import List
import subprocess
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
            return []

        output_dir.mkdir(parents=True, exist_ok=True)

        # Build a small inline script that uses cellpose's CLI to run segmentation per image
        # We avoid importing cellpose in this interpreter to prevent NumPy binary issues.
        inline = (
            "import sys, pathlib; "
            "from cellpose import models, io; "
            "p=pathlib.Path(sys.argv[1]); out=pathlib.Path(sys.argv[2]); "
            "diam=float(sys.argv[3]); flow=float(sys.argv[4]); prob=float(sys.argv[5]); model=sys.argv[6]; "
            "out.mkdir(parents=True, exist_ok=True); "
            "m=models.Cellpose(gpu=False, model_type=model); "
            "img=io.imread(p.as_posix()); "
            "masks, flows, styles, diams = m.eval(img, diameter=diam, flow_threshold=flow, cellprob_threshold=prob); "
            "import numpy as np, tifffile; tifffile.imwrite((out/(p.stem + '_mask.tif')).as_posix(), (masks>0).astype(np.uint8)*255)"
        )

        generated: List[Path] = []
        for img in images:
            try:
                cmd = [
                    str(self._python),
                    "-c",
                    inline,
                    str(img),
                    str(output_dir),
                    str(params.cell_diameter),
                    str(params.flow_threshold),
                    str(params.probability_threshold),
                    params.model_type,
                ]
                logger.info("Running Cellpose: %s", " ".join(cmd[:3]) + " ...")
                proc = subprocess.run(cmd, capture_output=True, text=True)
                if proc.returncode != 0:
                    logger.error("Cellpose failed for %s: %s", img, proc.stderr)
                    continue
                out_mask = output_dir / f"{img.stem}_mask.tif"
                if out_mask.exists():
                    generated.append(out_mask)
            except Exception as exc:
                logger.error("Error running Cellpose for %s: %s", img, exc)

        return generated


