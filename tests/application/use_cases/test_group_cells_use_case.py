from pathlib import Path
from unittest.mock import Mock
import numpy as np
import pandas as pd

from percell.application.use_cases.group_cells import GroupCellsUseCase
from percell.domain.services.cell_grouping_service import CellGroupingService, GroupingParameters
from percell.domain.value_objects.processing import BinningParameters


def test_group_cells_use_case_with_mocks(tmp_path: Path):
    # Arrange mocks
    grouping_service = CellGroupingService()
    image_reader = Mock()
    image_writer = Mock()
    metadata_store = Mock()
    filesystem = Mock()

    # Create fake cell files
    cell_files = [tmp_path / f'cell_{i}.tif' for i in range(4)]
    filesystem.glob.return_value = cell_files
    filesystem.ensure_dir.return_value = None

    # Each read returns a 2x2 ones image
    image_reader.read.return_value = np.ones((2, 2))

    params = BinningParameters(num_bins=2, strategy='uniform')

    use_case = GroupCellsUseCase(
        grouping_service, image_reader, image_writer, metadata_store, filesystem
    )

    # Act
    result = use_case.execute(tmp_path, tmp_path / 'out', params)

    # Assert
    assert result.num_input_cells == 4
    assert result.output_dir == tmp_path / 'out'
    image_reader.read.assert_called()  # called for each file
    image_writer.write.assert_called()
    metadata_store.write_csv.assert_called()


def test_group_cells_use_case_grouping_logic(tmp_path: Path):
    # This test uses the real grouping service; intensities are identical to test code path
    grouping_service = CellGroupingService()
    image_reader = Mock()
    image_writer = Mock()
    metadata_store = Mock()
    filesystem = Mock()

    cell_files = [tmp_path / 'a.tif', tmp_path / 'b.tif']
    filesystem.glob.return_value = cell_files
    filesystem.ensure_dir.return_value = None

    image_reader.read.side_effect = [np.ones((2, 2)), np.ones((2, 2)) * 2]

    params = BinningParameters(num_bins=2, strategy='uniform')

    use_case = GroupCellsUseCase(
        grouping_service, image_reader, image_writer, metadata_store, filesystem
    )

    result = use_case.execute(tmp_path, tmp_path / 'out', params)
    assert result.num_groups >= 1
