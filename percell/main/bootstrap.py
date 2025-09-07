from __future__ import annotations

from pathlib import Path

from percell.application.container import build_container


def bootstrap(config_path: str | Path):
    """Build and return the DI container for the application."""
    return build_container(Path(config_path))


