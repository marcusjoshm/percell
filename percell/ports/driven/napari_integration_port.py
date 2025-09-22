from __future__ import annotations

from pathlib import Path
from typing import Protocol, List, Optional


class NapariIntegrationPort(Protocol):
    """Driven port for invoking Napari visualization."""

    def launch_viewer(
        self,
        images: Optional[List[Path]] = None,
        masks: Optional[List[Path]] = None,
        working_dir: Optional[Path] = None,
    ) -> None:
        """Launch Napari viewer with optional images and masks."""
        ...