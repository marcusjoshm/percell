from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import List

import numpy as np

from percell.ports.outbound.image_port import ImageReaderPort, ImageWriterPort
from percell.ports.outbound.segmenter_port import SegmenterPort
from percell.domain.value_objects.processing import SegmentationParameters
from percell.ports.outbound.filesystem_port import FilesystemPort


@dataclass(frozen=True)
class SegmentationResult:
    output_paths: List[Path]
    processed_count: int


class SegmentCellsUseCase:
    """Use case to execute cell segmentation over images in a directory."""

    def __init__(
        self,
        image_reader: ImageReaderPort,
        image_writer: ImageWriterPort,
        segmenter: SegmenterPort,
        filesystem: FilesystemPort,
    ) -> None:
        self.image_reader = image_reader
        self.image_writer = image_writer
        self.segmenter = segmenter
        self.filesystem = filesystem

    def execute(self, input_dir: Path, output_dir: Path, parameters: SegmentationParameters) -> SegmentationResult:
        self.filesystem.ensure_dir(output_dir)
        image_paths: List[Path] = sorted(self.filesystem.glob("*.tif", root=input_dir))
        outputs: List[Path] = []
        for ip in image_paths:
            img = self.image_reader.read(ip)
            mask = self.segmenter.segment(img, parameters)
            out = output_dir / f"{ip.stem}_masks.tif"
            self.image_writer.write(out, mask)
            outputs.append(out)
        return SegmentationResult(output_paths=outputs, processed_count=len(outputs))


