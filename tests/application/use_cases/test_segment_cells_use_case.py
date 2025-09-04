from pathlib import Path
from unittest.mock import Mock
import numpy as np

from percell.application.use_cases.segment_cells import SegmentCellsUseCase
from percell.domain.value_objects.processing import SegmentationParameters


def test_segment_cells_use_case_with_mocks(tmp_path: Path):
    image_reader = Mock()
    image_writer = Mock()
    segmenter = Mock()
    filesystem = Mock()

    # Pretend there are two input images
    in_dir = tmp_path / 'in'
    out_dir = tmp_path / 'out'
    filesystem.glob.return_value = [in_dir / 'a.tif', in_dir / 'b.tif']
    filesystem.ensure_dir.return_value = None

    image_reader.read.return_value = np.zeros((4, 4), dtype=np.uint8)
    segmenter.segment.return_value = np.ones((4, 4), dtype=np.uint8)

    params = SegmentationParameters(model='cellpose', diameter=30.0, flow_threshold=0.5, cellprob_threshold=0.0)

    use_case = SegmentCellsUseCase(image_reader, image_writer, segmenter, filesystem)
    result = use_case.execute(in_dir, out_dir, params)

    assert result.processed_count == 2
    assert len(result.output_paths) == 2
    assert image_writer.write.called
