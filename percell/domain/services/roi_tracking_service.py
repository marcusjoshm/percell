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
import numpy as np
from scipy.optimize import linear_sum_assignment
 

from percell.domain.value_objects.file_path import FilePath
from percell.domain.services.metadata_service import MetadataService
from percell.ports.outbound.storage_port import StoragePort
from percell.domain.entities.roi import ROI


 


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
        rois1 = self._load_rois(zip_file1)
        rois2 = self._load_rois(zip_file2)
        if rois1 is None or rois2 is None:
            return False

        items2 = list(rois2)

        if len(rois1) == 0 or len(rois2) == 0:
            return False

        matching_indices = self._match_rois(rois1, rois2)

        # Reorder ROI entities from the second file according to matching
        reordered_rois: List[ROI] = []
        for idx in matching_indices:
            if idx < len(items2):
                reordered_rois.append(items2[idx])

        # Backup original second file
        backup = FilePath.from_string(str(zip_file2) + ".bak")
        try:
            if not self.storage.file_exists(backup):
                self.storage.copy_file(zip_file2, backup)
        except Exception:
            pass

        # Write the reordered ROIs over the original target path
        return self._save_reordered_rois(reordered_rois, zip_file2)

    def batch_process_directory(
        self, directory: FilePath, t0: str, t1: str, recursive: bool = True
    ) -> int:
        """Find and process all matching ROI pairs in a directory."""
        pairs = self.find_roi_files_recursive(directory, t0, t1) if recursive else []
        if not pairs:
            return 0

        successful = 0
        for file1, file2 in pairs:
            if self.process_roi_pair(file1, file2):
                successful += 1
        return successful

    def find_roi_files_recursive(self, directory: FilePath, t0: str, t1: str) -> List[Tuple[FilePath, FilePath]]:
        """
        Recursively find pairs of ROI zip files matching t0 and t1 timepoints based on common filename prefixes.
        """
        t0_pattern = f"**/*{t0}*_rois.zip"
        t1_pattern = f"**/*{t1}*_rois.zip"
        t0_files = self.storage.list_files(directory, pattern=t0_pattern, recursive=True)
        t1_files = self.storage.list_files(directory, pattern=t1_pattern, recursive=True)

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
                continue
            if str(candidate) in t1_map:
                pairs.append((f0, candidate))
            else:
                pass

        return pairs

    # ---- Internal helpers ----
    def _load_rois(self, zip_file_path: FilePath) -> Optional[List[ROI]]:
        try:
            return self.storage.read_roi_file(zip_file_path)
        except Exception:
            return None

    def _get_roi_center_from_entity(self, roi: ROI) -> Tuple[float, float]:
        if roi.centroid is not None:
            return roi.centroid
        if roi.coordinates:
            x = [p[0] for p in roi.coordinates]
            y = [p[1] for p in roi.coordinates]
            if x[0] != x[-1] or y[0] != y[-1]:
                x.append(x[0])
                y.append(y[0])
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
        if roi.bounding_box is not None:
            x, y, w, h = roi.bounding_box
            return (x + w / 2.0, y + h / 2.0)
        return (0.0, 0.0)

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

    def _match_rois(self, roi_list1: List[ROI], roi_list2: List[ROI]) -> List[int]:
        n = min(len(roi_list1), len(roi_list2))
        roi_subset1 = roi_list1[:n]
        roi_subset2 = roi_list2[:n]

        cost = np.zeros((n, n))
        centers1 = [self._get_roi_center_from_entity(roi) for roi in roi_subset1]
        centers2 = [self._get_roi_center_from_entity(roi) for roi in roi_subset2]
        for i in range(n):
            for j in range(n):
                cost[i, j] = np.linalg.norm(np.array(centers1[i]) - np.array(centers2[j]))

        _, col_ind = linear_sum_assignment(cost)
        # If second list longer, pad sequentially (keeps extras in order)
        if len(roi_list2) > len(roi_list1):
            extra = list(range(n, len(roi_list2)))
            return list(col_ind) + extra
        return list(col_ind)

    def _save_reordered_rois(self, rois: List[ROI], output_zip_path: FilePath) -> bool:
        try:
            parent = output_zip_path.get_parent()
            if not self.storage.directory_exists(parent):
                self.storage.create_directory(parent)
            self.storage.write_roi_file(rois, output_zip_path)
            return True
        except Exception:
            return False


