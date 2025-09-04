from pathlib import Path
import numpy as np

from percell.infrastructure.bootstrap.container import get_container, AppConfig
from percell.domain.value_objects.processing import SegmentationParameters


def test_segment_cells_integration_with_dummy_segmenter(tmp_path: Path):
    # Arrange: create input images
    in_dir = tmp_path / "in"
    out_dir = tmp_path / "out"
    in_dir.mkdir(parents=True, exist_ok=True)

    img = np.ones((8, 8), dtype=np.uint8)

    container = get_container()
    image = container.image_adapter()

    image.write(in_dir / "a.tif", img)
    image.write(in_dir / "b.tif", img)

    # Act: use default DummySegmenter from container
    use_case = container.segment_cells_use_case()
    params = SegmentationParameters(model="dummy", diameter=30.0, flow_threshold=0.0, cellprob_threshold=0.0)
    result = use_case.execute(in_dir, out_dir, params)

    # Assert
    assert result.processed_count == 2
    for p in result.output_paths:
        assert p.is_file()


