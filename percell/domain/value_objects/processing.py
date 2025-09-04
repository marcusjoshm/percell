from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class BinningParameters:
    """Parameters controlling cell intensity binning."""

    num_bins: int
    strategy: str  # "gmm", "kmeans", "uniform"


@dataclass(frozen=True)
class SegmentationParameters:
    """Parameters controlling segmentation behavior."""

    model: str
    diameter: float
    flow_threshold: float
    cellprob_threshold: float


