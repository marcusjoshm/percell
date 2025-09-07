from __future__ import annotations

from pathlib import Path
from typing import Tuple

import numpy as np
from PIL import Image

from percell.ports.driven.image_processing_port import ImageProcessingPort


class PILImageProcessingAdapter(ImageProcessingPort):
    """Image processing adapter using Pillow and NumPy."""

    def read_image(self, path: Path) -> np.ndarray:
        with Image.open(path) as im:
            return np.array(im)

    def write_image(self, path: Path, image: np.ndarray) -> None:
        mode = "L" if image.ndim == 2 else None
        Image.fromarray(image).save(path, format="TIFF")

    def bin_image(self, image: np.ndarray, factor: int) -> np.ndarray:
        if factor <= 1:
            return image
        h, w = image.shape[:2]
        new_h = (h // factor) * factor
        new_w = (w // factor) * factor
        cropped = image[:new_h, :new_w, ...]
        if cropped.ndim == 2:
            reshaped = cropped.reshape(new_h // factor, factor, new_w // factor, factor)
            return reshaped.mean(axis=(1, 3)).astype(cropped.dtype)
        else:
            c = cropped.shape[2]
            reshaped = cropped.reshape(new_h // factor, factor, new_w // factor, factor, c)
            return reshaped.mean(axis=(1, 3)).astype(cropped.dtype)

    def resize(self, image: np.ndarray, target_hw: Tuple[int, int]) -> np.ndarray:
        target_h, target_w = target_hw
        im = Image.fromarray(image)
        im = im.resize((target_w, target_h), Image.NEAREST if image.ndim == 2 else Image.BILINEAR)
        return np.array(im)


