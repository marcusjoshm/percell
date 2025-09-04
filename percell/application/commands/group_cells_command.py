from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from percell.application.use_cases.group_cells import GroupCellsUseCase
from percell.domain.value_objects.processing import BinningParameters


@dataclass(frozen=True)
class GroupCellsCommand:
    """Command encapsulating parameters to group cells in a directory."""

    cell_dir: Path
    output_dir: Path
    parameters: BinningParameters

    def execute(self, use_case: GroupCellsUseCase):
        return use_case.execute(self.cell_dir, self.output_dir, self.parameters)


