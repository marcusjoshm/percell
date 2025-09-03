"""
CellGroupingService

Domain service for grouping cell images by intensity (AUC) into bins,
resizing to common dimensions per group, summing, and writing outputs.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable, List, Optional, Sequence, Tuple
import numpy as np
 

 

from percell.domain.value_objects.file_path import FilePath
from percell.ports.outbound.storage_port import StoragePort
from percell.domain.services.metadata_service import MetadataService


 


@dataclass
class GroupingConfig:
    bins: int = 5
    force_clusters: bool = False
    channels: Optional[Sequence[str]] = None


class CellGroupingService:
    """Encapsulates grouping logic independent of concrete storage or tools."""

    def __init__(self, storage: StoragePort, metadata_service: MetadataService) -> None:
        self.storage = storage
        self.metadata_service = metadata_service

    # ---- Public API ----
    def process_all(
        self,
        cells_dir: FilePath,
        output_dir: FilePath,
        config: GroupingConfig,
    ) -> int:
        """Process all cell directories under `cells_dir` and group cell images."""
        # Ensure output root exists
        if not self.storage.directory_exists(output_dir):
            self.storage.create_directory(output_dir)

        # Discover candidate cell directories (contain CELL*.tif)
        candidate_dirs = self._find_cell_directories(cells_dir)
        if not candidate_dirs:
            return 0

        processed = 0
        for cell_dir in candidate_dirs:
            if not self._should_process_directory(cell_dir, config.channels):
                continue
            if self._group_and_sum_cells(cell_dir, output_dir, config):
                processed += 1

        return processed

    # ---- Internals ----
    def _find_cell_directories(self, cells_dir: FilePath) -> List[FilePath]:
        result: List[FilePath] = []
        for directory in self.storage.list_directories(cells_dir, recursive=True):
            cell_files = self.storage.list_files(directory, pattern="CELL*.tif", recursive=False)
            if cell_files:
                result.append(directory)
        return result

    def _should_process_directory(self, directory: FilePath, channels: Optional[Sequence[str]]) -> bool:
        if not channels:
            return True
        try:
            md_list = self.metadata_service.scan_directory_for_metadata(directory, recursive=True)
            chan_set = {m.channel for m in md_list if getattr(m, 'channel', None)}
            if any(ch in chan_set for ch in channels):
                return True
        except Exception:
            pass
        # Fallback: simple substring in path
        directory_str = str(directory).lower()
        for ch in channels:
            if ch.lower() in directory_str:
                return True
        return False

    def _read_image(self, path: FilePath) -> Optional[np.ndarray]:
        try:
            img = self.storage.read_image(path)
            # Convert to grayscale if multi-channel
            if img is not None and img.ndim > 2:
                img = np.mean(img, axis=2).astype(img.dtype)
            return img
        except Exception:
            return None

    def _compute_auc(self, img: np.ndarray) -> float:
        return float(np.sum(img))

    def _resize_to_target(self, img: np.ndarray, target_height: int, target_width: int) -> np.ndarray:
        """Resize image to fit within target (H, W) using nearest-neighbor and pad to center.
        Pure NumPy implementation to avoid external dependencies.
        """
        height, width = img.shape[:2]
        if height == 0 or width == 0 or target_height == 0 or target_width == 0:
            return np.zeros((target_height, target_width), dtype=img.dtype)

        img_aspect = width / max(1, height)
        target_aspect = target_width / max(1, target_height)

        if img_aspect > target_aspect:
            new_width = target_width
            new_height = max(1, int(round(new_width / img_aspect)))
        else:
            new_height = target_height
            new_width = max(1, int(round(new_height * img_aspect)))

        # Nearest-neighbor resize via index mapping
        y_indices = (np.linspace(0, height - 1, new_height)).astype(int)
        x_indices = (np.linspace(0, width - 1, new_width)).astype(int)
        resized = img[np.ix_(y_indices, x_indices)]

        # Center-pad into target canvas
        result = np.zeros((target_height, target_width), dtype=img.dtype)
        pad_top = (target_height - new_height) // 2
        pad_left = (target_width - new_width) // 2
        result[pad_top:pad_top + new_height, pad_left:pad_left + new_width] = resized
        return result

    def _cluster_labels(
        self,
        auc_values: np.ndarray,
        bins: int,
        force_clusters: bool,
    ) -> Tuple[np.ndarray, Dict[int, float]]:
        """Return labels and cluster means (using original auc scale)."""
        n = len(auc_values)
        actual_bins = min(bins, n)
        if n == 0 or actual_bins == 0:
            return np.array([], dtype=int), {}

        zero_count = int(np.sum(auc_values == 0))
        intensity_range = float(np.max(auc_values) - np.min(auc_values)) if n > 0 else 0.0

        # Log-transform for stability when positive
        auc_log = np.log1p(auc_values) if np.min(auc_values) > 0 else auc_values.copy()

        # Force equal bins if requested in degenerate cases
        if (zero_count == n or intensity_range < 1e-6) and force_clusters:
            sorted_idx = np.argsort(auc_values)
            cells_per = n // actual_bins
            rem = n % actual_bins
            labels = np.zeros(n, dtype=int)
            start = 0
            for i in range(actual_bins):
                size = cells_per + (1 if i < rem else 0)
                end = start + size
                labels[sorted_idx[start:end]] = i
                start = end
            means = {i: float(np.mean(auc_values[labels == i])) if np.any(labels == i) else 0.0 for i in range(actual_bins)}
            return labels, means

        # Pure NumPy k-means (Lloyd's algorithm) with k-means++ init
        rng = np.random.default_rng(0)
        data = auc_log.reshape(-1, 1)
        k = actual_bins

        # k-means++ initialization
        centers = np.empty((k, 1), dtype=float)
        centers[0] = data[rng.integers(0, n)]
        closest_dist_sq = ((data - centers[0]) ** 2).sum(axis=1)
        for ci in range(1, k):
            probs = closest_dist_sq / closest_dist_sq.sum() if closest_dist_sq.sum() > 0 else np.ones(n) / n
            idx = rng.choice(n, p=probs)
            centers[ci] = data[idx]
            dist_sq = ((data - centers[ci]) ** 2).sum(axis=1)
            closest_dist_sq = np.minimum(closest_dist_sq, dist_sq)

        labels = np.zeros(n, dtype=int)
        max_iters = 100
        for _ in range(max_iters):
            # Assign step
            dists = np.square(data - centers.T)  # shape (n, k)
            new_labels = np.argmin(dists, axis=1)
            if np.array_equal(new_labels, labels):
                break
            labels = new_labels
            # Update step
            for ci in range(k):
                mask = labels == ci
                if np.any(mask):
                    centers[ci] = data[mask].mean(axis=0)
                else:
                    # Reinitialize empty cluster to random point
                    centers[ci] = data[rng.integers(0, n)]

        unique = np.unique(labels)
        means = {int(l): float(np.mean(auc_values[labels == l])) for l in unique}

        if force_clusters and len(unique) < k:
            # Redistribute evenly by sorted intensity
            sorted_idx = np.argsort(auc_values)
            cells_per = n // k
            rem = n % k
            new_labels = np.zeros_like(labels)
            start = 0
            for i in range(k):
                size = cells_per + (1 if i < rem else 0)
                end = start + size
                new_labels[sorted_idx[start:end]] = i
                start = end
            labels = new_labels
            means = {i: float(np.mean(auc_values[labels == i])) if np.any(labels == i) else 0.0 for i in range(k)}

        return labels, means

    def _group_and_sum_cells(self, cell_dir: FilePath, output_root: FilePath, config: GroupingConfig) -> bool:
        image_files = self.storage.list_files(cell_dir, pattern="CELL*.tif", recursive=False)
        if not image_files:
            return False

        # Read images and compute AUC
        image_data: List[Tuple[FilePath, float, np.ndarray]] = []
        zero_count = 0
        for fp in image_files:
            img = self._read_image(fp)
            if img is None:
                continue
            auc = self._compute_auc(img)
            if auc == 0:
                zero_count += 1
            image_data.append((fp, auc, img))

        if not image_data:
            return False

        auc_values = np.array([d[1] for d in image_data], dtype=float)
        labels, cluster_means = self._cluster_labels(auc_values, config.bins, config.force_clusters)
        if labels.size == 0:
            return False

        # Sort clusters by mean intensity for consistent binning
        sorted_clusters = sorted(cluster_means, key=lambda k: cluster_means[k]) if cluster_means else list(range(config.bins))
        label_mapping = {old_label: new_label for new_label, old_label in enumerate(sorted_clusters)}

        # Determine max dimensions per group
        actual_bins = max(label_mapping.values()) + 1 if label_mapping else config.bins
        group_dims: Dict[int, Tuple[int, int]] = {i: (0, 0) for i in range(actual_bins)}
        for idx, (_, _, img) in enumerate(image_data):
            original = int(labels[idx])
            mapped = label_mapping.get(original, original % actual_bins)
            h, w = img.shape[:2]
            mh, mw = group_dims[mapped]
            group_dims[mapped] = (max(mh, h), max(mw, w))

        # Sum images per group
        sum_images: List[Optional[np.ndarray]] = [None] * actual_bins
        cell_counts: List[int] = [0] * actual_bins
        for idx, (fp, _, img) in enumerate(image_data):
            original = int(labels[idx])
            mapped = label_mapping.get(original, original % actual_bins)
            th, tw = group_dims[mapped]
            if th == 0 or tw == 0:
                continue
            resized = self._resize_to_target(img, th, tw)
            if sum_images[mapped] is None:
                sum_images[mapped] = np.zeros((th, tw), dtype=np.float64)
            sum_images[mapped] = sum_images[mapped] + resized.astype(np.float64)
            cell_counts[mapped] += 1

        # Output directory mirrors input structure
        output_subdir = output_root.join(cell_dir.get_parent().get_name()).join(cell_dir.get_name())
        if not self.storage.directory_exists(output_subdir):
            self.storage.create_directory(output_subdir)

        # Save group images (normalize to 16-bit range)
        for i, sum_img in enumerate(sum_images):
            if sum_img is None:
                continue
            min_val = float(np.min(sum_img))
            max_val = float(np.max(sum_img))
            if max_val - min_val <= 1e-12:
                norm = np.zeros_like(sum_img, dtype=np.uint16)
            else:
                scaled = (sum_img - min_val) / (max_val - min_val)
                norm = (scaled * 65535.0).clip(0, 65535).astype(np.uint16)
            out_name = f"{cell_dir.get_name()}_bin_{i+1}.tif"
            out_path = output_subdir.join(out_name)
            try:
                self.storage.write_image(norm, out_path)
            except Exception:
                pass

        # Write info text
        info_lines = [
            f"Cell directory: {cell_dir}\n",
            f"Number of cells: {len(image_data)}\n",
            f"Clustering: bins={config.bins} force={config.force_clusters}\n",
            f"Images with zero intensity: {zero_count}\n",
        ]
        for i in range(actual_bins):
            info_lines.append(f"Group {i+1}: cells={cell_counts[i]}\n")
        try:
            self.storage.write_text_file("".join(info_lines), output_subdir.join(f"{cell_dir.get_name()}_grouping_info.txt"))
        except Exception:
            pass

        # Write CSV mapping
        try:
            header = "cell_filename,cell_id,group_id,group_name,group_mean_auc,cell_auc\n"
            rows = [header]
            for idx, (fp, auc, _) in enumerate(image_data):
                original = int(labels[idx])
                mapped = label_mapping.get(original, original % actual_bins) + 1
                base = fp.get_name().replace('.tif', '')
                # Extract numeric id if prefixed with CELL
                cell_id = ''.join(c for c in base if c.isdigit()) or base
                mean_auc = 0.0
                if original in cluster_means:
                    mean_auc = float(cluster_means[original])
                rows.append(f"{fp},{cell_id},{mapped},Group_{mapped},{mean_auc:.6f},{auc:.6f}\n")
            self.storage.write_text_file("".join(rows), output_subdir.join(f"{cell_dir.get_name()}_cell_groups.csv"))
        except Exception:
            pass

        return True


