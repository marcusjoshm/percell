from __future__ import annotations

from dataclasses import dataclass
from typing import Dict
import numpy as np


@dataclass(frozen=True)
class CellMask:
    image_data: np.ndarray
    metadata: Dict[str, object]


@dataclass(frozen=True)
class AnalysisParams:
    threshold_method: str
    min_area: float


