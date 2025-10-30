#!/usr/bin/env python3
"""
Headless Cellpose Segmentation with Optional SAM Integration

This script performs automated cell segmentation using Cellpose in headless mode
and generates ImageJ-formatted ROI lists. Optionally integrates with Segment
Anything Model (SAM) for improved segmentation.

Usage:
    python headless_cellpose_segmentation.py \
        --input_dir /path/to/images \
        --output_dir /path/to/output \
        --model_type cyto2 \
        --diameter 30 \
        --channels 0 0 \
        [--use_sam] \
        [--flow_threshold 0.4] \
        [--cellprob_threshold 0.0]
"""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path
from typing import List, Optional, Tuple
import numpy as np
from numpy.typing import NDArray

try:
    from cellpose import models
    CELLPOSE_AVAILABLE = True
except ImportError:
    CELLPOSE_AVAILABLE = False
    print("Warning: cellpose not available. Install with: pip install cellpose")

try:
    from roifile import ImagejRoi, roiwrite
    ROIFILE_AVAILABLE = True
except ImportError:
    ROIFILE_AVAILABLE = False
    print("Warning: roifile not available. Install with: pip install roifile")

try:
    from skimage import measure
    SKIMAGE_AVAILABLE = True
except ImportError:
    SKIMAGE_AVAILABLE = False
    print("Warning: scikit-image not available. Install with: pip install scikit-image")

try:
    from tifffile import imread, imwrite
    TIFFFILE_AVAILABLE = True
except ImportError:
    TIFFFILE_AVAILABLE = False
    print("Warning: tifffile not available. Install with: pip install tifffile")


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def check_dependencies() -> bool:
    """Check if all required dependencies are available."""
    missing = []
    if not CELLPOSE_AVAILABLE:
        missing.append("cellpose")
    if not ROIFILE_AVAILABLE:
        missing.append("roifile")
    if not SKIMAGE_AVAILABLE:
        missing.append("scikit-image")
    if not TIFFFILE_AVAILABLE:
        missing.append("tifffile")

    if missing:
        logger.error(f"Missing required dependencies: {', '.join(missing)}")
        logger.error("Install with: pip install " + " ".join(missing))
        return False
    return True


def run_cellpose_segmentation(
    image: NDArray,
    model_type: str = "cyto2",
    diameter: float = 30.0,
    channels: List[int] = [0, 0],
    flow_threshold: float = 0.4,
    cellprob_threshold: float = 0.0,
    gpu: bool = False,
) -> Tuple[NDArray, NDArray, NDArray]:
    """
    Run Cellpose segmentation on an image.

    Args:
        image: Input image as numpy array
        model_type: Cellpose model type (cyto, cyto2, nuclei, cpsam, etc.)
        diameter: Expected cell diameter in pixels
        channels: Channel configuration [cytoplasm, nucleus]
        flow_threshold: Flow error threshold (default 0.4)
        cellprob_threshold: Cell probability threshold (default 0.0)
        gpu: Use GPU acceleration if available

    Returns:
        Tuple of (masks, flows, styles) from Cellpose
    """
    logger.info(f"Initializing Cellpose model: {model_type}")

    # Check if using CP-SAM model
    is_cpsam = model_type.lower() in ['cpsam', 'cp-sam', 'sam']

    if is_cpsam:
        logger.info("Using Cellpose-SAM (CP-SAM) model")
        # CP-SAM uses a different model class
        try:
            from cellpose.models import CellposeModel
            # For CP-SAM, we use the pretrained_model parameter
            model = CellposeModel(gpu=gpu, pretrained_model=model_type)
        except Exception as e:
            logger.warning(f"Could not load CP-SAM directly: {e}")
            logger.info("Falling back to standard Cellpose with SAM model")
            model = models.Cellpose(gpu=gpu, model_type=model_type)
    else:
        # Standard Cellpose models
        model = models.Cellpose(gpu=gpu, model_type=model_type)

    # For CP-SAM, diameter is optional (SAM auto-detects scale)
    # Use diameter=None to let SAM handle it automatically
    if is_cpsam and diameter == 0:
        logger.info("Running CP-SAM with automatic scale detection")
        eval_diameter = None
    elif diameter == 0:
        logger.info("Running with automatic diameter estimation")
        eval_diameter = None
    else:
        logger.info(f"Running segmentation with diameter={diameter}")
        eval_diameter = diameter

    # CP-SAM returns different number of values than standard Cellpose
    result = model.eval(
        image,
        diameter=eval_diameter,
        channels=channels,
        flow_threshold=flow_threshold,
        cellprob_threshold=cellprob_threshold,
    )

    # Handle different return formats
    if len(result) == 4:
        # Standard Cellpose: (masks, flows, styles, diams)
        masks, flows, styles, diams = result
    elif len(result) == 3:
        # CP-SAM may return: (masks, flows, styles)
        masks, flows, styles = result
        diams = 0
    else:
        # Fallback - just get masks
        masks = result[0] if isinstance(result, tuple) else result
        flows = None
        styles = None
        diams = 0

    num_cells = masks.max()
    logger.info(f"Segmentation complete. Found {num_cells} cells")

    return masks, flows, styles


