from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Protocol

import numpy as np

from percell.domain.value_objects.processing import SegmentationParameters


class SegmenterPort(ABC):
    """Driven port for running cell segmentation on an image array."""

    @abstractmethod
    def segment(self, image: np.ndarray, parameters: SegmentationParameters) -> np.ndarray:
        """Return a label mask (int array) for the given image and parameters."""


