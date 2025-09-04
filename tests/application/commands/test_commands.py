from pathlib import Path
from unittest.mock import Mock

from percell.application.commands.group_cells_command import GroupCellsCommand
from percell.application.commands.track_rois_command import TrackROIsCommand
from percell.application.commands.segment_cells_command import SegmentCellsCommand
from percell.domain.value_objects.processing import BinningParameters, SegmentationParameters


def test_group_cells_command_executes_use_case(tmp_path: Path):
    cmd = GroupCellsCommand(
        cell_dir=tmp_path / 'cells',
        output_dir=tmp_path / 'out',
        parameters=BinningParameters(num_bins=3, strategy='uniform'),
    )
    use_case = Mock()
    cmd.execute(use_case)
    use_case.execute.assert_called_once()


def test_track_rois_command_executes_use_case(tmp_path: Path):
    cmd = TrackROIsCommand(
        zip_t0=tmp_path / 't0.zip',
        zip_t1=tmp_path / 't1.zip',
        output_zip=tmp_path / 'out.zip',
        max_distance=50.0,
    )
    use_case = Mock()
    cmd.execute(use_case)
    use_case.execute.assert_called_once()


def test_segment_cells_command_executes_use_case(tmp_path: Path):
    cmd = SegmentCellsCommand(
        input_dir=tmp_path / 'in',
        output_dir=tmp_path / 'out',
        parameters=SegmentationParameters('cellpose', 30.0, 0.5, 0.0),
    )
    use_case = Mock()
    cmd.execute(use_case)
    use_case.execute.assert_called_once()
