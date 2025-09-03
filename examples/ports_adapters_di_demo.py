#!/usr/bin/env python3
"""
End-to-end demo: Ports & Adapters via DI Container

Flow:
 - Build Container with config paths
 - Find a sample .tif
 - Read image via Storage adapter
 - Segment via Cellpose adapter (fallback if needed)
 - Crop cell region via ImageProcessing adapter
 - Measure intensity
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Optional

import numpy as np

from percell.infrastructure.dependencies.container import Container, AppConfig
from percell.domain.entities.image import Image
from percell.domain.value_objects.file_path import FilePath


def find_first_tif(base: Path) -> Optional[Path]:
    candidates = list(base.rglob("*.tif")) + list(base.rglob("*.tiff"))
    return candidates[0] if candidates else None


def main() -> int:
    parser = argparse.ArgumentParser(description="Ports & Adapters DI demo")
    parser.add_argument("--input", required=True, help="Input directory to search for images")
    parser.add_argument("--imagej", required=False, help="Path to ImageJ executable (optional)")
    parser.add_argument("--cellpose", required=False, help="Path to Cellpose python (optional)")
    args = parser.parse_args()

    input_dir = Path(args.input)
    if not input_dir.exists():
        print(f"ERROR: Input directory does not exist: {input_dir}")
        return 2

    # Build container
    container = Container(
        AppConfig(
            storage_base_path=str(input_dir),
            cellpose_path=args.cellpose,
            imagej_path=args.imagej,
        )
    )

    # Probe adapters
    print(f"ImageJ available: {container.imagej_adapter.is_available()}")
    print(f"Cellpose available: {container.cellpose_adapter.is_available()}")

    # Find an image
    img_path = find_first_tif(input_dir)
    if img_path is None:
        print("No .tif images found in input.")
        return 1
    print(f"Using image: {img_path}")

    # Read image via storage
    storage = container.storage_adapter
    np_img = storage.read_image(FilePath(img_path))
    demo_image = Image(image_id=img_path.stem, data=np_img, file_path=img_path)
    print(f"Image stats: {demo_image.get_statistics()}")

    # Segment via Cellpose adapter
    seg_params = {"model": "cyto", "diameter": 0, "flow_threshold": 0.4}
    rois = container.cellpose_adapter.segment_cells(demo_image, seg_params)
    print(f"ROIs returned: {len(rois)}")
    if not rois:
        print("No ROIs; exiting.")
        return 0

    # Post-process: crop first ROI and measure intensity
    ip = container.imagej_adapter
    roi = rois[0]
    # If bbox not set, estimate quickly from coordinates
    if roi.bounding_box is None and roi.coordinates:
        roi.calculate_bounding_box()
    if roi.bounding_box is None:
        print("ROI lacks bounding box; cannot crop.")
        return 0
    # If coordinates missing, synthesize rectangle from bbox for measurements
    if not roi.coordinates and roi.bounding_box is not None:
        x, y, w, h = roi.bounding_box
        roi.coordinates = [
            (x, y), (x + max(0, w - 1), y),
            (x + max(0, w - 1), y + max(0, h - 1)), (x, y + max(0, h - 1))
        ]

    cropped = ip.extract_cell_region(demo_image, roi, padding=2)
    stats = ip.measure_roi_intensity(demo_image, roi)
    print(f"Cropped image shape: {None if cropped.data is None else cropped.data.shape}")
    print(f"ROI intensity stats: {stats}")

    # Threshold preview
    thr = ip.threshold_image(demo_image, method="otsu")
    print(f"Thresholded image shape: {None if thr.data is None else thr.data.shape}")

    print("DEMO OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


