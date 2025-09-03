"""
RoiTrackingService

Domain service for tracking cells by matching ROIs between two timepoints.

Implements centroid-based matching with a Hungarian assignment to reorder
the second ROI set to match the first. Includes batch discovery support
for timepoint pairs using filename patterns and MetadataService heuristics.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional, Tuple
import logging
from pathlib import Path
import zipfile
import numpy as np
from scipy.optimize import linear_sum_assignment
from read_roi import read_roi_zip

from percell.domain.value_objects.file_path import FilePath
from percell.domain.services.metadata_service import MetadataService
from percell.ports.outbound.storage_port import StoragePort


logger = logging.getLogger(__name__)


class RoiTrackingService:
    """Domain service encapsulating ROI tracking logic."""

    def __init__(self, storage: StoragePort, metadata_service: MetadataService) -> None:
        self.storage = storage
        self.metadata_service = metadata_service

    # ---- Public API ----
    def process_roi_pair(self, zip_file1: FilePath, zip_file2: FilePath) -> bool:
        """
        Reorder ROIs in zip_file2 to best match zip_file1 and overwrite zip_file2.
        Returns True on success.
        """
        logger.info(
            "Processing ROI pair: %s -> %s",
            zip_file1.get_name(),
            zip_file2.get_name(),
        )

        roi_dict1 = self._load_roi_dict(zip_file1)
        roi_dict2 = self._load_roi_dict(zip_file2)
        if roi_dict1 is None or roi_dict2 is None:
            logger.error("Failed to load ROI dictionaries.")
            return False

        roi_bytes2 = self._load_roi_bytes(zip_file2)
        if roi_bytes2 is None:
            logger.error("Failed to load ROI bytes from %s", zip_file2)
            return False

        items1 = list(roi_dict1.items())
        items2 = list(roi_dict2.items())
        rois1 = [it[1] for it in items1]
        rois2 = [it[1] for it in items2]
        names2 = [it[0] for it in items2]

        if len(rois1) == 0 or len(rois2) == 0:
            logger.error("One or both ROI files contain no ROIs")
            return False

        matching_indices = self._match_rois(rois1, rois2)

        # Reorder raw bytes according to matching
        reordered_bytes = []
        for idx in matching_indices:
            if idx < len(names2):
                key = names2[idx]
                reordered_bytes.append(roi_bytes2[key])

        # Backup original second file
        backup = FilePath.from_string(str(zip_file2) + ".bak")
        try:
            if not self.storage.file_exists(backup):
                # Use storage adapter for a safe copy
                self.storage.copy_file(zip_file2, backup)
        except Exception:
            # If backup via storage fails, attempt OS-level rename as fallback
            try:
                Path(str(zip_file2)).rename(str(backup))
            except Exception:
                logger.warning("Failed to create backup for %s; proceeding.", zip_file2)

        # Write the reordered zip over the original target path
        return self._save_zip_from_bytes(reordered_bytes, zip_file2)

    def batch_process_directory(
        self, directory: FilePath, t0: str, t1: str, recursive: bool = True
    ) -> int:
        """Find and process all matching ROI pairs in a directory."""
        pairs = self.find_roi_files_recursive(directory, t0, t1) if recursive else []
        if not pairs:
            logger.warning("No matching ROI pairs found in %s", directory)
            return 0

        successful = 0
        for file1, file2 in pairs:
            if self.process_roi_pair(file1, file2):
                successful += 1
        logger.info("Successfully processed %d out of %d ROI file pairs", successful, len(pairs))
        return successful

    def find_roi_files_recursive(self, directory: FilePath, t0: str, t1: str) -> List[Tuple[FilePath, FilePath]]:
        """
        Recursively find pairs of ROI zip files matching t0 and t1 timepoints based on common filename prefixes.
        """
        t0_pattern = f"**/*{t0}*_rois.zip"
        t1_pattern = f"**/*{t1}*_rois.zip"
        logger.info(
            "Searching for ROI pairs in '%s' using timepoints '%s' -> '%s'",
            directory,
            t0,
            t1,
        )
        logger.debug("Patterns: T0=%s T1=%s", t0_pattern, t1_pattern)

        t0_files = self.storage.list_files(directory, pattern=t0_pattern, recursive=True)
        t1_files = self.storage.list_files(directory, pattern=t1_pattern, recursive=True)

        logger.info("Found %d files matching %s", len(t0_files), t0)
        logger.info("Found %d files matching %s", len(t1_files), t1)

        t1_map = {str(f): f for f in t1_files}
        pairs: List[Tuple[FilePath, FilePath]] = []

        for f0 in t0_files:
            f0_str = str(f0)
            candidate = FilePath.from_string(f0_str.replace(t0, t1))

            matched = False
            # Heuristic with metadata service (future improvements could use region/condition constraints)
            try:
                scan_dir = f0.get_parent()
                _ = self.metadata_service.scan_directory_for_metadata(scan_dir, recursive=False)
                if str(candidate) in t1_map:
                    pairs.append((f0, candidate))
                    matched = True
            except Exception:
                pass

            if matched:
                continue
            # Simple replacement fallback
            if t0 not in f0_str:
                logger.debug("Timepoint '%s' not in path '%s'", t0, f0_str)
                continue
            if str(candidate) in t1_map:
                pairs.append((f0, candidate))
            else:
                logger.warning("Could not find matching %s file for %s (expected: %s)", t1, f0, candidate)

        logger.info("Found %d matching ROI pairs.", len(pairs))
        return pairs

    # ---- Internal helpers ----
    def _load_roi_dict(self, zip_file_path: FilePath):
        try:
            return read_roi_zip(str(zip_file_path))
        except Exception as e:
            logger.error("Error loading ROI file %s: %s", zip_file_path, e)
            return None

    def _load_roi_bytes(self, zip_file_path: FilePath):
        roi_bytes = {}
        try:
            with zipfile.ZipFile(str(zip_file_path), 'r') as z:
                for name in z.namelist():
                    key = name[:-4] if name.lower().endswith('.roi') else name
                    roi_bytes[key] = z.read(name)
            return roi_bytes
        except Exception as e:
            logger.error("Error loading ROI bytes from %s: %s", zip_file_path, e)
            return None

    def _polygon_centroid(self, x: List[float], y: List[float]) -> Tuple[float, float]:
        A = 0.0
        Cx = 0.0
        Cy = 0.0
        n = len(x) - 1
        for i in range(n):
            cross = x[i] * y[i + 1] - x[i + 1] * y[i]
            A += cross
            Cx += (x[i] + x[i + 1]) * cross
            Cy += (y[i] + y[i + 1]) * cross
        A *= 0.5
        if abs(A) < 1e-8:
            return (sum(x[:-1]) / n, sum(y[:-1]) / n)
        Cx /= (6 * A)
        Cy /= (6 * A)
        return (Cx, Cy)

    def _get_roi_center(self, roi: dict) -> Tuple[float, float]:
        if 'x' in roi and 'y' in roi:
            x = list(roi['x'])
            y = list(roi['y'])
            if x[0] != x[-1] or y[0] != y[-1]:
                x.append(x[0])
                y.append(y[0])
            return self._polygon_centroid(x, y)
        elif all(k in roi for k in ['left', 'top', 'width', 'height']):
            return (roi['left'] + roi['width'] / 2, roi['top'] + roi['height'] / 2)
        elif all(k in roi for k in ['left', 'top', 'right', 'bottom']):
            w = roi['right'] - roi['left']
            h = roi['bottom'] - roi['top']
            return (roi['left'] + w / 2, roi['top'] + h / 2)
        else:
            raise ValueError("ROI dictionary missing expected keys.")

    def _match_rois(self, roi_list1: List[dict], roi_list2: List[dict]) -> List[int]:
        n = min(len(roi_list1), len(roi_list2))
        roi_subset1 = roi_list1[:n]
        roi_subset2 = roi_list2[:n]

        cost = np.zeros((n, n))
        centers1 = [self._get_roi_center(roi) for roi in roi_subset1]
        centers2 = [self._get_roi_center(roi) for roi in roi_subset2]
        for i in range(n):
            for j in range(n):
                cost[i, j] = np.linalg.norm(np.array(centers1[i]) - np.array(centers2[j]))

        _, col_ind = linear_sum_assignment(cost)
        # If second list longer, pad sequentially (keeps extras in order)
        if len(roi_list2) > len(roi_list1):
            extra = list(range(n, len(roi_list2)))
            return list(col_ind) + extra
        return list(col_ind)

    def _save_zip_from_bytes(self, roi_bytes_list: List[bytes], output_zip_path: FilePath) -> bool:
        try:
            # Ensure parent exists
            output_zip_path.get_parent().mkdir(parents=True, exist_ok=True)
            with zipfile.ZipFile(str(output_zip_path), 'w') as z:
                for i, data in enumerate(roi_bytes_list):
                    name = f"ROI_{i+1:03d}.roi"
                    z.writestr(name, data)
            logger.info("Saved reordered ROIs to %s", output_zip_path)
            return True
        except Exception as e:
            logger.error("Error saving zip file %s: %s", output_zip_path, e)
            return False


