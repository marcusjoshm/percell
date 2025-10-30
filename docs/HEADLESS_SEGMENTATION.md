# Headless Cellpose Segmentation

This document describes how to use the new headless (automated) segmentation feature in Percell.

## Overview

The headless segmentation feature allows you to run Cellpose segmentation automatically without the GUI, making the workflow fully automated. The script:

1. Runs Cellpose segmentation in headless mode
2. Generates segmentation masks automatically
3. Converts masks to ImageJ-formatted ROI files
4. Supports all standard Cellpose parameters

## Requirements

Install the required dependencies in your Cellpose environment:

```bash
# Activate your cellpose virtual environment
source cellpose_venv/bin/activate  # or your cellpose environment path

# Install dependencies
pip install cellpose roifile scikit-image tifffile
```

## Configuration

Add the following settings to your `percell_config.yaml`:

```yaml
# Enable headless mode
segmentation:
  headless: true                    # Set to true for automated mode
  model_type: cyto2                 # Options: cyto, cyto2, nuclei, cyto3
  diameter: 30.0                    # Expected cell diameter in pixels
  flow_threshold: 0.4               # Higher = fewer cells (range: 0-1)
  cellprob_threshold: 0.0           # Higher = fewer cells (range: -6 to 6)
  min_area: 10                      # Minimum ROI area in pixels
  use_gpu: false                    # Set to true if GPU available
```

### Configuration Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `headless` | `false` | Enable automated headless mode (no GUI) |
| `model_type` | `cyto2` | Cellpose model: `cyto`, `cyto2`, `nuclei`, `cyto3` |
| `diameter` | `30.0` | Expected cell diameter in pixels (set to 0 for auto-detection) |
| `flow_threshold` | `0.4` | Flow error threshold (higher = more stringent, fewer cells) |
| `cellprob_threshold` | `0.0` | Cell probability threshold (higher = fewer cells) |
| `min_area` | `10` | Minimum ROI area in pixels (filter out small objects) |
| `use_gpu` | `false` | Use GPU acceleration if available |

## Usage

### Method 1: Through the Percell Workflow

Simply run your standard Percell workflow with the configuration above:

```bash
source venv/bin/activate
python -m percell.main
```

The segmentation stage will automatically run in headless mode if `segmentation.headless: true` is set in your config.

### Method 2: Standalone Script

You can also use the headless segmentation script directly:

```bash
# Activate cellpose environment
source cellpose_venv/bin/activate

# Run segmentation
python percell/scripts/headless_cellpose_segmentation.py \
    --input_dir /path/to/images \
    --output_dir /path/to/output \
    --model_type cyto2 \
    --diameter 30 \
    --flow_threshold 0.4 \
    --cellprob_threshold 0.0 \
    --min_area 10
```

#### Standalone Script Options

```
Required arguments:
  -i, --input_dir PATH        Input directory containing images
  -o, --output_dir PATH       Output directory for masks and ROIs

Cellpose parameters:
  --model_type {cyto,cyto2,nuclei,cyto3}
                              Cellpose model (default: cyto2)
  --diameter FLOAT            Expected cell diameter (default: 30)
  --channels INT INT          Channel config [cytoplasm nucleus] (default: 0 0)
  --flow_threshold FLOAT      Flow error threshold (default: 0.4)
  --cellprob_threshold FLOAT  Cell probability threshold (default: 0.0)

ROI parameters:
  --min_area INT              Minimum ROI area in pixels (default: 10)

Processing options:
  --gpu                       Use GPU acceleration
  --no_save_masks             Don't save masks, only ROIs
  --pattern PATTERN           File pattern (default: *.tif)
  --verbose                   Enable debug logging
```

## Output Files

The headless segmentation generates the following outputs:

```
output_dir/
├── condition1/
│   ├── image1_mask.tif           # Segmentation mask (labeled)
│   ├── image1_rois.zip           # ImageJ ROI file
│   ├── image2_mask.tif
│   └── image2_rois.zip
└── condition2/
    ├── image3_mask.tif
    └── image3_rois.zip
```

### File Formats

