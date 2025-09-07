from pathlib import Path
import numpy as np

from percell.adapters.pil_image_processing_adapter import PILImageProcessingAdapter


def test_read_write_bin_resize(tmp_path: Path):
    img = (np.arange(0, 100, dtype=np.uint8).reshape(10, 10))
    adapter = PILImageProcessingAdapter()

    p = tmp_path / "a.tif"
    adapter.write_image(p, img)
    arr = adapter.read_image(p)
    assert arr.shape == img.shape

    binned = adapter.bin_image(img, 2)
    assert binned.shape == (5, 5)

    resized = adapter.resize(img, (20, 20))
    assert resized.shape == (20, 20)


