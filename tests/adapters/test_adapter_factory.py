from pathlib import Path
import pytest
from percell.adapters.factory import AdapterFactory, AdapterFactoryConfig
from percell.adapters.outbound.tifffile_image_adapter import TifffileImageAdapter
from percell.adapters.outbound.imagej_macro_adapter import ImageJMacroAdapter
from percell.adapters.outbound.pandas_metadata_adapter import PandasMetadataAdapter
from percell.adapters.outbound.pathlib_filesystem_adapter import PathlibFilesystemAdapter


def test_factory_builds_default_adapters(tmp_path: Path):
    cfg = AdapterFactoryConfig(
        imagej_path=tmp_path / 'ImageJ',
        macro_dir=tmp_path / 'macros',
    )
    cfg.macro_dir.mkdir()
    cfg.imagej_path.write_text('stub')

    factory = AdapterFactory(cfg)
    assert isinstance(factory.build_image_reader(), TifffileImageAdapter)
    assert isinstance(factory.build_image_writer(), TifffileImageAdapter)
    assert isinstance(factory.build_metadata_store(), PandasMetadataAdapter)
    assert isinstance(factory.build_filesystem(), PathlibFilesystemAdapter)


def test_factory_requires_imagej_paths(tmp_path: Path):
    cfg = AdapterFactoryConfig()
    factory = AdapterFactory(cfg)
    with pytest.raises(ValueError):
        factory.build_macro_runner()

    # Provide imagej path but missing macro_dir
    cfg2 = AdapterFactoryConfig(imagej_path=tmp_path / 'ImageJ')
    factory2 = AdapterFactory(cfg2)
    with pytest.raises(ValueError):
        factory2.build_macro_runner()

    # Provide both
    cfg3 = AdapterFactoryConfig(imagej_path=tmp_path / 'ImageJ', macro_dir=tmp_path)
    factory3 = AdapterFactory(cfg3)
    runner = factory3.build_macro_runner()
    assert isinstance(runner, ImageJMacroAdapter)
