from __future__ import annotations

from pathlib import Path
from typing import Protocol, Tuple

import numpy as np


class ImageProcessingPort(Protocol):
    """Driven port for image manipulation (binning/resizing/format conversions)."""

    def read_image(self, path: Path) -> np.ndarray:
        ...

    def write_image(self, path: Path, image: np.ndarray) -> None:
        ...

    def bin_image(self, image: np.ndarray, factor: int) -> np.ndarray:
        ...

    def resize(self, image: np.ndarray, target_hw: Tuple[int, int]) -> np.ndarray:
        ...


