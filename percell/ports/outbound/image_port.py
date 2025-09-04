from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

import numpy as np


class ImageReaderPort(ABC):
    """Driven port for reading images from storage.

    Implementations should provide filesystem/library-specific reading logic
    while keeping the interface stable for application/domain layers.
    """

    @abstractmethod
    def read(self, path: Path) -> np.ndarray:
        """Read an image from the given path and return a numpy array."""

    @abstractmethod
    def read_with_metadata(self, path: Path) -> Tuple[np.ndarray, Dict[str, Any]]:
        """Read an image and return the array along with a metadata dictionary."""


class ImageWriterPort(ABC):
    """Driven port for writing images to storage.

    Implementations should handle persistence details and optional metadata.
    """

    @abstractmethod
    def write(self, path: Path, image: np.ndarray, metadata: Optional[Dict[str, Any]] = None) -> None:
        """Write an image (and optional metadata) to the given path."""


