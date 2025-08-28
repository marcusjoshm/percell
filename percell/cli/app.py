from __future__ import annotations

# Adapter that forwards to the existing core CLI to decouple callers from core
from percell.core.cli import create_cli as _create_core_cli
from percell.core.cli import parse_arguments as _parse_core_arguments


def create_cli():
    return _create_core_cli()


def parse_arguments():
    return _parse_core_arguments()


__all__ = ["create_cli", "parse_arguments"]