def mask_to_imagej_rois(
    mask: NDArray,
    min_area: int = 10,
) -> List[Tuple[NDArray, int]]:
    """
    Convert a labeled mask to ImageJ ROI format.

    Args:
        mask: Labeled mask where each cell has a unique integer ID
        min_area: Minimum area (in pixels) to keep an ROI

    Returns:
        List of (polygon_coordinates, label) tuples
    """
    logger.info("Converting masks to ROI contours...")

    rois = []
    num_labels = mask.max()

    for label_id in range(1, num_labels + 1):
        # Create binary mask for this cell
        binary_mask = (mask == label_id).astype(np.uint8)

        # Find contours
        contours = measure.find_contours(binary_mask, 0.5)

        if not contours:
            continue

        # Take the longest contour (outer boundary)
        contour = max(contours, key=len)

        # Check area
        area = np.sum(binary_mask)
        if area < min_area:
            logger.debug(f"Skipping ROI {label_id} (area={area} < {min_area})")
            continue

        # Convert to ImageJ format (x, y) with origin at top-left
        # skimage.measure.find_contours returns (row, col) so we need to swap
        polygon = np.column_stack([contour[:, 1], contour[:, 0]])

        rois.append((polygon, label_id))

    logger.info(f"Created {len(rois)} ROI contours")
    return rois


def save_rois_as_imagej_zip(
    rois: List[Tuple[NDArray, int]],
    output_path: Path,
) -> None:
    """
    Save ROIs to an ImageJ-compatible ZIP file.

    Args:
        rois: List of (polygon_coordinates, label) tuples
        output_path: Path to save the ROI zip file
    """
    logger.info(f"Saving {len(rois)} ROIs to {output_path}")

    # Create ImageJ ROI objects
    imagej_rois = []
    for polygon, label_id in rois:
        # Convert polygon to integer coordinates
        coords = polygon.astype(np.int32)

        # Create ImageJ polygon ROI
        roi = ImagejRoi.frompoints(coords)
        roi.name = f"Cell_{label_id:04d}"
        imagej_rois.append(roi)

    # Write to zip file
    roiwrite(str(output_path), imagej_rois)
    logger.info(f"Successfully saved ROI zip: {output_path}")


