# CP-SAM (Cellpose-SAM) Setup Guide

## What is CP-SAM?

CP-SAM combines Cellpose with the Segment Anything Model (SAM) from Meta AI, providing superior segmentation quality, especially for:
- Complex cell morphologies
- Cells with irregular shapes
- Crowded or overlapping cells
- Variable cell sizes in the same image

## Your Current Configuration

Your config is already set up for CP-SAM at `percell/config/config.json`:

```json
"segmentation": {
  "headless": false,        // Set to true to enable automated mode
  "model_type": "cpsam",   // ✓ CP-SAM model
  "diameter": 0,            // ✓ Auto-detection (recommended for SAM)
  "flow_threshold": 0.4,
  "cellprob_threshold": 0.0,
  "min_area": 10,
  "use_gpu": false         // Set to true if you have GPU
}
```

## Installation

CP-SAM requires additional dependencies. Install them in your cellpose environment:

```bash
# 1. Activate cellpose environment
source cellpose_venv/bin/activate

# 2. Install CP-SAM and dependencies
pip install cellpose[sam]
# OR if the above doesn't work:
pip install cellpose segment-anything

# 3. Install other required packages
pip install roifile scikit-image tifffile

# 4. Verify installation
python -c "from cellpose.models import CellposeModel; print('CP-SAM ready!')"
```

## Key Differences from Standard Cellpose

| Feature | Standard Cellpose | CP-SAM |
|---------|-------------------|---------|
| **Diameter** | Required (must specify) | **Optional** (auto-detects) |
| **Accuracy** | Good for uniform cells | **Excellent** for varied shapes |
| **Speed** | Fast | Slower (more compute) |
| **GPU Benefit** | Moderate (2-5x faster) | **High** (10-50x faster) |
| **Memory** | Low (~2GB) | **Higher** (~8-16GB) |

## Recommended Settings for CP-SAM

### Auto-Detection (Recommended)
```json
"segmentation": {
  "headless": true,
  "model_type": "cpsam",
  "diameter": 0,              // Let SAM auto-detect
  "flow_threshold": 0.4,
  "cellprob_threshold": 0.0,
  "min_area": 10,
  "use_gpu": true            // Highly recommended for SAM
}
```

### With Manual Diameter
If you still want to provide a diameter hint:
```json
"segmentation": {
  "headless": true,
  "model_type": "cpsam",
  "diameter": 30,            // Optional hint
  "flow_threshold": 0.4,
  "cellprob_threshold": 0.0,
  "min_area": 10,
  "use_gpu": true
}
```

## GPU Acceleration for CP-SAM

**CP-SAM strongly benefits from GPU!** Without GPU, it can be 20-50x slower.

### Check GPU Availability
```bash
source cellpose_venv/bin/activate
python -c "import torch; print('GPU available:', torch.cuda.is_available())"
```

### Install CUDA Support
If GPU is not available but you have an NVIDIA GPU:

```bash
# For CUDA 11.8
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu118

# For CUDA 12.1
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu121
```

Then enable GPU in config:
```json
"use_gpu": true
```

## Running with CP-SAM

### Method 1: Full Workflow (Headless)

1. **Enable headless mode** in `percell/config/config.json`:
   ```json
   "segmentation": {
     "headless": true,
     "model_type": "cpsam",
     "diameter": 0,
     "use_gpu": true
   }
   ```

2. **Run the workflow**:
   ```bash
   source venv/bin/activate
   python -m percell.main
   ```

### Method 2: Standalone Script

```bash
source cellpose_venv/bin/activate

python percell/scripts/headless_cellpose_segmentation.py \
    --input_dir /path/to/images \
    --output_dir /path/to/output \
    --model_type cpsam \
    --diameter 0 \
    --gpu
```

## Expected Performance

### Processing Time Examples (per 1024×1024 image)

**Without GPU:**
- Standard Cellpose: ~30 seconds
- **CP-SAM: ~5-10 minutes** ⚠️ Much slower!

**With GPU (RTX 3080):**
- Standard Cellpose: ~3 seconds
- **CP-SAM: ~10-15 seconds** ✅ Acceptable

**Recommendation:** Use GPU for CP-SAM, or expect significantly longer processing times.

## Troubleshooting

### Issue: "segment_anything not found"

```bash
pip install segment-anything
# OR
pip install 'git+https://github.com/facebookresearch/segment-anything.git'
```

### Issue: CP-SAM model not downloading

On first use, CP-SAM downloads model weights (~2.4GB). Ensure:
- Internet connection is active
- Enough disk space (~5GB free)
- No firewall blocking download

Check download location:
```python
from cellpose import models
print(models.MODEL_DIR)  # Usually ~/.cellpose/models/
```

### Issue: Out of memory

CP-SAM requires more memory. Solutions:
1. **Enable GPU** (uses GPU memory instead)
2. **Process smaller batches**
3. **Reduce image size** (bin images more)
4. **Increase system RAM** (16GB+ recommended)

### Issue: Very slow without GPU

This is expected. Options:
1. **Install GPU support** (recommended)
2. **Use standard Cellpose** instead:
   ```json
   "model_type": "cyto2",
   "diameter": 30
   ```
3. **Process fewer images** at a time

## When to Use CP-SAM vs Standard Cellpose

### Use CP-SAM when:
- ✅ Cells have complex/irregular shapes
- ✅ Cell sizes vary significantly
- ✅ Cells are overlapping or crowded
- ✅ You have GPU available
- ✅ Quality > speed is priority

### Use Standard Cellpose when:
- ✅ Cells are relatively uniform
- ✅ Speed is critical
- ✅ No GPU available
- ✅ Working with large datasets
- ✅ Memory is limited

## Verification

Test your CP-SAM setup:

```bash
source cellpose_venv/bin/activate
python percell/scripts/test_headless_segmentation.py /path/to/test/image
```

Look for output like:
```
✓ Cellpose Models Check
  Using Cellpose-SAM (CP-SAM) model
  Running CP-SAM with automatic scale detection
  Segmentation successful!
```

## Example Workflow

Complete example for using CP-SAM:

```bash
# 1. Install dependencies
source cellpose_venv/bin/activate
pip install cellpose[sam] roifile scikit-image tifffile

# 2. Verify GPU (optional but recommended)
python -c "import torch; print('GPU:', torch.cuda.is_available())"

# 3. Edit config
# Set: "headless": true, "model_type": "cpsam", "diameter": 0, "use_gpu": true

# 4. Run workflow
source venv/bin/activate
python -m percell.main

# 5. Check outputs
ls output_dir/ROIs/  # Should contain *_rois.zip files
```

## Diameter = 0 Explanation

Setting `diameter: 0` tells the system:
- **For standard Cellpose**: Use automatic diameter estimation (analyzes image)
- **For CP-SAM**: Use SAM's automatic scale detection (no diameter needed)

This is **recommended for CP-SAM** because:
1. SAM is designed to be scale-invariant
2. It can handle multiple scales in the same image
3. Removes the need to manually measure cell sizes

## Summary

Your configuration is set up correctly for CP-SAM!

**Current status:**
- ✅ Model: `cpsam`
- ✅ Diameter: `0` (auto-detection)
- ⚠️ Headless: `false` (change to `true` for automation)
- ⚠️ GPU: `false` (change to `true` if available - **highly recommended**)

**To activate:**
1. Install dependencies: `pip install cellpose[sam] roifile scikit-image tifffile`
2. Enable headless: Set `"headless": true` in config
3. Enable GPU (optional): Set `"use_gpu": true` if you have CUDA GPU
4. Run: `python -m percell.main`

**Next:** Ready to work on automating the thresholding steps?
