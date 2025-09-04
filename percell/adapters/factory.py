from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from percell.adapters.outbound.tifffile_image_adapter import TifffileImageAdapter
from percell.adapters.outbound.imagej_macro_adapter import ImageJMacroAdapter
from percell.adapters.outbound.pandas_metadata_adapter import PandasMetadataAdapter
from percell.adapters.outbound.pathlib_filesystem_adapter import PathlibFilesystemAdapter
from percell.ports.outbound.image_port import ImageReaderPort, ImageWriterPort
from percell.ports.outbound.macro_runner_port import MacroRunnerPort
from percell.ports.outbound.metadata_port import MetadataStorePort
from percell.ports.outbound.filesystem_port import FilesystemPort


ImageAdapterKind = Literal["tifffile"]
MacroRunnerKind = Literal["imagej"]
MetadataStoreKind = Literal["pandas"]
FilesystemKind = Literal["pathlib"]


@dataclass(frozen=True)
class AdapterFactoryConfig:
    image_adapter: ImageAdapterKind = "tifffile"
    macro_runner: MacroRunnerKind = "imagej"
    metadata_store: MetadataStoreKind = "pandas"
    filesystem: FilesystemKind = "pathlib"

    # Required when macro_runner == "imagej"
    imagej_path: Path | None = None
    macro_dir: Path | None = None


class AdapterFactory:
    """Factory that builds adapter implementations based on configuration."""

    def __init__(self, config: AdapterFactoryConfig):
        self.config = config

    def build_image_reader(self) -> ImageReaderPort:
        if self.config.image_adapter == "tifffile":
            return TifffileImageAdapter()
        raise ValueError(f"Unsupported image adapter: {self.config.image_adapter}")

    def build_image_writer(self) -> ImageWriterPort:
        if self.config.image_adapter == "tifffile":
            return TifffileImageAdapter()
        raise ValueError(f"Unsupported image adapter: {self.config.image_adapter}")

    def build_macro_runner(self) -> MacroRunnerPort:
        if self.config.macro_runner == "imagej":
            if self.config.imagej_path is None or self.config.macro_dir is None:
                raise ValueError("imagej_path and macro_dir are required for ImageJMacroAdapter")
            return ImageJMacroAdapter(self.config.imagej_path, self.config.macro_dir)
        raise ValueError(f"Unsupported macro runner: {self.config.macro_runner}")

    def build_metadata_store(self) -> MetadataStorePort:
        if self.config.metadata_store == "pandas":
            return PandasMetadataAdapter()
        raise ValueError(f"Unsupported metadata store: {self.config.metadata_store}")

    def build_filesystem(self) -> FilesystemPort:
        if self.config.filesystem == "pathlib":
            return PathlibFilesystemAdapter()
        raise ValueError(f"Unsupported filesystem: {self.config.filesystem}")


