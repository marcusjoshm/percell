from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Optional, Tuple
import os

import numpy as np
import tifffile

from percell.ports.outbound.image_port import ImageReaderPort, ImageWriterPort


class TifffileImageAdapter(ImageReaderPort, ImageWriterPort):
    """Tifffile-based implementation of image reader/writer ports."""

    def read(self, path: Path) -> np.ndarray:
        return tifffile.imread(str(path))

    def read_with_metadata(self, path: Path) -> Tuple[np.ndarray, Dict[str, Any]]:
        with tifffile.TiffFile(str(path)) as tif:
            image = tif.asarray()
            metadata: Dict[str, Any] = {
                "imagej_metadata": tif.imagej_metadata,
                "num_pages": len(tif.pages),
            }
            # Attempt to read common resolution tags if present
            try:
                page0 = tif.pages[0]
                xres = page0.tags.get("XResolution")
                yres = page0.tags.get("YResolution")
                if xres is not None and yres is not None:
                    # values can be (num, den)
                    def _to_float(v):
                        try:
                            n, d = v.value
                            return float(n) / float(d) if d else float(n)
                        except Exception:
                            return None

                    metadata["resolution"] = {
                        "x": _to_float(xres),
                        "y": _to_float(yres),
                    }
            except Exception:
                # Keep metadata best-effort; do not raise
                pass
        return image, metadata

    def write(self, path: Path, image: np.ndarray, metadata: Optional[Dict[str, Any]] = None) -> None:
        # Optional performance tuning via env vars
        # PERCELL_TIFF_COMPRESSION: e.g., 'zlib', 'lzw', 'zstd', 'none'
        # PERCELL_TIFF_BIGTIFF: '1' to force BigTIFF
        # PERCELL_TIFF_PREDICTOR: 'horizontal' for better compression on images with gradients
        compression = os.environ.get("PERCELL_TIFF_COMPRESSION", None)
        if compression == "none":
            compression = None
        bigtiff_flag = os.environ.get("PERCELL_TIFF_BIGTIFF", "0") == "1"
        predictor = os.environ.get("PERCELL_TIFF_PREDICTOR", None)

        kwargs: Dict[str, Any] = {}
        if compression is not None:
            kwargs["compression"] = compression
        if bigtiff_flag:
            kwargs["bigtiff"] = True
        if predictor in {"horizontal", "float"}:
            kwargs["predictor"] = predictor

        if metadata is not None:
            kwargs["metadata"] = metadata

        tifffile.imwrite(str(path), image, **kwargs)


