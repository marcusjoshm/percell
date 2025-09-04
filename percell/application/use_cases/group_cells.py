from __future__ import annotations

from dataclasses import dataclass
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import List

import numpy as np

from percell.domain.services.cell_grouping_service import (
    CellGroupingService,
    GroupingParameters,
)
from percell.domain.value_objects.processing import BinningParameters
from percell.ports.outbound.image_port import ImageReaderPort, ImageWriterPort
from percell.ports.outbound.metadata_port import MetadataStorePort
from percell.ports.outbound.filesystem_port import FilesystemPort


@dataclass(frozen=True)
class GroupCellsResult:
    output_dir: Path
    num_input_cells: int
    num_groups: int


class GroupCellsUseCase:
    """Orchestrates grouping of cell images into bins and saving outputs."""

    def __init__(
        self,
        grouping_service: CellGroupingService,
        image_reader: ImageReaderPort,
        image_writer: ImageWriterPort,
        metadata_store: MetadataStorePort,
        filesystem: FilesystemPort,
    ) -> None:
        self.grouping_service = grouping_service
        self.image_reader = image_reader
        self.image_writer = image_writer
        self.metadata_store = metadata_store
        self.filesystem = filesystem

    def execute(
        self,
        cell_dir: Path,
        output_dir: Path,
        parameters: BinningParameters,
    ) -> GroupCellsResult:
        self.filesystem.ensure_dir(output_dir)

        # 1) Discover cell images
        cell_files: List[Path] = sorted(self.filesystem.glob("*.tif", root=cell_dir))
        # 2) Load cell images (optionally with I/O concurrency)
        # Default to sequential for determinism; enable concurrency via env var
        workers_env = os.environ.get("PERCELL_IO_WORKERS")
        if workers_env and workers_env.isdigit() and int(workers_env) > 1:
            max_workers = int(workers_env)
            cell_images: List[np.ndarray] = []
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                future_to_path = {executor.submit(self.image_reader.read, p): p for p in cell_files}
                for future in as_completed(future_to_path):
                    cell_images.append(future.result())
        else:
            cell_images = [self.image_reader.read(p) for p in cell_files]

        # 3) Compute intensities via domain service (flatten image to 1D profile)
        intensities: List[float] = [
            self.grouping_service.compute_auc(np.ravel(img)) for img in cell_images
        ]

        # 4) Group cells
        grouping_params = GroupingParameters(
            num_bins=parameters.num_bins, strategy=parameters.strategy
        )
        assignments = self.grouping_service.group_by_intensity(
            intensities, grouping_params
        )

        # 5) Aggregate by group and write outputs
        aggregated = self.grouping_service.aggregate_by_group(cell_images, assignments)
        for group_id, group_image in aggregated.items():
            out_path = output_dir / f"group_{int(group_id)}.tif"
            self.image_writer.write(out_path, group_image)

        # 6) Save metadata CSV
        import pandas as pd

        metadata_rows = [
            {"file": str(p), "intensity": float(i), "group": int(g)}
            for p, i, g in zip(cell_files, intensities, assignments)
        ]
        df = pd.DataFrame(metadata_rows)
        self.metadata_store.write_csv(output_dir / "grouping_metadata.csv", df, index=False)

        return GroupCellsResult(
            output_dir=output_dir,
            num_input_cells=len(cell_files),
            num_groups=len(aggregated),
        )


