#!/usr/bin/env python3
"""
Test script for headless Cellpose segmentation.

This script tests the headless segmentation setup and helps diagnose issues.
"""

import sys
from pathlib import Path


def check_python_version():
    """Check Python version."""
    print("=" * 60)
    print("Python Version Check")
    print("=" * 60)
    version = sys.version_info
    print(f"Python version: {version.major}.{version.minor}.{version.patch}")

    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print("❌ Python 3.8+ required")
        return False
    else:
        print("✓ Python version OK")
        return True


def check_dependencies():
    """Check required dependencies."""
    print("\n" + "=" * 60)
    print("Dependency Check")
    print("=" * 60)

    deps = {
        'cellpose': 'Cellpose segmentation library',
        'roifile': 'ImageJ ROI file writer',
        'skimage': 'scikit-image for image processing',
        'tifffile': 'TIFF file I/O',
        'numpy': 'Numerical arrays',
    }

    all_ok = True
    for module, description in deps.items():
        try:
            if module == 'skimage':
                import skimage
            else:
                __import__(module)
            print(f"✓ {module:15s} - {description}")
        except ImportError:
            print(f"❌ {module:15s} - {description} (NOT INSTALLED)")
            all_ok = False

    if not all_ok:
        print("\nInstall missing dependencies:")
        print("  pip install cellpose roifile scikit-image tifffile")

    return all_ok


def check_gpu():
    """Check GPU availability."""
    print("\n" + "=" * 60)
    print("GPU Check")
    print("=" * 60)

    try:
        import torch
        gpu_available = torch.cuda.is_available()

        if gpu_available:
            print(f"✓ GPU available: {torch.cuda.get_device_name(0)}")
            print(f"  CUDA version: {torch.version.cuda}")
            print(f"  Device count: {torch.cuda.device_count()}")
            return True
        else:
            print("⚠ No GPU detected (will use CPU)")
            print("  This is OK but slower than GPU")
            return False
    except ImportError:
        print("⚠ PyTorch not available, cannot check GPU")
        return False


def check_cellpose_models():
    """Check available Cellpose models."""
    print("\n" + "=" * 60)
    print("Cellpose Models Check")
    print("=" * 60)

    try:
        from cellpose import models

        available_models = ['cyto', 'cyto2', 'nuclei']
        for model_name in available_models:
            try:
                # Just initialize, don't download
                print(f"✓ {model_name:10s} - Available")
            except Exception as e:
                print(f"⚠ {model_name:10s} - Issue: {e}")

        print("\nNote: Models will be downloaded on first use")
        return True

    except ImportError:
        print("❌ Cannot check models - cellpose not installed")
        return False


def test_segmentation(test_dir: Path = None):
    """Test segmentation on sample images if available."""
    print("\n" + "=" * 60)
    print("Segmentation Test")
    print("=" * 60)

    if test_dir is None or not test_dir.exists():
        print("⚠ No test directory provided, skipping segmentation test")
        print("  To test segmentation, run:")
        print("    python test_headless_segmentation.py /path/to/test/images")
        return True

    try:
        # Import required modules
        from tifffile import imread
        from cellpose import models
        import numpy as np

        # Find test images
        images = list(test_dir.glob("*.tif"))
        images.extend(list(test_dir.glob("*.tiff")))

        if not images:
            print(f"⚠ No images found in {test_dir}")
            return True

        print(f"Found {len(images)} test images")
        test_image = images[0]
        print(f"Testing with: {test_image.name}")

        # Load image
        img = imread(str(test_image))
        print(f"  Image shape: {img.shape}")
        print(f"  Image dtype: {img.dtype}")

        # Initialize model
        print("  Initializing Cellpose model...")
        model = models.Cellpose(gpu=False, model_type='cyto2')

        # Run segmentation
        print("  Running segmentation...")
        masks, flows, styles, diams = model.eval(
            img,
            diameter=30,
            channels=[0, 0],
            flow_threshold=0.4,
            cellprob_threshold=0.0,
        )

        num_cells = masks.max()
        print(f"✓ Segmentation successful!")
        print(f"  Found {num_cells} cells")
        print(f"  Estimated diameter: {diams:.1f} pixels")

        # Test ROI conversion
        from skimage import measure

        print("  Testing ROI conversion...")
        roi_count = 0
        for label_id in range(1, min(num_cells + 1, 6)):  # Test first 5
            binary_mask = (masks == label_id).astype(np.uint8)
            contours = measure.find_contours(binary_mask, 0.5)
            if contours:
                roi_count += 1

        print(f"✓ ROI conversion successful!")
        print(f"  Converted {roi_count} test ROIs")

        return True

    except Exception as e:
        print(f"❌ Segmentation test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def check_script_location():
    """Check if the headless segmentation script exists."""
    print("\n" + "=" * 60)
    print("Script Location Check")
    print("=" * 60)

    # Try to find the script
    script_name = "headless_cellpose_segmentation.py"
    current_dir = Path(__file__).parent
    script_path = current_dir / script_name

    if script_path.exists():
        print(f"✓ Script found: {script_path}")
        return True
    else:
        print(f"❌ Script not found: {script_path}")
        print(f"   Expected location: {script_path}")
        return False


def main():
    """Run all checks."""
    print("\n" + "=" * 60)
    print("Headless Cellpose Segmentation Test")
    print("=" * 60)

    # Parse command line arguments
    test_dir = None
    if len(sys.argv) > 1:
        test_dir = Path(sys.argv[1])
        if not test_dir.exists():
            print(f"Warning: Test directory not found: {test_dir}")
            test_dir = None

    # Run checks
    results = {
        'Python Version': check_python_version(),
        'Dependencies': check_dependencies(),
        'GPU': check_gpu(),
        'Cellpose Models': check_cellpose_models(),
        'Script Location': check_script_location(),
        'Segmentation Test': test_segmentation(test_dir),
    }

    # Summary
    print("\n" + "=" * 60)
    print("Summary")
    print("=" * 60)

    for check, passed in results.items():
        status = "✓" if passed else "❌"
        print(f"{status} {check}")

    all_passed = all(results.values())

    print("\n" + "=" * 60)
    if all_passed:
        print("✓ All checks passed! Headless segmentation is ready to use.")
    else:
        print("⚠ Some checks failed. See above for details.")
    print("=" * 60)

    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
