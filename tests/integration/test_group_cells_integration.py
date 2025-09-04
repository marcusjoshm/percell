from pathlib import Path
import numpy as np

from percell.infrastructure.bootstrap.container import get_container
from percell.domain.value_objects.processing import BinningParameters


def test_group_cells_integration_with_real_adapters(tmp_path: Path):
    # Arrange: create fake cell images
    in_dir = tmp_path / "cells"
    out_dir = tmp_path / "out"
    in_dir.mkdir(parents=True, exist_ok=True)
    # Two simple 4x4 images with different intensities
    img_a = np.ones((4, 4), dtype=np.uint16)
    img_b = np.full((4, 4), 2, dtype=np.uint16)

    container = get_container()
    image = container.image_adapter()

    image.write(in_dir / "cell_a.tif", img_a)
    image.write(in_dir / "cell_b.tif", img_b)

    # Act
    use_case = container.group_cells_use_case()
    params = BinningParameters(num_bins=2, strategy="uniform")
    result = use_case.execute(in_dir, out_dir, params)

    # Assert
    # Output images per group should exist
    group_files = sorted(out_dir.glob("group_*.tif"))
    assert len(group_files) == result.num_groups >= 1
    # Metadata CSV should exist
    assert (out_dir / "grouping_metadata.csv").is_file()
    # The reported counts align
    assert result.num_input_cells == 2


