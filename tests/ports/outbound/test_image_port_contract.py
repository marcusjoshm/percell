import numpy as np
import pytest
from pathlib import Path
from percell.ports.outbound.image_port import ImageReaderPort, ImageWriterPort


class FakeImageAdapter(ImageReaderPort, ImageWriterPort):
    def read(self, path: Path) -> np.ndarray:
        return np.zeros((2, 2), dtype=np.uint16)

    def read_with_metadata(self, path: Path):
        return np.zeros((2, 2), dtype=np.uint16), {"dummy": True}

    def write(self, path: Path, image: np.ndarray, metadata=None) -> None:
        # pretend to write by checking types
        assert isinstance(path, Path)
        assert isinstance(image, np.ndarray)


def test_fake_image_adapter_contract(tmp_path: Path):
    adapter = FakeImageAdapter()
    img = adapter.read(tmp_path / 'x.tif')
    assert isinstance(img, np.ndarray)
    img2, meta = adapter.read_with_metadata(tmp_path / 'y.tif')
    assert isinstance(img2, np.ndarray)
    assert isinstance(meta, dict)
    adapter.write(tmp_path / 'z.tif', img2, {"a": 1})
