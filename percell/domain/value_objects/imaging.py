from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ImageDimensions:
    """Immutable image geometry."""

    width: int
    height: int
    channels: int = 1


@dataclass(frozen=True)
class Resolution:
    """Physical pixel resolution."""

    x: float
    y: float
    units: str = "pixel"  # e.g., "um"


