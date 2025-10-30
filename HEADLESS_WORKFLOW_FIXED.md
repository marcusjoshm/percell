# Headless Segmentation Workflow - Fixed

## What Was Fixed

The headless segmentation was saving ROI files to the wrong location. It has been corrected to match the expected workflow.

## Correct Workflow

### Step 1: Bin Images
Images are binned 4x4 and saved to preprocessed directory:
```
output_dir/preprocessed/
  └── A549_As_treated/
      └── timepoint_1/
          ├── bin4x4_image1.tif
          ├── bin4x4_image2.tif
          └── ...
```

### Step 2: Headless Segmentation (NEW - AUTOMATED)
ROI files are saved **in the same directory** as the binned images:
```
output_dir/preprocessed/
  └── A549_As_treated/
      └── timepoint_1/
          ├── bin4x4_image1.tif
          ├── bin4x4_image1_rois.zip     ← NEW: ROI file
          ├── bin4x4_image1_mask.tif     ← NEW: Mask file
          ├── bin4x4_image2.tif
          ├── bin4x4_image2_rois.zip     ← NEW: ROI file
          └── ...
```

### Step 3: Resize ROIs (Existing Workflow)
The `resize_rois` step finds ROI files in preprocessed directory and resizes them:
```
output_dir/ROIs/
  └── A549_As_treated/
      ├── ROIs_image1_rois.zip    ← Resized ROIs
      ├── ROIs_image2_rois.zip
      └── ...
```

## What Changed

### Before (Incorrect)
```python
# Was saving to separate output directory
roi_files = adapter.run_segmentation(
    images=images,
    output_dir=Path(f"{output_dir}/ROIs"),  # ❌ Wrong location
    ...
)
```

### After (Correct)
```python
# Now saves to preprocessed directory (same as binned images)
roi_files = adapter.run_segmentation(
    images=images,
    output_dir=Path(preprocessed_dir),  # ✓ Correct location
    ...
)
```

### Adapter Change
In `headless_cellpose_adapter.py`, the script now saves ROIs in the **same directory** as input images:

```python
# Before: Created separate output subdirectory
subdir_output = output_dir / subdir_name  # ❌ Wrong

# After: Saves in same directory as images
cmd = [
    "--input_dir", str(input_dir),
    "--output_dir", str(input_dir),  # ✓ Same directory
    ...
]
```

## Current Configuration

Your `percell/config/config.json` is now set up correctly:

```json
"segmentation": {
  "headless": true,        // ✓ Enabled
  "model_type": "cpsam",   // ✓ Using CP-SAM
  "diameter": 0,           // ✓ Auto-detect for SAM
  "flow_threshold": 0.4,
  "cellprob_threshold": 0.0,
  "min_area": 10,
  "use_gpu": false        // Set to true if you have GPU
}
```

## Expected Output Structure

After running the complete workflow with headless segmentation:

```
output_dir/
├── raw_data/              # Original images
├── preprocessed/          # Binned images + ROI files from segmentation
│   └── A549_As_treated/
│       └── timepoint_1/
│           ├── bin4x4_image1.tif
│           ├── bin4x4_image1_rois.zip      ← From headless segmentation
│           ├── bin4x4_image1_mask.tif      ← From headless segmentation
│           └── ...
├── ROIs/                  # Resized ROIs (from resize_rois step)
│   └── A549_As_treated/
│       ├── ROIs_image1_rois.zip
│       └── ...
├── cells/                 # Extracted cells
├── grouped_cells/         # Grouped by intensity
├── grouped_masks/         # Thresholded masks
├── combined_masks/        # Combined masks
├── masks/                 # Individual cell masks
└── analysis/             # Final analysis results
```

## Running the Workflow

Now that everything is configured correctly:

```bash
# 1. Make sure dependencies are installed
source cellpose_venv/bin/activate
pip install cellpose[sam] roifile scikit-image tifffile
deactivate

# 2. Run the workflow
source venv/bin/activate
python -m percell.main
```

The segmentation will now:
1. ✅ Run automatically (no GUI)
2. ✅ Save ROIs in the correct location
3. ✅ Allow the workflow to continue seamlessly

## Verification

Check that ROI files are created in the right place:

```bash
# After segmentation stage completes, check:
ls -la output_dir/preprocessed/A549_As_treated/timepoint_1/*.zip

# You should see files like:
# bin4x4_image1_rois.zip
# bin4x4_image2_rois.zip
# ...
```

## Next Steps

Now that segmentation is automated, the next steps you mentioned:

1. ✅ **Segmentation** - Fully automated with CP-SAM
2. 🔄 **Thresholding** - Next to automate
3. ✅ **ROI Tracking** - Already works automatically
4. ✅ **Cell Extraction** - Already works in batch mode

Ready to work on automating the thresholding steps next?
