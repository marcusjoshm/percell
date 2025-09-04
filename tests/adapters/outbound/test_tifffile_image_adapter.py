import numpy as np
from pathlib import Path
from percell.adapters.outbound.tifffile_image_adapter import TifffileImageAdapter


def test_write_and_read_roundtrip(tmp_path: Path):
    adapter = TifffileImageAdapter()
    img = (np.arange(16, dtype=np.uint16).reshape(4, 4))
    out_path = tmp_path / 'test.tif'

    adapter.write(out_path, img, metadata={"description": "roundtrip"})
    read_img = adapter.read(out_path)
    assert read_img.dtype == img.dtype
    assert read_img.shape == img.shape
    assert np.array_equal(read_img, img)


def test_read_with_metadata(tmp_path: Path):
    adapter = TifffileImageAdapter()
    img = np.zeros((8, 8), dtype=np.uint8)
    out_path = tmp_path / 'meta.tif'

    adapter.write(out_path, img, metadata={"axes": "YX"})
    data, meta = adapter.read_with_metadata(out_path)
    assert data.shape == img.shape
    assert isinstance(meta, dict)
    assert "num_pages" in meta
