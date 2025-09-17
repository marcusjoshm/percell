"""Image metadata extraction and preservation service.

This service provides centralized handling of TIFF image metadata,
including resolution, scale, and ImageJ-specific information.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Optional

try:
    import tifffile
    HAVE_TIFFFILE = True
except ImportError:
    HAVE_TIFFFILE = False

try:
    from PIL import Image
    HAVE_PIL = True
except ImportError:
    HAVE_PIL = False

import numpy as np

from ..models import ImageMetadata


class ImageMetadataService:
    """Service for extracting and preserving TIFF image metadata."""

    def __init__(self, logger: Optional[logging.Logger] = None):
        """Initialize the metadata service.

        Args:
            logger: Optional logger for metadata operations
        """
        self.logger = logger or logging.getLogger(__name__)

    def extract_metadata(self, image_path: Path) -> ImageMetadata:
        """Extract metadata from a TIFF image file.

        Args:
            image_path: Path to the TIFF image file

        Returns:
            ImageMetadata object with extracted information
        """
        if not image_path.exists():
            self.logger.warning(f"Image file not found: {image_path}")
            return ImageMetadata()

        if not HAVE_TIFFFILE:
            self.logger.warning(f"tifffile not available, limited metadata extraction for {image_path.name}")
            return self._extract_metadata_pil_fallback(image_path)

        try:
            return self._extract_metadata_tifffile(image_path)
        except Exception as e:
            self.logger.warning(f"tifffile extraction failed for {image_path.name}: {e}")
            return self._extract_metadata_pil_fallback(image_path)

    def _extract_metadata_tifffile(self, image_path: Path) -> ImageMetadata:
        """Extract metadata using tifffile library."""
        metadata = ImageMetadata()

        try:
            with tifffile.TiffFile(image_path) as tif:
                if hasattr(tif, 'pages') and len(tif.pages) > 0:
                    page = tif.pages[0]

                    if hasattr(page, 'tags'):
                        # Extract standard TIFF resolution tags
                        if 'XResolution' in page.tags:
                            x_res_value = page.tags['XResolution'].value
                            if isinstance(x_res_value, tuple) and len(x_res_value) >= 2:
                                metadata.x_resolution = float(x_res_value[0]) / float(x_res_value[1])
                            else:
                                metadata.x_resolution = float(x_res_value)
                        if 'YResolution' in page.tags:
                            y_res_value = page.tags['YResolution'].value
                            if isinstance(y_res_value, tuple) and len(y_res_value) >= 2:
                                metadata.y_resolution = float(y_res_value[0]) / float(y_res_value[1])
                            else:
                                metadata.y_resolution = float(y_res_value)
                        if 'ResolutionUnit' in page.tags:
                            metadata.resolution_unit = int(page.tags['ResolutionUnit'].value)

                        # Calculate pixel size if resolution is available
                        if metadata.x_resolution and metadata.resolution_unit:
                            metadata.pixel_size_um = self._calculate_pixel_size_um(
                                metadata.x_resolution, metadata.resolution_unit
                            )
                            if metadata.pixel_size_um:
                                metadata.pixels_per_um = 1.0 / metadata.pixel_size_um

                    # Extract ImageJ metadata
                    if hasattr(page, 'imagej_tags') and page.imagej_tags:
                        metadata.imagej_metadata.update(page.imagej_tags)

                    # Check TiffFile-level ImageJ metadata
                    if hasattr(tif, 'imagej_metadata') and tif.imagej_metadata:
                        metadata.imagej_metadata.update(tif.imagej_metadata)

                    # Extract pixel size from ImageJ metadata if not already available
                    if not metadata.pixel_size_um and metadata.imagej_metadata:
                        if 'pixelwidth' in metadata.imagej_metadata:
                            metadata.pixel_size_um = float(metadata.imagej_metadata['pixelwidth'])
                        elif 'resolution' in metadata.imagej_metadata:
                            metadata.pixel_size_um = float(metadata.imagej_metadata['resolution'])

            self._log_extracted_metadata(image_path, metadata)
            return metadata

        except Exception as e:
            self.logger.error(f"Error extracting metadata from {image_path.name}: {e}")
            return ImageMetadata()

    def _extract_metadata_pil_fallback(self, image_path: Path) -> ImageMetadata:
        """Extract basic metadata using PIL as fallback."""
        if not HAVE_PIL:
            self.logger.warning("Neither tifffile nor PIL available for metadata extraction")
            return ImageMetadata()

        metadata = ImageMetadata()

        try:
            with Image.open(image_path) as img:
                if hasattr(img, 'tag') and img.tag is not None:
                    # Extract resolution information from PIL
                    if 282 in img.tag:  # XResolution
                        metadata.x_resolution = float(img.tag[282])
                    if 283 in img.tag:  # YResolution
                        metadata.y_resolution = float(img.tag[283])
                    if 296 in img.tag:  # ResolutionUnit
                        metadata.resolution_unit = int(img.tag[296])

                    # Calculate pixel size
                    if metadata.x_resolution and metadata.resolution_unit:
                        metadata.pixel_size_um = self._calculate_pixel_size_um(
                            metadata.x_resolution, metadata.resolution_unit
                        )

            self.logger.info(f"Extracted basic metadata from {image_path.name} using PIL")
            return metadata

        except Exception as e:
            self.logger.error(f"Error extracting metadata with PIL from {image_path.name}: {e}")
            return ImageMetadata()

    def _calculate_pixel_size_um(self, resolution: float, resolution_unit: int) -> Optional[float]:
        """Calculate pixel size in micrometers from resolution information.

        Args:
            resolution: Resolution value
            resolution_unit: 1=none, 2=inch, 3=cm

        Returns:
            Pixel size in micrometers, or None if calculation fails
        """
        if resolution <= 0:
            return None

        try:
            if resolution_unit == 2:  # inches
                # Convert from pixels/inch to micrometers/pixel
                return 25400.0 / resolution  # 25400 µm/inch
            elif resolution_unit == 3:  # centimeters
                # Convert from pixels/cm to micrometers/pixel
                return 10000.0 / resolution  # 10000 µm/cm
            else:
                # Unknown unit, cannot calculate
                return None
        except (ZeroDivisionError, ValueError):
            return None

    def save_image_with_metadata(
        self,
        image: np.ndarray,
        output_path: Path,
        metadata: Optional[ImageMetadata] = None
    ) -> bool:
        """Save an image with preserved metadata.

        Args:
            image: Image array to save
            output_path: Path where to save the image
            metadata: Metadata to preserve (optional)

        Returns:
            True if successful, False otherwise
        """
        if not HAVE_TIFFFILE:
            self.logger.warning(f"tifffile not available, saving {output_path.name} without metadata")
            return self._save_image_pil_fallback(image, output_path)

        try:
            kwargs = {"imagej": True}

            if metadata and metadata.has_resolution_info():
                kwargs.update(metadata.to_tifffile_kwargs())
                self.logger.debug(f"Saving {output_path.name} with metadata: {list(kwargs.keys())}")
            else:
                self.logger.debug(f"Saving {output_path.name} without resolution metadata")

            # Ensure clean image data - no ROI overlays or selections embedded
            # This is particularly important for grouped cell images used in thresholding
            self.logger.debug(f"Saving image: shape={image.shape}, dtype={image.dtype}, range=[{image.min()}, {image.max()}]")

            tifffile.imwrite(str(output_path), image, **kwargs)
            self.logger.info(f"Successfully saved {output_path.name} with tifffile")
            return True

        except Exception as e:
            self.logger.error(f"Error saving {output_path.name} with tifffile: {e}")
            return self._save_image_pil_fallback(image, output_path)

    def _save_image_pil_fallback(self, image: np.ndarray, output_path: Path) -> bool:
        """Save image using PIL as fallback."""
        if not HAVE_PIL:
            self.logger.error("Neither tifffile nor PIL available for image saving")
            return False

        try:
            from PIL import Image
            mode = "L" if image.ndim == 2 else None
            Image.fromarray(image).save(output_path, format="TIFF")
            self.logger.info(f"Saved {output_path.name} using PIL fallback")
            return True
        except Exception as e:
            self.logger.error(f"Error saving {output_path.name} with PIL: {e}")
            return False

    def _log_extracted_metadata(self, image_path: Path, metadata: ImageMetadata) -> None:
        """Log extracted metadata information."""
        if metadata.has_resolution_info():
            self.logger.info(f"Extracted metadata from {image_path.name}:")
            if metadata.x_resolution and metadata.y_resolution:
                self.logger.info(f"  Resolution: {metadata.x_resolution} x {metadata.y_resolution}")
            if metadata.resolution_unit:
                unit_names = {1: "none", 2: "inch", 3: "cm"}
                unit_name = unit_names.get(metadata.resolution_unit, "unknown")
                self.logger.info(f"  Resolution unit: {unit_name}")
            if metadata.pixel_size_um:
                self.logger.info(f"  Pixel size: {metadata.pixel_size_um:.4f} µm")
            if metadata.imagej_metadata:
                self.logger.debug(f"  ImageJ metadata keys: {list(metadata.imagej_metadata.keys())}")
        else:
            self.logger.debug(f"No resolution metadata found in {image_path.name}")