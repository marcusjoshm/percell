"""Image Binning Service - Domain Layer

Handles business logic for binning (downsampling) microscopy images while
preserving metadata and applying selection filters.
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional, Iterable, Set
import logging

from percell.domain.services.file_naming_service import FileNamingService
from percell.ports.driven.image_processing_port import ImageProcessingPort


logger = logging.getLogger(__name__)


class ImageBinningService:
    """Domain service for image binning operations.

    This service contains the business logic for binning (downsampling) images
    with optional filtering by conditions, regions, timepoints, and channels.
    """

    def __init__(self, image_processor: ImageProcessingPort):
        """Initialize the binning service.

        Args:
            image_processor: Port for image I/O and processing operations
        """
        self.image_processor = image_processor
        self.naming_service = FileNamingService()

    def bin_images(
        self,
        input_dir: Path,
        output_dir: Path,
        bin_factor: int = 4,
        conditions: Optional[Set[str]] = None,
        regions: Optional[Set[str]] = None,
        timepoints: Optional[Set[str]] = None,
        channels: Optional[Set[str]] = None,
    ) -> int:
        """Bin images from input directory to output directory with filtering.

        Args:
            input_dir: Source directory containing images
            output_dir: Destination directory for binned images
            bin_factor: Binning factor (e.g., 4 for 4x4 binning)
            conditions: Set of conditions to include (None = all)
            regions: Set of regions to include (None = all)
            timepoints: Set of timepoints to include (None = all)
            channels: Set of channels to include (None = all)

        Returns:
            Number of images successfully processed
        """
        output_dir.mkdir(parents=True, exist_ok=True)
        processed_count = 0

        for file_path in input_dir.glob("**/*.tif"):
            try:
                if self._should_process_file(
                    file_path, input_dir, conditions, regions, timepoints, channels
                ):
                    if self._process_single_image(file_path, input_dir, output_dir, bin_factor):
                        processed_count += 1
            except Exception as e:
                logger.debug(f"Skipping file {file_path.name}: {e}")
                continue

        return processed_count

    def _should_process_file(
        self,
        file_path: Path,
        input_dir: Path,
        conditions: Optional[Set[str]],
        regions: Optional[Set[str]],
        timepoints: Optional[Set[str]],
        channels: Optional[Set[str]],
    ) -> bool:
        """Check if a file matches the selection criteria.

        Args:
            file_path: Path to the image file
            input_dir: Root input directory
            conditions: Conditions filter
            regions: Regions filter
            timepoints: Timepoints filter
            channels: Channels filter

        Returns:
            True if file should be processed, False otherwise
        """
        # Check condition (from directory structure)
        try:
            rel = file_path.relative_to(input_dir)
            current_condition = rel.parts[0] if rel.parts else None
            if not current_condition:
                return False
            if conditions is not None and current_condition not in conditions:
                return False
        except ValueError:
            return False

        # Parse filename metadata
        meta = self.naming_service.parse_microscopy_filename(file_path.name)

        # Check region, timepoint, channel
        if regions is not None and (not meta.region or meta.region not in regions):
            return False
        if timepoints is not None and (not meta.timepoint or meta.timepoint not in timepoints):
            return False
        if channels is not None and (not meta.channel or meta.channel not in channels):
            return False

        return True

    def _process_single_image(
        self,
        file_path: Path,
        input_dir: Path,
        output_dir: Path,
        bin_factor: int,
    ) -> bool:
        """Process a single image file (bin and save).

        Args:
            file_path: Path to input image
            input_dir: Root input directory
            output_dir: Root output directory
            bin_factor: Binning factor

        Returns:
            True if successful, False otherwise
        """
        try:
            # Preserve directory structure
            rel = file_path.relative_to(input_dir)
            out_file = output_dir / rel.parent / f"bin{bin_factor}x{bin_factor}_{file_path.name}"
            out_file.parent.mkdir(parents=True, exist_ok=True)

            # Read, bin, and write image
            image = self.image_processor.read_image(file_path)
            binned = self.image_processor.bin_image(image, bin_factor)
            self.image_processor.write_image(out_file, binned.astype(image.dtype))

            return True
        except Exception as e:
            logger.error(f"Error processing {file_path.name}: {e}")
            return False
