from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import List


class DataType(Enum):
    """Type of dataset being processed."""

    SINGLE_TIMEPOINT = "single"
    MULTI_TIMEPOINT = "multi"


@dataclass(frozen=True)
class Channel:
    """Represents an image channel and its roles in the workflow."""

    name: str
    is_segmentation: bool = False
    is_analysis: bool = False


@dataclass(frozen=True)
class Timepoint:
    """Represents a timepoint with a stable order index."""

    id: str
    order: int


@dataclass(frozen=True)
class Region:
    """Represents a spatial region identifier within an experiment."""

    id: str
    name: str


@dataclass(frozen=True)
class Condition:
    """Represents an experimental condition label."""

    name: str


@dataclass(frozen=True)
class ExperimentSelection:
    """Immutable selection of experiment context for a run."""

    data_type: DataType
    input_dir: Path
    output_dir: Path
    conditions: List[Condition]
    channels: List[Channel]
    timepoints: List[Timepoint]
    regions: List[Region]


