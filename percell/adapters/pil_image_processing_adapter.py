from __future__ import annotations

import logging
from pathlib import Path
from typing import Tuple, Optional

import numpy as np
from PIL import Image

from percell.ports.driven.image_processing_port import ImageProcessingPort
from percell.domain.services.image_metadata_service import ImageMetadataService
from percell.domain.models import ImageMetadata


class PILImageProcessingAdapter(ImageProcessingPort):
    """Image processing adapter using Pillow and NumPy with metadata preservation."""

    def __init__(self, logger: Optional[logging.Logger] = None):
        """Initialize the adapter with metadata service."""
        self.metadata_service = ImageMetadataService(logger)

    def read_image(self, path: Path) -> np.ndarray:
        with Image.open(path) as im:
            return np.array(im)

    def write_image(self, path: Path, image: np.ndarray) -> None:
        """Write image with metadata preservation."""
        mode = "L" if image.ndim == 2 else None

        # Try to preserve metadata if it's a TIFF file
        if path.suffix.lower() in ['.tif', '.tiff']:
            # For new files, we don't have source metadata, so use basic save
            # This method is primarily for backward compatibility
            success = self.metadata_service.save_image_with_metadata(image, path, None)
            if success:
                return

        # Fallback to basic PIL save
        Image.fromarray(image).save(path, format="TIFF")

    def write_image_with_metadata(
        self,
        path: Path,
        image: np.ndarray,
        metadata: Optional[ImageMetadata] = None
    ) -> None:
        """Write image with specific metadata preservation."""
        success = self.metadata_service.save_image_with_metadata(image, path, metadata)
        if not success:
            # Fallback to basic save
            mode = "L" if image.ndim == 2 else None
            Image.fromarray(image).save(path, format="TIFF")

    def extract_metadata(self, path: Path) -> ImageMetadata:
        """Extract metadata from an image file."""
        return self.metadata_service.extract_metadata(path)

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


