"""
ImageJ image processing adapter for Percell.

Skeleton adapter implementing ImageProcessingPort. This establishes the
contract and can be filled in with actual ImageJ invocation logic.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import cv2  # type: ignore
from skimage import filters, exposure, morphology, registration  # type: ignore
from skimage.draw import polygon  # type: ignore

from percell.ports.outbound.image_processing_port import (
    ImageProcessingPort,
    ImageProcessingError,
)
from percell.domain.entities.image import Image
from percell.domain.entities.roi import ROI
from percell.domain.value_objects.file_path import FilePath
from percell.core import get_macro_file, run_subprocess_with_spinner
from percell.core.utils import get_package_root
from pathlib import Path


class ImageJAdapter(ImageProcessingPort):
    def __init__(self, imagej_path: Optional[FilePath] = None) -> None:
        self.imagej_path = imagej_path

    def execute_macro(
        self,
        macro_name: str,
        parameters: Dict[str, Any],
        input_files: Optional[List[FilePath]] = None,
    ) -> Dict[str, Any]:
        if self.imagej_path is None:
            raise ImageProcessingError("ImageJ path is not configured")

        # Resolve macro path from package if a bare name is provided
        try:
            macro_path = (
                Path(macro_name)
                if Path(macro_name).exists()
                else get_macro_file(macro_name)
            )
        except Exception as exc:
            raise ImageProcessingError(f"Macro not found: {macro_name} ({exc})")

        # ImageJ -macro supports passing a single argument string; keep it simple
        # by serializing parameters as key=value;key2=value2
        arg_str = "".join(
            []
            if not parameters
            else [
                ";".join(
                    f"{key}={value}" for key, value in parameters.items() if value is not None
                )
            ]
        )

        cmd = [str(self.imagej_path), "-macro", str(macro_path)]
        if arg_str:
            cmd.append(arg_str)

        result = run_subprocess_with_spinner(
            cmd,
            title=f"ImageJ: {Path(macro_path).stem}",
            capture_output=True,
            text=True,
            check=False,
        )

        return {
            "returncode": result.returncode,
            "stdout": result.stdout or "",
            "stderr": result.stderr or "",
        }

    def resize_rois(self, rois: List[ROI], scale_factor: float) -> List[ROI]:
        if scale_factor == 1.0:
            return rois
        resized: List[ROI] = []
        for roi in rois:
            resized.append(roi.scale(scale_factor))
        return resized

    def threshold_image(
        self, image: Image, method: str = "otsu", parameters: Optional[Dict[str, Any]] = None
    ) -> Image:
        if image.data is None:
            raise ImageProcessingError("threshold_image requires image.data")
        params = parameters or {}
        data = image.data
        if data.ndim == 3:
            # Convert to grayscale by averaging channels
            data_gray = np.mean(data, axis=2)
        else:
            data_gray = data
        if method == "otsu":
            t = filters.threshold_otsu(data_gray)
        elif method == "yen":
            t = filters.threshold_yen(data_gray)
        elif method == "li":
            t = filters.threshold_li(data_gray)
        else:
            # Fallback to Otsu
            t = filters.threshold_otsu(data_gray)
        binary = (data_gray > t).astype(data.dtype)
        return Image(image_id=f"{image.image_id}_thresholded", data=binary)

    def interactive_threshold(
        self, image: Image, roi: Optional[ROI] = None
    ) -> Tuple[Image, float]:
        # Non-interactive fallback: Otsu
        if image.data is None:
            raise ImageProcessingError("interactive_threshold requires image.data")
        data = image.data
        data_gray = np.mean(data, axis=2) if data.ndim == 3 else data
        t = filters.threshold_otsu(data_gray)
        binary = (data_gray > t).astype(data.dtype)
        return Image(image_id=f"{image.image_id}_thresh", data=binary), float(t)

    def measure_roi_intensity(self, image: Image, roi: ROI) -> Dict[str, float]:
        if image.data is None or not roi.coordinates:
            raise ImageProcessingError("measure_roi_intensity requires image.data and ROI coordinates")
        data = image.data
        mask = np.zeros((image.height, image.width), dtype=np.uint8)
        coords = np.array(roi.coordinates, dtype=np.int32)
        if coords.ndim == 2:
            cv2.fillPoly(mask, [coords], 1)
        else:
            raise ImageProcessingError("ROI coordinates must be 2D")
        if data.ndim == 3:
            data_gray = np.mean(data, axis=2)
        else:
            data_gray = data
        values = data_gray[mask == 1]
        if values.size == 0:
            return {"mean": 0.0, "median": 0.0, "min": 0.0, "max": 0.0}
        return {
            "mean": float(np.mean(values)),
            "median": float(np.median(values)),
            "min": float(np.min(values)),
            "max": float(np.max(values)),
        }

    def measure_roi_area(self, roi: ROI, pixel_size: Optional[float] = None) -> float:
        if roi.area is not None:
            area = roi.area
        else:
            area = roi.calculate_area()
        if pixel_size is None:
            return float(area)
        # Convert pixels^2 to physical units^2
        return float(area) * (pixel_size ** 2)

    def extract_cell_region(self, image: Image, roi: ROI, padding: int = 0) -> Image:
        if image.data is None or roi.bounding_box is None:
            raise ImageProcessingError("extract_cell_region requires image.data and ROI.bounding_box")
        x, y, w, h = roi.bounding_box
        x = max(0, x - padding)
        y = max(0, y - padding)
        x2 = min(image.width, x + w + padding)
        y2 = min(image.height, y + h + padding)
        if image.data.ndim == 3:
            crop = image.data[y:y2, x:x2, :]
        else:
            crop = image.data[y:y2, x:x2]
        return Image(image_id=f"{image.image_id}_crop_{roi.roi_id}", data=crop)

    def apply_gaussian_blur(self, image: Image, sigma: float) -> Image:
        if image.data is None:
            raise ImageProcessingError("apply_gaussian_blur requires image.data")
        ksize = max(1, int(6 * sigma) // 2 * 2 + 1)
        if image.data.ndim == 3:
            blurred = np.stack([cv2.GaussianBlur(image.data[..., c], (ksize, ksize), sigma) for c in range(image.data.shape[2])], axis=2)
        else:
            blurred = cv2.GaussianBlur(image.data, (ksize, ksize), sigma)
        return Image(image_id=f"{image.image_id}_gauss", data=blurred)

    def apply_median_filter(self, image: Image, kernel_size: int) -> Image:
        if image.data is None:
            raise ImageProcessingError("apply_median_filter requires image.data")
        k = max(1, kernel_size // 2 * 2 + 1)
        if image.data.ndim == 3:
            filtered = np.stack([cv2.medianBlur(image.data[..., c], k) for c in range(image.data.shape[2])], axis=2)
        else:
            filtered = cv2.medianBlur(image.data, k)
        return Image(image_id=f"{image.image_id}_median", data=filtered)

    def enhance_contrast(
        self, image: Image, method: str = "clahe", parameters: Optional[Dict[str, Any]] = None
    ) -> Image:
        if image.data is None:
            raise ImageProcessingError("enhance_contrast requires image.data")
        params = parameters or {}
        if method.lower() == "clahe":
            clip = float(params.get("clip", 0.01))
            nbins = int(params.get("nbins", 256))
            if image.data.ndim == 3:
                out = np.stack([exposure.equalize_adapthist(image.data[..., c], clip_limit=clip, nbins=nbins) for c in range(image.data.shape[2])], axis=2)
            else:
                out = exposure.equalize_adapthist(image.data, clip_limit=clip, nbins=nbins)
            return Image(image_id=f"{image.image_id}_clahe", data=(out * 255).astype(image.data.dtype))
        # Fallback: return original
        return image

    def normalize_image(self, image: Image, method: str = "minmax") -> Image:
        if image.data is None:
            raise ImageProcessingError("normalize_image requires image.data")
        data = image.data.astype(np.float32)
        if method == "minmax":
            mn, mx = np.min(data), np.max(data)
            if mx > mn:
                norm = (data - mn) / (mx - mn)
            else:
                norm = np.zeros_like(data)
        else:
            mu, sd = float(np.mean(data)), float(np.std(data) + 1e-8)
            norm = (data - mu) / sd
        return Image(image_id=f"{image.image_id}_norm", data=norm)

    def create_composite_image(self, images: List[Image], channels: List[str]) -> Image:
        # Stack provided images along channel axis
        if not images:
            raise ImageProcessingError("create_composite_image requires at least one image")
        arrays = [img.data for img in images if img.data is not None]
        if not arrays:
            raise ImageProcessingError("create_composite_image images must have data")
        # Ensure shapes match by minimal cropping to smallest HxW
        min_h = min(arr.shape[0] for arr in arrays)
        min_w = min(arr.shape[1] for arr in arrays)
        arrays = [arr[:min_h, :min_w] if arr.ndim == 2 else arr[:min_h, :min_w, 0] for arr in arrays]
        comp = np.stack(arrays, axis=2)
        return Image(image_id="composite", data=comp)

    def split_channels(self, image: Image) -> List[Image]:
        if image.data is None:
            raise ImageProcessingError("split_channels requires image.data")
        if image.data.ndim == 2:
            return [Image(image_id=f"{image.image_id}_ch0", data=image.data)]
        imgs: List[Image] = []
        for c in range(image.data.shape[2]):
            imgs.append(Image(image_id=f"{image.image_id}_ch{c}", data=image.data[..., c]))
        return imgs

    def create_maximum_projection(self, images: List[Image]) -> Image:
        arrays = [img.data for img in images if img.data is not None]
        if not arrays:
            raise ImageProcessingError("create_maximum_projection requires image data")
        # Stack along a new axis and take max
        stack = np.stack(arrays, axis=0)
        proj = np.max(stack, axis=0)
        return Image(image_id="max_projection", data=proj)

    def register_images(self, reference: Image, target: Image) -> Image:
        if reference.data is None or target.data is None:
            raise ImageProcessingError("register_images requires image data")
        ref = reference.data if reference.data.ndim == 2 else np.mean(reference.data, axis=2)
        tar = target.data if target.data.ndim == 2 else np.mean(target.data, axis=2)
        shift, _, _ = registration.phase_cross_correlation(ref, tar)
        # Simple translation only
        M = np.float32([[1, 0, -shift[1]], [0, 1, -shift[0]]])
        aligned = cv2.warpAffine(target.data, M, (target.data.shape[1], target.data.shape[0]))
        return Image(image_id=f"{target.image_id}_registered", data=aligned)

    def calculate_colocalization(
        self, image1: Image, image2: Image, roi: Optional[ROI] = None
    ) -> Dict[str, float]:
        if image1.data is None or image2.data is None:
            raise ImageProcessingError("calculate_colocalization requires image data")
        a = image1.data if image1.data.ndim == 2 else image1.data[..., 0]
        b = image2.data if image2.data.ndim == 2 else image2.data[..., 0]
        if roi and roi.coordinates:
            mask = np.zeros_like(a, dtype=np.uint8)
            cv2.fillPoly(mask, [np.array(roi.coordinates, dtype=np.int32)], 1)
            a = a[mask == 1]
            b = b[mask == 1]
        a = a.astype(np.float32).ravel()
        b = b.astype(np.float32).ravel()
        if a.size == 0:
            return {"pearson": 0.0, "manders_m1": 0.0, "manders_m2": 0.0}
        pearson = float(np.corrcoef(a, b)[0, 1])
        m1 = float(np.sum(a[b > 0]) / (np.sum(a) + 1e-8))
        m2 = float(np.sum(b[a > 0]) / (np.sum(b) + 1e-8))
        return {"pearson": pearson, "manders_m1": m1, "manders_m2": m2}

    def create_binary_mask(self, rois: List[ROI], image_shape: Tuple[int, int]) -> np.ndarray:
        mask = np.zeros(image_shape, dtype=np.uint8)
        for r in rois:
            if r.coordinates:
                cv2.fillPoly(mask, [np.array(r.coordinates, dtype=np.int32)], 1)
        return mask

    def apply_morphological_operations(
        self, image: Image, operation: str, kernel_size: int = 3
    ) -> Image:
        if image.data is None:
            raise ImageProcessingError("apply_morphological_operations requires image.data")
        kernel = morphology.square(kernel_size)
        data = image.data
        if data.ndim == 3:
            data_gray = np.mean(data, axis=2)
        else:
            data_gray = data
        if operation == "opening":
            out = morphology.opening(data_gray, kernel)
        elif operation == "closing":
            out = morphology.closing(data_gray, kernel)
        elif operation == "erosion":
            out = morphology.erosion(data_gray, kernel)
        elif operation == "dilation":
            out = morphology.dilation(data_gray, kernel)
        else:
            out = data_gray
        return Image(image_id=f"{image.image_id}_{operation}", data=out.astype(image.data.dtype))

    def detect_edges(
        self, image: Image, method: str = "canny", parameters: Optional[Dict[str, Any]] = None
    ) -> Image:
        if image.data is None:
            raise ImageProcessingError("detect_edges requires image.data")
        params = parameters or {}
        data = image.data
        data_gray = np.mean(data, axis=2) if data.ndim == 3 else data
        if method == "canny":
            low = int(params.get("low", 50))
            high = int(params.get("high", 150))
            edges = cv2.Canny(data_gray.astype(np.uint8), low, high)
        else:
            edges = filters.sobel(data_gray)
        return Image(image_id=f"{image.image_id}_edges", data=edges)

    def get_available_macros(self) -> List[str]:
        try:
            macros_dir = get_package_root() / "macros"
            if not macros_dir.exists():
                return []
            return [p.name for p in macros_dir.glob("*.ijm")]
        except Exception:
            return []

    def validate_macro_parameters(self, macro_name: str, parameters: Dict[str, Any]) -> bool:
        return True

    def is_available(self) -> bool:
        try:
            return self.imagej_path is not None and Path(str(self.imagej_path)).exists()
        except Exception:
            return False

    def get_version(self) -> str:
        # FIJI/ImageJ doesn't have a consistent --version; keep minimal
        return "unknown"

    def cleanup_resources(self) -> None:
        return None


