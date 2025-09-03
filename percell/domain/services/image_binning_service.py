"""
ImageBinningService

Domain service that performs image binning and related selection/filtering
using domain ports (StoragePort, MetadataService) and value objects.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List, Optional, Set
import numpy as np

from percell.domain.value_objects.file_path import FilePath
from percell.domain.services.metadata_service import MetadataService
from percell.ports.outbound.storage_port import StoragePort


 


@dataclass
class BinningSelection:
    conditions: Optional[Set[str]] = None
    regions: Optional[Set[str]] = None
    timepoints: Optional[Set[str]] = None
    channels: Optional[Set[str]] = None


class ImageBinningService:
    """
    Domain service to bin images by a specified factor, preserving
    directory structure and filtering by metadata selections.
    """

    def __init__(
        self,
        storage: StoragePort,
        metadata_service: MetadataService,
    ) -> None:
        self.storage = storage
        self.metadata_service = metadata_service

    def process_images(
        self,
        input_dir: FilePath,
        output_dir: FilePath,
        bin_factor: int = 4,
        target_conditions: Optional[Iterable[str]] = None,
        target_regions: Optional[Iterable[str]] = None,
        target_timepoints: Optional[Iterable[str]] = None,
        target_channels: Optional[Iterable[str]] = None,
    ) -> int:
        """
        Process and bin images under input_dir, writing outputs under output_dir.

        Returns number of processed files.
        """
        

        selection = self._build_selection(
            target_conditions, target_regions, target_timepoints, target_channels
        )

        # Ensure output directory exists
        if not self.storage.directory_exists(output_dir):
            self.storage.create_directory(output_dir)

        files = self._discover_input_files(input_dir)
        

        processed_count = 0
        for image_path in files:
            # Filter by condition/region/timepoint/channel
            if not self._file_matches_selection(input_dir, image_path, selection):
                continue

            # Compute destination path mirroring structure
            relative = image_path.path.relative_to(input_dir.path)
            destination_parent = output_dir.path / relative.parent
            destination_name = f"bin{bin_factor}x{bin_factor}_" + image_path.get_name()
            destination = FilePath.from_string(str(destination_parent / destination_name))

            # Ensure destination directory exists
            if not self.storage.directory_exists(FilePath.from_string(str(destination_parent))):
                self.storage.create_directory(FilePath.from_string(str(destination_parent)))

            try:
                image = self.storage.read_image(image_path)
                binned = self._bin_image_array(image, bin_factor)
                self.storage.write_image(binned.astype(image.dtype), destination)
                processed_count += 1
            except Exception:  # pragma: no cover - safety
                continue

        return processed_count

    def _build_selection(
        self,
        conditions: Optional[Iterable[str]],
        regions: Optional[Iterable[str]],
        timepoints: Optional[Iterable[str]],
        channels: Optional[Iterable[str]],
    ) -> BinningSelection:
        def to_set(values: Optional[Iterable[str]]) -> Optional[Set[str]]:
            if values is None:
                return None
            values_set = set(values)
            return None if {"all"}.issubset(values_set) else values_set

        return BinningSelection(
            conditions=to_set(conditions),
            regions=to_set(regions),
            timepoints=to_set(timepoints),
            channels=to_set(channels),
        )

    def _discover_input_files(self, input_dir: FilePath) -> List[FilePath]:
        # Prefer MetadataService for a full scan; fallback to StoragePort listing
        try:
            metadata = self.metadata_service.scan_directory_for_metadata(input_dir, recursive=True)
            files = [FilePath.from_string(str(getattr(m, "file_path", ""))) for m in metadata if getattr(m, "file_path", None)]
            return files
        except Exception:  # pragma: no cover - safety fallback
            return self.storage.list_files(input_dir, pattern="**/*.tif", recursive=True)

    def _file_matches_selection(
        self,
        base_dir: FilePath,
        file_path: FilePath,
        selection: BinningSelection,
    ) -> bool:
        # Condition: inferred from first directory under base_dir
        try:
            relative_parts = list(file_path.path.relative_to(base_dir.path).parts)
            current_condition = relative_parts[0] if relative_parts else None
        except Exception:
            current_condition = None

        if selection.conditions is not None and current_condition not in selection.conditions:
            return False

        # Prefer metadata from service
        current_region = None
        current_timepoint = None
        current_channel = None
        try:
            md_list = self.metadata_service.scan_directory_for_metadata(file_path.get_parent(), recursive=False)
            md = next((m for m in md_list if getattr(m, 'file_path', None) and str(m.file_path) == str(file_path)), None)
            if md:
                current_region = getattr(md, 'region', None)
                current_timepoint = getattr(md, 'timepoint', None)
                current_channel = getattr(md, 'channel', None)
        except Exception:
            pass

        # Apply filters
        if selection.regions is not None and (not current_region or current_region not in selection.regions):
            return False
        if selection.timepoints is not None and (not current_timepoint or current_timepoint not in selection.timepoints):
            return False
        if selection.channels is not None and (not current_channel or current_channel not in selection.channels):
            return False
        return True

    def _bin_image_array(self, image: np.ndarray, bin_factor: int) -> np.ndarray:
        """
        Bin an image by local mean using numpy reshaping. Supports 2D (H,W)
        and 3D with channels last (H,W,C). If dimensions are not divisible by
        bin_factor, the image is cropped at the end to the nearest divisible size.
        """
        if bin_factor <= 1:
            return image

        if image.ndim == 2:
            h, w = image.shape
            h2 = (h // bin_factor) * bin_factor
            w2 = (w // bin_factor) * w // bin_factor * bin_factor
            w2 = (w // bin_factor) * bin_factor
            img = image[:h2, :w2]
            reshaped = img.reshape(h2 // bin_factor, bin_factor, w2 // bin_factor, bin_factor)
            return reshaped.mean(axis=(1, 3))

        if image.ndim == 3:
            h, w, c = image.shape
            h2 = (h // bin_factor) * bin_factor
            w2 = (w // bin_factor) * bin_factor
            img = image[:h2, :w2, :]
            reshaped = img.reshape(h2 // bin_factor, bin_factor, w2 // bin_factor, bin_factor, c)
            return reshaped.mean(axis=(1, 3))

        # For other dimensions, fallback to returning image unchanged
        return image


