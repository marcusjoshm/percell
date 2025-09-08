from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Sequence


@dataclass(slots=True)
class PackageResourceService:
    """Pure domain logic for locating package resources relative to a root.

    This encapsulates the core path-derivation logic that previously lived in
    `core/utils.py` without performing any I/O beyond `exists()` checks.
    """

    package_root: Path

    def verify_root(self, expected_dirs: Sequence[str] = ("bash", "config", "macros")) -> bool:
        """Verify the package root contains required resource directories.

        The legacy layout included a 'modules' directory, which has been
        migrated into the application layer. We no longer require 'modules'
        for a valid package root. Extra directories are ignored.
        """
        return all((self.package_root / d).exists() for d in expected_dirs)

    def resource(self, relative_path: str) -> Path:
        p = self.package_root / relative_path
        if not p.exists():
            raise FileNotFoundError(f"Package resource not found: {relative_path} (searched in {self.package_root})")
        return p

    def bash(self, script_name: str) -> Path:
        return self.resource(f"bash/{script_name}")

    def config(self, config_name: str) -> Path:
        return self.resource(f"config/{config_name}")

    def macro(self, macro_name: str) -> Path:
        return self.resource(f"macros/{macro_name}")