def process_single_image(
    image_path: Path,
    output_dir: Path,
    model_type: str = "cyto2",
    diameter: float = 30.0,
    channels: List[int] = [0, 0],
    flow_threshold: float = 0.4,
    cellprob_threshold: float = 0.0,
    min_area: int = 10,
    gpu: bool = False,
    save_mask: bool = True,
) -> bool:
    """
    Process a single image: segment and create ROIs.

    Args:
        image_path: Path to input image
        output_dir: Directory to save outputs
        model_type: Cellpose model type
        diameter: Expected cell diameter
        channels: Channel configuration
        flow_threshold: Flow error threshold
        cellprob_threshold: Cell probability threshold
        min_area: Minimum ROI area in pixels
        gpu: Use GPU acceleration
        save_mask: Save the segmentation mask as TIFF

    Returns:
        True if successful, False otherwise
    """
    try:
        logger.info(f"Processing: {image_path.name}")

        # Load image
        logger.info("Loading image...")
        image = imread(str(image_path))
        logger.info(f"Image shape: {image.shape}, dtype: {image.dtype}")

        # Run Cellpose segmentation
        masks, flows, styles = run_cellpose_segmentation(
            image=image,
            model_type=model_type,
            diameter=diameter,
            channels=channels,
            flow_threshold=flow_threshold,
            cellprob_threshold=cellprob_threshold,
            gpu=gpu,
        )

        # Save mask if requested
        if save_mask:
            mask_filename = f"{image_path.stem}_mask.tif"
            mask_path = output_dir / mask_filename
            logger.info(f"Saving mask to: {mask_path}")
            imwrite(str(mask_path), masks.astype(np.uint16))

        # Convert masks to ROIs
        rois = mask_to_imagej_rois(masks, min_area=min_area)

        if not rois:
            logger.warning(f"No ROIs generated for {image_path.name}")
            return False

        # Save ROIs in ImageJ format
        roi_filename = f"{image_path.stem}_rois.zip"
        roi_path = output_dir / roi_filename
        save_rois_as_imagej_zip(rois, roi_path)

        logger.info(f"Successfully processed {image_path.name}")
        return True

    except Exception as e:
        logger.error(f"Error processing {image_path.name}: {e}", exc_info=True)
        return False


def process_directory(
    input_dir: Path,
    output_dir: Path,
    model_type: str = "cyto2",
    diameter: float = 30.0,
    channels: List[int] = [0, 0],
    flow_threshold: float = 0.4,
    cellprob_threshold: float = 0.0,
    min_area: int = 10,
    gpu: bool = False,
    save_masks: bool = True,
    file_pattern: str = "*.tif",
) -> Tuple[int, int]:
    """
    Process all images in a directory.

    Args:
        input_dir: Input directory containing images
        output_dir: Output directory for results
        model_type: Cellpose model type
        diameter: Expected cell diameter
        channels: Channel configuration
        flow_threshold: Flow error threshold
        cellprob_threshold: Cell probability threshold
        min_area: Minimum ROI area
        gpu: Use GPU acceleration
        save_masks: Save segmentation masks
        file_pattern: Glob pattern for finding images

    Returns:
        Tuple of (successful_count, total_count)
    """
    # Create output directory
    output_dir.mkdir(parents=True, exist_ok=True)

    # Find all images
    image_files = sorted(input_dir.glob(file_pattern))

    # Also try .tiff extension
    if file_pattern == "*.tif":
        image_files.extend(sorted(input_dir.glob("*.tiff")))

    if not image_files:
        logger.error(f"No images found in {input_dir} with pattern {file_pattern}")
        return 0, 0

    logger.info(f"Found {len(image_files)} images to process")

    # Process each image
    successful = 0
    for image_path in image_files:
        success = process_single_image(
            image_path=image_path,
            output_dir=output_dir,
            model_type=model_type,
            diameter=diameter,
            channels=channels,
            flow_threshold=flow_threshold,
            cellprob_threshold=cellprob_threshold,
            min_area=min_area,
            gpu=gpu,
            save_mask=save_masks,
        )
        if success:
            successful += 1

    logger.info(f"Processed {successful}/{len(image_files)} images successfully")
    return successful, len(image_files)


