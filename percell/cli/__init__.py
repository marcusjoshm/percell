"""CLI adapter layer."""

from .app import create_cli, parse_arguments  # re-export for convenience

__all__ = ["create_cli", "parse_arguments"]

