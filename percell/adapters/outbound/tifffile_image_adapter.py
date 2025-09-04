from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Optional, Tuple

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
        if metadata is not None:
            tifffile.imwrite(str(path), image, metadata=metadata)
        else:
            tifffile.imwrite(str(path), image)