- **Mask files** (`*_mask.tif`): 16-bit TIFF images where each cell has a unique integer ID
- **ROI files** (`*_rois.zip`): ImageJ-compatible ZIP archives containing polygon ROIs

## Tips for Good Segmentation

### 1. Choosing the Right Model

- **`cyto`/`cyto2`**: For cytoplasm/whole-cell segmentation
- **`nuclei`**: For nuclear segmentation
- **`cyto3`**: Latest generalist model (requires newer Cellpose)

### 2. Setting Cell Diameter

The diameter parameter is critical:

- Measure typical cell diameter in pixels using ImageJ
- Set to `0` for automatic diameter estimation (slower but more flexible)
- Too small → over-segmentation (cells split)
- Too large → under-segmentation (cells merged)

### 3. Adjusting Thresholds

**Flow Threshold** (`flow_threshold`):
- Default: `0.4`
- Increase (e.g., `0.6`) if you get too many false positives
- Decrease (e.g., `0.2`) if you miss cells

**Cell Probability Threshold** (`cellprob_threshold`):
- Default: `0.0`
- Increase (e.g., `0.5`) to be more stringent
- Decrease (e.g., `-2.0`) to detect fainter cells

### 4. GPU Acceleration

If you have a CUDA-compatible GPU:

```yaml
segmentation:
  use_gpu: true
```

This can speed up processing by 10-100x depending on your GPU.

## Troubleshooting

### Issue: No ROIs generated

**Solutions:**
- Lower `flow_threshold` (try `0.2`)
- Lower `cellprob_threshold` (try `-2.0`)
- Check that `diameter` matches your actual cells
- Verify image quality and contrast

### Issue: Too many false positives

**Solutions:**
- Increase `flow_threshold` (try `0.6`)
- Increase `cellprob_threshold` (try `0.5`)
- Increase `min_area` to filter small objects

### Issue: Cells are split or merged

**Solutions:**
- Adjust `diameter` parameter
- Try a different `model_type`
- Consider using `diameter: 0` for auto-detection

### Issue: Import errors

Make sure all dependencies are installed:

```bash
pip install cellpose roifile scikit-image tifffile
```

### Issue: GPU not working

Check CUDA installation:

```bash
python -c "import torch; print(torch.cuda.is_available())"
```

If False, you need to install CUDA-compatible PyTorch. See: https://pytorch.org/get-started/locally/

## Comparing GUI vs Headless

| Feature | GUI Mode | Headless Mode |
|---------|----------|---------------|
| User interaction | Required | None (fully automated) |
| Parameter tuning | Interactive | Pre-configured |
| Speed | Depends on user | Fast and consistent |
| Reproducibility | Variable | Perfect (same params = same result) |
| Best for | Exploration, difficult samples | Production, batch processing |

## Example Workflow

Here's a complete example configuration for automated processing:

```yaml
# percell_config.yaml

# Paths
imagej_path: /Applications/ImageJ.app/Contents/MacOS/ImageJ
cellpose_path: cellpose_venv/bin/python

# Automated segmentation
segmentation:
  headless: true
  model_type: cyto2
  diameter: 35.0
  flow_threshold: 0.5
  cellprob_threshold: 0.2
  min_area: 20
  use_gpu: true

# Data selection
data_selection:
  selected_conditions:
    - control
    - treatment
  selected_regions:
    - R_01
    - R_02
  selected_timepoints:
    - t00
    - t01
    - t02
  segmentation_channel: ch00
```

Then run:

```bash
source venv/bin/activate
python -m percell.main
```

The entire workflow will run automatically!

## Advanced: Parameter Optimization

To find optimal parameters for your dataset:

1. **Start with GUI mode** to test different settings interactively
2. **Record the parameters** that work best
3. **Switch to headless mode** with those parameters for batch processing

## Next Steps

After segmentation, the workflow continues with:
1. ROI tracking across timepoints
2. ROI resizing (if images were binned)
3. Cell extraction
4. Intensity analysis

All of these steps can also be automated! See the main Percell documentation for details.

## References

- [Cellpose Documentation](https://cellpose.readthedocs.io/)
- [ImageJ ROI Format](https://imagej.net/ij/docs/guide/146-30.html)
- [roifile Python Package](https://pypi.org/project/roifile/)
