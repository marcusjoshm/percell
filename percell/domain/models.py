"""Domain models and value objects for PerCell.

These dataclasses and enums define the core business entities of the
application and are intentionally free of infrastructure concerns.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, auto
from pathlib import Path
from typing import Any, Mapping, Optional, Sequence, Tuple


class WorkflowStep(Enum):
    """Enumerates the high-level workflow steps in PerCell."""

    DATA_SELECTION = auto()
    SEGMENTATION = auto()
    PROCESSING = auto()
    THRESHOLDING = auto()
    ANALYSIS = auto()


class WorkflowState(Enum):
    """Represents the state of a workflow execution."""

    PENDING = auto()
    RUNNING = auto()
    COMPLETED = auto()
    FAILED = auto()


class FileOperationType(Enum):
    """Types of file operations the application may perform."""

    COPY = auto()
    MOVE = auto()
    RENAME = auto()
    DELETE = auto()


@dataclass(slots=True)
class FileMetadata:
    """Metadata parsed from microscopy filenames.

    Attributes:
        original_name: The original filename including extension.
        path: Optional absolute file path of the asset.
        condition: Experimental condition identifier.
        timepoint: Timepoint identifier.
        region: Region/field identifier.
        channel: Imaging channel identifier.
        z_index: Z-stack index when applicable.
        extension: File extension including the dot (e.g., ".tif").
    """

    original_name: str
    path: Optional[Path] = None
    condition: Optional[str] = None
    timepoint: Optional[str] = None
    region: Optional[str] = None
    channel: Optional[str] = None
    z_index: Optional[int] = None
    extension: Optional[str] = None


@dataclass(slots=True)
class ChannelConfig:
    """Configuration describing an imaging channel.

    Attributes:
        name: Human-friendly channel name.
        index: Optional numeric index used in stacks.
        role: Optional semantic role (e.g., "nucleus", "cytoplasm").
        is_primary: Whether this channel acts as the primary reference.
    """

    name: str
    index: Optional[int] = None
    role: Optional[str] = None
    is_primary: bool = False


@dataclass(slots=True)
class DatasetSelection:
    """Represents a user's dataset selection and filters.

    Attributes:
        root: Root directory containing the dataset.
        files: Concrete list of files participating in the workflow.
        conditions: Selected condition identifiers.
        timepoints: Selected timepoint identifiers.
        regions: Selected region identifiers.
        channels: Selected channels to process.
    """

    root: Path
    files: list[Path] = field(default_factory=list)
    conditions: list[str] = field(default_factory=list)
    timepoints: list[str] = field(default_factory=list)
    regions: list[str] = field(default_factory=list)
    channels: list[str] = field(default_factory=list)


@dataclass(slots=True)
class CellMetrics:
    """Per-cell measurements produced by analysis.

    Attributes:
        cell_id: Unique identifier of the cell within an image.
        area: Area of the cell in pixels.
        mean_intensity: Mean pixel intensity within the cell.
        integrated_intensity: Optional sum of intensities.
        perimeter: Optional perimeter length in pixels.
        bbox: Optional bounding box (x, y, width, height).
    """

    cell_id: int
    area: float
    mean_intensity: float
    integrated_intensity: Optional[float] = None
    perimeter: Optional[float] = None
    bbox: Optional[Tuple[int, int, int, int]] = None


@dataclass(slots=True)
class ROI:
    """Region of interest representing a cell or object boundary.

    Attributes:
        id: ROI identifier.
        label: Optional label describing the ROI.
        polygon: Optional list of (x, y) vertices.
        mask_path: Optional path to a binary mask file representing the ROI.
    """

    id: int
    label: Optional[str] = None
    polygon: Optional[list[Tuple[int, int]]] = None
    mask_path: Optional[Path] = None


@dataclass(slots=True)
class ThresholdParameters:
    """Parameters for thresholding logic.

    Attributes:
        method: Thresholding method identifier (e.g., "otsu").
        lower: Optional lower threshold bound.
        upper: Optional upper threshold bound.
        params: Additional method-specific parameters.
    """

    method: str
    lower: Optional[float] = None
    upper: Optional[float] = None
    params: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class IntensityGroup:
    """Grouping of cells by brightness or other criteria.

    Attributes:
        name: Group label (e.g., "bright", "dim").
        members: List of cell identifiers belonging to this group.
        range_min: Optional lower bound used to define the group.
        range_max: Optional upper bound used to define the group.
    """

    name: str
    members: list[int] = field(default_factory=list)
    range_min: Optional[float] = None
    range_max: Optional[float] = None


@dataclass(slots=True)
class FileOperation:
    """Describes a file system operation to perform.

    Attributes:
        op: The type of file operation.
        src: Source path of the operation.
        dst: Optional destination path (required for copy/move/rename).
        overwrite: Whether to overwrite if destination exists.
    """

    op: FileOperationType
    src: Path
    dst: Optional[Path] = None
    overwrite: bool = False


@dataclass(slots=True)
class AnalysisResult:
    """Aggregated analysis results.

    Attributes:
        metrics: Collection of per-cell metrics.
        csv_path: Optional path to a generated CSV summary.
        summary: Optional aggregate statistics by group or channel.
    """

    metrics: list[CellMetrics] = field(default_factory=list)
    csv_path: Optional[Path] = None
    summary: Optional[Mapping[str, Any]] = None


@dataclass(slots=True)
class WorkflowConfig:
    """Configuration for controlling workflow execution.

    Attributes:
        steps: Ordered list of workflow steps to execute.
        allow_custom: Whether to allow non-default step orders.
        stop_on_error: Whether to stop execution on first error.
    """

    steps: list[WorkflowStep]
    allow_custom: bool = False
    stop_on_error: bool = True


