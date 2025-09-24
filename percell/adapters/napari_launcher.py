#!/usr/bin/env python3
"""Custom Napari launcher script that preprocesses masks to convert zeros to NaN."""

import argparse
from pathlib import Path
import numpy as np
import napari
from skimage import io


def load_image_with_nan_zeros(file_path: Path) -> np.ndarray:
    """Load an image and convert zero values to NaN.

    Args:
        file_path: Path to the image file

    Returns:
        Image array with zeros converted to NaN
    """
    img = io.imread(file_path)
    # Convert to float to support NaN values
    img_float = img.astype(np.float64)
    # Convert zeros to NaN
    img_float[img_float == 0] = np.nan
    return img_float


def main():
    """Main function to launch Napari with preprocessed masks."""
    parser = argparse.ArgumentParser(description="Launch Napari with mask preprocessing")
    parser.add_argument("--images", nargs="*", help="Image file paths")
    parser.add_argument("--masks", nargs="*", help="Mask file paths")
    parser.add_argument("--working-dir", type=str, help="Working directory")

    args = parser.parse_args()

    # Create napari viewer
    viewer = napari.Viewer()

    # Load regular images
    if args.images:
        for img_path in args.images:
            img_file = Path(img_path)
            if img_file.exists():
                img = io.imread(img_file)
                viewer.add_image(
                    img,
                    name=img_file.name,
                    colormap='viridis'
                )

    # Load masks with zero-to-NaN conversion
    if args.masks:
        for mask_path in args.masks:
            mask_file = Path(mask_path)
            if mask_file.exists():
                mask = load_image_with_nan_zeros(mask_file)
                viewer.add_image(
                    mask,
                    name=f"mask_{mask_file.name}",
                    opacity=1.0,
                    blending='additive',
                    colormap='gray'
                )

    # Change working directory if specified
    if args.working_dir:
        import os
        os.chdir(args.working_dir)

    # Reset view to fit all loaded layers to screen
    viewer.reset_view()

    # Start the napari event loop
    napari.run()


if __name__ == "__main__":
    main()
