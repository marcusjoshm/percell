"""
ROIProcessor

Domain service for ROI-related operations that are business-logic centric
and independent of concrete tools (adapters handle I/O and external macros).
"""

from __future__ import annotations

import logging
import re
from typing import Iterable, List, Optional, Set

from percell.domain.value_objects.file_path import FilePath
from percell.ports.outbound.storage_port import StoragePort
from percell.domain.services.metadata_service import MetadataService


logger = logging.getLogger(__name__)


class ROIProcessor:
    """Encapsulates ROI utilities that operate over StoragePort and MetadataService."""

    def __init__(self, storage: StoragePort, metadata_service: MetadataService) -> None:
        self.storage = storage
        self.metadata_service = metadata_service

    def duplicate_rois_for_channels(self, roi_dir: FilePath, channels: Iterable[str]) -> int:
        """
        Duplicate ROI .zip files for each provided analysis channel by substituting
        the channel token in filenames (e.g., _ch00_ -> _ch02_).

        Returns number of copies created.
        """
        channels_set: Set[str] = set(channels)
        if not self.storage.directory_exists(roi_dir):
            logger.error("ROI directory not found: %s", roi_dir)
            return 0

        roi_files = self.storage.list_files(roi_dir, pattern="**/*.zip", recursive=True)
        if not roi_files:
            logger.warning("No ROI files found in %s", roi_dir)
            return 0

        created = 0
        for roi_file in roi_files:
            name = roi_file.get_name()
            match = re.search(r"_ch\d+_", name)
            channel = match.group(0).strip("_") if match else None
            if channel is None:
                # Heuristic: try to infer via metadata service by scanning sibling directory
                try:
                    md_list = self.metadata_service.scan_directory_for_metadata(roi_file.get_parent(), recursive=True)
                    stem = roi_file.get_stem().replace("ROIs_", "").replace("_rois", "")
                    m = next((m for m in md_list if getattr(m, 'file_path', None) and stem in str(m.file_path)), None)
                    if m and getattr(m, 'channel', None):
                        channel = m.channel
                        # normalize format chNN
                        if not channel.startswith('ch'):
                            channel = f"ch{channel}"
                except Exception:
                    pass
            if channel is None:
                logger.info("Skipping ROI without channel token: %s", name)
                continue

            for target_channel in channels_set:
                if target_channel == channel:
                    continue
                new_name = re.sub(r"_ch\d+_", f"_{target_channel}_", name)
                destination = roi_file.get_parent().join(new_name)
                if self.storage.file_exists(destination):
                    continue
                try:
                    self.storage.copy_file(roi_file, destination)
                    created += 1
                except Exception as exc:
                    logger.warning("Failed to copy %s -> %s: %s", roi_file, destination, exc)
                    continue

        logger.info("Created %d ROI copies for requested channels", created)
        return created


