from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional

import pandas as pd


class MetadataStorePort(ABC):
    """Driven port for CSV/metadata storage operations."""

    @abstractmethod
    def read_csv(self, path: Path) -> pd.DataFrame:
        """Read a CSV into a DataFrame."""

    @abstractmethod
    def write_csv(self, path: Path, df: pd.DataFrame, index: bool = False) -> None:
        """Write a DataFrame to CSV."""

    @abstractmethod
    def merge_csv(
        self,
        left_path: Path,
        right_path: Path,
        on: str,
        how: str,
        output_path: Optional[Path] = None,
    ) -> pd.DataFrame:
        """Merge two CSVs on a key with `how` and optionally write to output_path."""