def main():
    """Main entry point for command-line usage."""
    parser = argparse.ArgumentParser(
        description="Headless Cellpose Segmentation with ImageJ ROI Output",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    # Basic usage with default settings
    python headless_cellpose_segmentation.py -i images/ -o output/

    # Custom model and diameter
    python headless_cellpose_segmentation.py -i images/ -o output/ \\
        --model_type nuclei --diameter 15

    # Use GPU acceleration
    python headless_cellpose_segmentation.py -i images/ -o output/ --gpu

    # Adjust thresholds for better segmentation
    python headless_cellpose_segmentation.py -i images/ -o output/ \\
        --flow_threshold 0.6 --cellprob_threshold 0.5
        """
    )

    # Required arguments
    parser.add_argument(
        "-i", "--input_dir",
        type=Path,
        required=True,
        help="Input directory containing images to segment"
    )
    parser.add_argument(
        "-o", "--output_dir",
        type=Path,
        required=True,
        help="Output directory for masks and ROIs"
    )

    # Cellpose parameters
    parser.add_argument(
        "--model_type",
        type=str,
        default="cyto2",
        choices=["cyto", "cyto2", "nuclei", "cyto3", "cpsam"],
        help="Cellpose model type (default: cyto2, use cpsam for SAM)"
    )
    parser.add_argument(
        "--diameter",
        type=float,
        default=30.0,
        help=(
            "Expected cell diameter in pixels (default: 30). "
            "Set to 0 for automatic detection (recommended for cpsam)"
        )
    )
    parser.add_argument(
        "--channels",
        type=int,
        nargs=2,
        default=[0, 0],
        help="Channel indices for [cytoplasm, nucleus]. Use 0 for grayscale (default: 0 0)"
    )
    parser.add_argument(
        "--flow_threshold",
        type=float,
        default=0.4,
        help="Flow error threshold, higher = fewer cells (default: 0.4)"
    )
    parser.add_argument(
        "--cellprob_threshold",
        type=float,
        default=0.0,
        help="Cell probability threshold, higher = fewer cells (default: 0.0)"
    )

    # ROI parameters
    parser.add_argument(
        "--min_area",
        type=int,
        default=10,
        help="Minimum ROI area in pixels (default: 10)"
    )

    # Processing options
    parser.add_argument(
        "--gpu",
        action="store_true",
        help="Use GPU acceleration if available"
    )
    parser.add_argument(
        "--no_save_masks",
        action="store_true",
        help="Don't save segmentation masks, only ROIs"
    )
    parser.add_argument(
        "--pattern",
        type=str,
        default="*.tif",
        help="File pattern for finding images (default: *.tif)"
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose debug logging"
    )

    args = parser.parse_args()

    # Set logging level
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # Check dependencies
    if not check_dependencies():
        sys.exit(1)

    # Validate inputs
    if not args.input_dir.exists():
        logger.error(f"Input directory does not exist: {args.input_dir}")
        sys.exit(1)

    if not args.input_dir.is_dir():
        logger.error(f"Input path is not a directory: {args.input_dir}")
        sys.exit(1)

    # Log configuration
    logger.info("=" * 60)
    logger.info("Headless Cellpose Segmentation")
    logger.info("=" * 60)
    logger.info(f"Input directory: {args.input_dir}")
    logger.info(f"Output directory: {args.output_dir}")
    logger.info(f"Model type: {args.model_type}")
    logger.info(f"Cell diameter: {args.diameter}")
    logger.info(f"Channels: {args.channels}")
    logger.info(f"Flow threshold: {args.flow_threshold}")
    logger.info(f"Cell prob threshold: {args.cellprob_threshold}")
    logger.info(f"Minimum ROI area: {args.min_area}")
    logger.info(f"GPU acceleration: {args.gpu}")
    logger.info(f"Save masks: {not args.no_save_masks}")
    logger.info("=" * 60)

    # Process images
    successful, total = process_directory(
        input_dir=args.input_dir,
        output_dir=args.output_dir,
        model_type=args.model_type,
        diameter=args.diameter,
        channels=args.channels,
        flow_threshold=args.flow_threshold,
        cellprob_threshold=args.cellprob_threshold,
        min_area=args.min_area,
        gpu=args.gpu,
        save_masks=not args.no_save_masks,
        file_pattern=args.pattern,
    )

    # Summary
    logger.info("=" * 60)
    logger.info(f"Processing complete: {successful}/{total} images successful")
    logger.info("=" * 60)

    if successful == 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
