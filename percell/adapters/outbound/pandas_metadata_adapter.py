from __future__ import annotations

from pathlib import Path
from typing import Optional

import pandas as pd

from percell.ports.outbound.metadata_port import MetadataStorePort


class PandasMetadataAdapter(MetadataStorePort):
    """Pandas-based implementation of metadata storage operations."""

    def read_csv(self, path: Path) -> pd.DataFrame:
        return pd.read_csv(path)

    def write_csv(self, path: Path, df: pd.DataFrame, index: bool = False) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(path, index=index)

    def merge_csv(
        self,
        left_path: Path,
        right_path: Path,
        on: str,
        how: str,
        output_path: Optional[Path] = None,
    ) -> pd.DataFrame:
        left = pd.read_csv(left_path)
        right = pd.read_csv(right_path)
        merged = left.merge(right, on=on, how=how)
        if output_path is not None:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            merged.to_csv(output_path, index=False)
        return merged


