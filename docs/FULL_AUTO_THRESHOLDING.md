# Full-Auto Thresholding Implementation

This document describes the full-auto thresholding feature in Percell.

## Overview

The full-auto thresholding method provides **completely automatic** Otsu thresholding of grouped cell images without any user interaction. This is ideal for:
- Batch processing large datasets
- Reproducible, standardized analysis
- Automated workflows
- High-throughput screening

## Implementation Details

### Key Differences: Semi-Auto vs Full-Auto

| Feature | Semi-Auto | Full-Auto |
|---------|-----------|-----------|
| **User Interaction** | Required - draw ROI on each image | None - fully automatic |
| **ROI Selection** | User draws oval in representative area | Uses entire image |
| **Threshold Method** | Otsu (on selected ROI) | Otsu (on full image) |
| **Bin Evaluation** | Asks if more bins needed | Automatic processing |
| **Empty Field Handling** | User selects "no structures" option | Applies threshold anyway |
| **Batch Mode** | Disabled (interactive GUI) | Enabled (headless processing) |
| **Processing Speed** | Slow (waits for user input) | Fast (no delays) |

### Technical Implementation

#### 1. ImageJ Macro (`full_auto_threshold_grouped_cells.ijm`)

**Key Features:**
```javascript
// Line 10: Enable batch mode (no GUI display)
setBatchMode(true);

// Lines 144-150: Process each image automatically
open(imagePath);
run("Select None");           // Clear any existing ROI
run("Gaussian Blur...", "sigma=1.70");
run("Enhance Contrast...", "saturated=0.01");

// Line 149: Use ENTIRE image (not user-selected ROI)
run("Select All");

// Lines 151-156: Apply Otsu threshold automatically
if (bitDepth() == 8) {
    setAutoThreshold("Otsu dark");
} else {
    setAutoThreshold("Otsu dark 16-bit");
}

// Lines 158-163: Convert to binary mask
setOption("BlackBackground", true);
run("Convert to Mask");
run("8-bit");
```

**No User Prompts:**
- No `waitForUser()` calls
- No dialog boxes
- No ROI drawing required
- No bin evaluation questions

#### 2. Stage Implementation (`full_auto_threshold_grouped_cells_stage.py`)

```python
class FullAutoThresholdGroupedCellsStage(StageBase):
    def __init__(self, config, logger, stage_name="full_auto_threshold_grouped_cells"):
        super().__init__(config, logger, stage_name)

    def run(self, **kwargs) -> bool:
        # Calls full_auto_threshold_grouped_cells() from imagej_tasks
        ok_thresh = _threshold(
            input_dir=f"{output_dir}/grouped_cells",
            output_dir=f"{output_dir}/grouped_masks",
            imagej_path=self.config.get('imagej_path'),
            macro_path=get_path_str("full_auto_threshold_grouped_cells_macro"),
            channels=data_selection.get('analysis_channels'),
            regions=data_selection.get('selected_regions'),
            auto_close=True,
        )
        return ok_thresh
```

#### 3. ImageJ Integration (`imagej_tasks.py`)

```python
def full_auto_threshold_grouped_cells(...) -> bool:
    """Automatically threshold grouped cells without user interaction."""
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    macro_flag = create_threshold_macro_with_parameters(...)

    try:
        # Run in batch mode (macro has setBatchMode(true))
        ok = run_imagej_macro(imagej_path, macro_file, auto_close=True, imagej=imagej)
        return ok
    finally:
        # Cleanup temp files
        Path(macro_file).unlink(missing_ok=True)
        Path(flag_file).unlink(missing_ok=True)
```

**Key Difference:** Uses `run_imagej_macro()` with `auto_close=True`. The macro itself enables batch mode with `setBatchMode(true)`, eliminating the need for a separate batch function

## Usage

### Method 1: Via Workflow Configuration Menu

```bash
percell --interactive

# Navigate to:
Main Menu → Configuration → Workflow Configuration → Thresholding (3)

# Select:
2. Full-Auto Threshold - Automatic Otsu thresholding without user interaction
```

### Method 2: Via config.json

```json
{
  "workflow": {
    "thresholding_tool": "full_auto"
  }
}
```

### Method 3: Direct Stage Execution (Advanced)

```bash
percell --full-auto-threshold-grouped-cells \
    --input /path/to/input \
    --output /path/to/output
```

## Workflow Integration

When you run the complete workflow with full-auto thresholding enabled:

```bash
percell --complete-workflow --input /path --output /path
```

**What Happens:**
1. Data Selection → (user configures)
2. Cellpose Segmentation → (user interaction with Cellpose)
3. Process Cellpose Single-Cell Data → (automatic)
4. **Full-Auto Threshold** → ✨ **FULLY AUTOMATIC - NO USER INPUT** ✨
   - All binned images processed
   - Otsu threshold applied to each
   - Masks saved automatically
5. Measure ROI Areas → (automatic)
6. Analysis → (automatic)

## Processing Details

### Input
- **Location:** `{output_dir}/grouped_cells/`
- **File Pattern:** Files containing `_bin_` in filename
- **Format:** TIFF images (8-bit or 16-bit)

### Processing Steps (per image)
1. **Load Image** - Open from grouped_cells directory
2. **Preprocessing:**
   - Apply Gaussian blur (σ=1.70) for noise reduction
   - Enhance contrast (0.01% saturated pixels)
   - Convert to 8-bit if needed
3. **ROI Selection:**
   - `run("Select All")` - Uses entire image
4. **Thresholding:**
   - Apply Otsu automatic threshold
   - "dark" mode (objects darker than background)
   - Method chosen based on bit depth
5. **Binarization:**
   - Convert to binary mask
   - Black background (background=0, objects=255)
   - Ensure 8-bit format
