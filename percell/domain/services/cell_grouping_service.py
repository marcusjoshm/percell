from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable, List, Sequence

import numpy as np


@dataclass(frozen=True)
class GroupingParameters:
    """Parameters controlling grouping behavior.

    Mirrors `BinningParameters` but scoped to the service to avoid coupling.
    """

    num_bins: int
    strategy: str  # "uniform" | "kmeans" | "gmm"


class CellGroupingService:
    """Pure domain service for cell grouping logic."""

    def compute_auc(self, intensity_profile: np.ndarray) -> float:
        """Compute area under the curve as a discrete sum.

        This aligns with existing expectations in the project where the
        intensity profile AUC is computed as the sum of samples.
        """
        if intensity_profile.ndim != 1:
            raise ValueError("Intensity profile must be a 1D array")
        return float(np.sum(intensity_profile.astype(float)))

    def group_by_intensity(self, intensities: Sequence[float], params: GroupingParameters) -> List[int]:
        """Assign each intensity to a group according to the chosen strategy."""
        if params.num_bins <= 0:
            raise ValueError("num_bins must be positive")
        if params.strategy == "uniform":
            return self._uniform_bins(intensities, params.num_bins)
        elif params.strategy == "kmeans":
            return self._kmeans_bins(intensities, params.num_bins)
        elif params.strategy == "gmm":
            return self._gmm_bins(intensities, params.num_bins)
        else:
            raise ValueError(f"Unknown strategy: {params.strategy}")

    def aggregate_by_group(self, cell_images: Sequence[np.ndarray], assignments: Sequence[int]) -> Dict[int, np.ndarray]:
        """Sum cell images within each assigned group (pure numpy)."""
        if len(cell_images) != len(assignments):
            raise ValueError("cell_images and assignments must have same length")
        assignments = np.asarray(assignments)
        unique_groups = np.unique(assignments)
        aggregated: Dict[int, np.ndarray] = {}
        for g in unique_groups:
            mask = assignments == g
            if not np.any(mask):
                continue
            selected = [img for img, m in zip(cell_images, mask) if m]
            aggregated[int(g)] = np.sum(np.stack(selected, axis=0), axis=0)
        return aggregated

    # --- helpers ---

    def _uniform_bins(self, intensities: Sequence[float], num_bins: int) -> List[int]:
        vals = np.asarray(intensities, dtype=float)
        if vals.size == 0:
            return []
        # Edge case: constant intensities
        if np.all(vals == vals[0]):
            return [0 for _ in vals]
        edges = np.linspace(vals.min(), vals.max(), num_bins + 1)
        # rightmost edge inclusive
        indices = np.digitize(vals, edges[1:-1], right=True)
        return indices.tolist()

    def _kmeans_bins(self, intensities: Sequence[float], num_bins: int) -> List[int]:
        try:
            from sklearn.cluster import KMeans  # type: ignore
        except Exception as exc:  # pragma: no cover - optional dep
            raise RuntimeError("kmeans strategy requires scikit-learn") from exc
        vals = np.asarray(intensities, dtype=float).reshape(-1, 1)
        model = KMeans(n_clusters=num_bins, n_init=10, random_state=0)
        labels = model.fit_predict(vals)
        return labels.tolist()

    def _gmm_bins(self, intensities: Sequence[float], num_bins: int) -> List[int]:
        try:
            from sklearn.mixture import GaussianMixture  # type: ignore
        except Exception as exc:  # pragma: no cover - optional dep
            raise RuntimeError("gmm strategy requires scikit-learn") from exc
        vals = np.asarray(intensities, dtype=float).reshape(-1, 1)
        model = GaussianMixture(n_components=num_bins, covariance_type="full", random_state=0)
        labels = model.fit_predict(vals)
        return labels.tolist()


