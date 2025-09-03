"""
Cellpose segmentation adapter for Percell.

Implements the SegmentationPort interface by delegating to an external
Cellpose installation. This is a skeleton implementation aligned to the
ports/adapters refactor and can be filled in incrementally.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple
import shutil
import subprocess

from percell.ports.outbound.segmentation_port import (
    SegmentationPort,
    SegmentationError,
)
from percell.domain.entities.image import Image
from percell.domain.entities.roi import ROI
from percell.domain.value_objects.file_path import FilePath
from percell.core import run_subprocess_with_spinner
import numpy as np
import json
import tempfile
from pathlib import Path


class CellposeAdapter(SegmentationPort):
    """
    Segmentation adapter that will invoke Cellpose to generate ROIs.

    Note: Actual invocation of Cellpose is intentionally not implemented here.
    This adapter only establishes the contract with the domain via the port.
    """

    def __init__(self, cellpose_path: Optional[FilePath] = None) -> None:
        self.cellpose_path = cellpose_path

    def segment_cells(self, image: Image, parameters: Dict[str, Any]) -> List[ROI]:
        # Minimal non-interactive segmentation using python -m cellpose with CLI
        # Expects image.file_path to be set; returns placeholder ROIs from a simple mask threshold
        if image.data is None and image.file_path is None:
            raise SegmentationError("segment_cells requires image data or file_path")
        # If data available but no file, write temp
        tmp_img_path: Optional[Path] = None
        try:
            if image.file_path is None and image.data is not None:
                tmp = tempfile.NamedTemporaryFile(suffix=".tif", delete=False)
                tmp_img_path = Path(tmp.name)
                tmp.close()
                # Save via numpy (simple), consumers typically expect TIFF; rely on downstream
                from tifffile import imwrite  # type: ignore
                imwrite(str(tmp_img_path), image.data)
                img_path = tmp_img_path
            else:
                img_path = Path(str(image.file_path))
            python_exe = str(self.cellpose_path) if self.cellpose_path is not None else "python"
            outdir = Path(tempfile.mkdtemp(prefix="cellpose_"))
            cmd = [
                python_exe,
                "-m",
                "cellpose",
                "--image_path",
                str(img_path),
                "--save_tif",
                "--dir",
                str(outdir),
                "--pretrained_model",
                str(parameters.get("model", "cyto")),
                "--diameter",
                str(parameters.get("diameter", 0)),
                "--flow_threshold",
                str(parameters.get("flow_threshold", 0.4)),
            ]
            _ = run_subprocess_with_spinner(cmd, title="Cellpose: segment", capture_output=True)
            # Minimal ROI reconstruction: fallback to threshold on loaded image to create a single ROI bounding box
            data = image.data
            if data is None:
                from tifffile import imread  # type: ignore
                data = imread(str(img_path))
            if data.ndim == 3:
                data_gray = np.mean(data, axis=2)
            else:
                data_gray = data
            t = np.percentile(data_gray, 90)
            ys, xs = np.where(data_gray > t)
            if ys.size == 0:
                return []
            min_y, max_y = int(ys.min()), int(ys.max())
            min_x, max_x = int(xs.min()), int(xs.max())
            bbox = (min_x, min_y, max_x - min_x + 1, max_y - min_y + 1)
            return [
                ROI(
                    roi_id="roi_0",
                    name="cell_region",
                    bounding_box=bbox,
                    channel=parameters.get("channel"),
                    timepoint=parameters.get("timepoint"),
                )
            ]
        except Exception as e:
            raise SegmentationError(f"Cellpose segmentation failed: {e}")
        finally:
            if tmp_img_path is not None:
                try:
                    Path(tmp_img_path).unlink()
                except Exception:
                    pass

    def segment_batch(
        self, images: List[Image], parameters: Dict[str, Any]
    ) -> Dict[str, List[ROI]]:
        results: Dict[str, List[ROI]] = {}
        for img in images:
            results[img.image_id] = self.segment_cells(img, parameters)
        return results

    def validate_segmentation(
        self, rois: List[ROI], image: Optional[Image] = None
    ) -> Dict[str, Any]:
        raise NotImplementedError(
            "CellposeAdapter.validate_segmentation is not implemented yet"
        )

    def get_supported_models(self) -> List[str]:
        # Placeholder: real implementation would query Cellpose or config
        return ["cyto", "nuclei"]

    def get_default_parameters(self, model: Optional[str] = None) -> Dict[str, Any]:
        # Minimal defaults as a placeholder
        return {"model": model or "cyto", "diameter": None, "flow_threshold": 0.4}

    def estimate_processing_time(self, image: Image, parameters: Dict[str, Any]) -> float:
        # Stubbed estimate
        return 0.0

    def preprocess_image(self, image: Image, parameters: Dict[str, Any]) -> Image:
        # Simple normalization
        if image.data is None:
            return image
        data = image.data.astype(np.float32)
        mn, mx = float(np.min(data)), float(np.max(data))
        if mx > mn:
            norm = (data - mn) / (mx - mn)
        else:
            norm = np.zeros_like(data)
        return Image(image_id=f"{image.image_id}_pre", data=norm)

    def postprocess_rois(self, rois: List[ROI], parameters: Dict[str, Any]) -> List[ROI]:
        # No-op for now
        return rois

    def filter_rois_by_size(
        self,
        rois: List[ROI],
        min_area: Optional[float] = None,
        max_area: Optional[float] = None,
    ) -> List[ROI]:
        raise NotImplementedError(
            "CellposeAdapter.filter_rois_by_size is not implemented yet"
        )

    def filter_rois_by_shape(
        self,
        rois: List[ROI],
        min_circularity: Optional[float] = None,
        max_aspect_ratio: Optional[float] = None,
    ) -> List[ROI]:
        raise NotImplementedError(
            "CellposeAdapter.filter_rois_by_shape is not implemented yet"
        )

    def merge_overlapping_rois(
        self, rois: List[ROI], overlap_threshold: float = 0.5
    ) -> List[ROI]:
        raise NotImplementedError(
            "CellposeAdapter.merge_overlapping_rois is not implemented yet"
        )

    def split_touching_cells(
        self, rois: List[ROI], image: Optional[Image] = None
    ) -> List[ROI]:
        raise NotImplementedError(
            "CellposeAdapter.split_touching_cells is not implemented yet"
        )

    def calculate_roi_properties(
        self, roi: ROI, image: Optional[Image] = None
    ) -> Dict[str, float]:
        raise NotImplementedError(
            "CellposeAdapter.calculate_roi_properties is not implemented yet"
        )

    def export_masks(
        self, rois: List[ROI], image_shape: Tuple[int, int], output_path: FilePath
    ) -> None:
        raise NotImplementedError("CellposeAdapter.export_masks is not implemented yet")

    def import_masks(self, mask_path: FilePath) -> List[ROI]:
        raise NotImplementedError("CellposeAdapter.import_masks is not implemented yet")

    def get_segmentation_statistics(self, rois: List[ROI]) -> Dict[str, Any]:
        raise NotImplementedError(
            "CellposeAdapter.get_segmentation_statistics is not implemented yet"
        )

    def is_available(self) -> bool:
        try:
            python_exe = str(self.cellpose_path) if self.cellpose_path is not None else "python"
            cmd = [python_exe, "-m", "cellpose", "--help"]
            result = run_subprocess_with_spinner(cmd, title="Checking Cellpose", capture_output=True)
            return result.returncode == 0
        except Exception:
            return False

    def get_version(self) -> str:
        try:
            python_exe = str(self.cellpose_path) if self.cellpose_path is not None else "python"
            code = (
                "import importlib, import importlib.metadata as md;"
                "importlib.import_module('cellpose');"
                "print(md.version('cellpose'))"
            )
            result = run_subprocess_with_spinner([python_exe, "-c", code], title="Cellpose version", capture_output=True)
            if result.returncode == 0 and result.stdout:
                return result.stdout.strip().splitlines()[-1].strip()
        except Exception:
            pass
        return "unknown"

    def cleanup_resources(self) -> None:
        # Nothing to cleanup in the skeleton implementation
        return None