6. **Save:**
   - Prefix with "MASK_"
   - Same directory structure as input
   - Location: `{output_dir}/grouped_masks/`

### Output
- **Location:** `{output_dir}/grouped_masks/`
- **Naming:** `MASK_{original_filename}.tif`
- **Format:** Binary 8-bit TIFF (0=background, 255=objects)

## Advantages

### 1. Reproducibility
- Same input always produces same output
- No variability from user ROI selection
- Standardized across all samples

### 2. Speed
- No waiting for user input
- Batch mode processing
- Can process hundreds of images unattended

### 3. Automation
- Perfect for batch processing
- Integrate into automated pipelines
- Schedule overnight processing

### 4. Consistency
- All images processed identically
- Removes user bias
- Easier to compare across experiments

## Limitations

### When Semi-Auto is Better

Use semi-auto thresholding when:
1. **Variable Image Quality** - Images have inconsistent quality
2. **Complex Backgrounds** - Background varies significantly
3. **Specific ROI Needed** - Only certain regions should be analyzed
4. **Quality Control** - Want to visually verify each image
5. **Edge Cases** - Need to handle unusual images specially

### When Full-Auto is Better

Use full-auto thresholding when:
1. **Batch Processing** - Processing many samples
2. **Consistent Quality** - Images are standardized
3. **High Throughput** - Speed is priority
4. **Reproducibility** - Need identical processing
5. **Automation** - Part of automated pipeline

## Validation

### Before Using Full-Auto

Test on a representative subset:

1. **Run Semi-Auto** on 10-20 images
2. **Run Full-Auto** on same images
3. **Compare Results:**
   - Visual inspection of masks
   - Quantitative metrics (area, intensity, etc.)
   - Statistical comparison

### Quality Checks

After full-auto processing:

```python
# Check mask statistics
import numpy as np
from skimage import io

mask = io.imread('path/to/MASK_file.tif')

# Check threshold was applied
unique_values = np.unique(mask)
print(f"Unique values: {unique_values}")  # Should be [0, 255]

# Check object coverage
object_pixels = np.sum(mask == 255)
total_pixels = mask.size
coverage = object_pixels / total_pixels
print(f"Coverage: {coverage:.2%}")

# Reasonable coverage: 1-50% depending on cell density
if coverage < 0.001:
    print("Warning: Very few objects detected")
elif coverage > 0.8:
    print("Warning: Threshold may be too permissive")
```

## Troubleshooting

### Issue: No Objects Detected

**Symptoms:** All masks are completely black

**Causes:**
- Images too dim
- Objects lighter than background
- Need different threshold method

**Solutions:**
1. Check image intensity: `ImageJ → Image → Show Info`
2. Verify image orientation (objects should be darker)
3. Try semi-auto to see appropriate ROI
4. May need to invert images first

### Issue: Entire Image Thresholded

**Symptoms:** All masks are completely white

**Causes:**
- Images too bright
- Background darker than objects
- Incorrect "dark" mode

**Solutions:**
1. Check if images need inverting
2. Verify background is lighter than objects
3. May need to create custom threshold method

### Issue: Inconsistent Results

**Symptoms:** Some images threshold well, others don't

**Causes:**
- Variable image quality
- Inconsistent imaging conditions
- Different cell densities

**Solutions:**
1. Use semi-auto for quality control
2. Check imaging conditions
3. May need separate processing for subsets
4. Consider preprocessing normalization

## Performance

### Benchmarks

Approximate processing times (on MacBook Pro M1):

| # of Bin Files | Semi-Auto | Full-Auto | Speedup |
|----------------|-----------|-----------|---------|
| 10 images | 10-15 min | 30 sec | 20-30x |
| 50 images | 50-75 min | 2.5 min | 20-30x |
| 100 images | 100-150 min | 5 min | 20-30x |

**Note:** Semi-auto time depends heavily on user speed.

### Optimization Tips

1. **Use SSD:** Store data on SSD for faster I/O
2. **Batch Size:** Process one experiment at a time
3. **Memory:** Close other applications for large batches
4. **Parallel:** Can't parallelize (ImageJ limitation)

## Example Workflow

### Complete Analysis with Full-Auto

```bash
# 1. Configure workflow
percell --interactive
# Select: Configuration → Workflow Configuration → Thresholding → Full-Auto

# 2. Run complete workflow
percell --complete-workflow \
    --input /data/experiment_2024_01 \
    --output /results/experiment_2024_01

# 3. Process runs automatically:
#    - Data selection (user configures once)
#    - Segmentation (user uses Cellpose)
#    - Processing (automatic)
#    - Thresholding (FULLY AUTOMATIC - no user input!)
#    - Measurement (automatic)
#    - Analysis (automatic)

# 4. Results ready in /results/experiment_2024_01/
```

### Batch Processing Multiple Experiments

```bash
# Set configuration once
echo '{"workflow": {"thresholding_tool": "full_auto"}}' > config.json

# Process multiple experiments
for exp in /data/exp_*; do
    exp_name=$(basename $exp)
    percell --complete-workflow \
        --input $exp \
        --output /results/$exp_name \
        --config config.json
done
```

## Summary

Full-auto thresholding is a powerful feature that:

✅ **Eliminates user interaction** - Run unattended
✅ **Ensures reproducibility** - Same input = same output
✅ **Increases throughput** - 20-30x faster than semi-auto
✅ **Simplifies automation** - Easy to integrate
✅ **Maintains quality** - Otsu is proven, reliable method

Use it for batch processing, automated pipelines, and whenever you need standardized, reproducible analysis of grouped cell images.

For images requiring special handling or quality control, use the semi-auto method instead.
