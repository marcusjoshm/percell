# Auto-Threshold Analysis Module

## Overview

The Auto-Threshold Analysis module provides automated thresholding capabilities for microscopy images with ROI (Region of Interest) processing. This is a standalone module that can be used independently of the complete PerCell workflow. It processes .tif images with structured naming patterns and applies thresholding within specific regions defined by .zip ROI files.

### File Naming Convention

Input .tif files should follow the pattern:
```
base_name_s{s}_z{z}_ch{c}_t{t}.tif
```

Where:
- `base_name`: The base name of the file (used to match with ROI files)
- `s{s}`: Site/tile number (optional)
- `z{z}`: Z-stack position (optional) 
- `ch{c}`: Channel number (required for matching)
- `t{t}`: Timepoint (optional)

The module extracts the base name (everything before the first pattern) and matches it with corresponding ROI files that have the same base name.

## Features

- **Otsu Thresholding**: Uses Otsu's method for automatic binary mask creation
- **ROI-Based Processing**: Apply thresholding within specific regions of interest
- **Channel-Specific Processing**: Target specific channels using structured naming patterns (_ch{d+})
- **Batch Processing**: Process multiple images and ROIs automatically
- **Quality Assessment**: Evaluate thresholding results with particle analysis
- **Comprehensive Reporting**: Generate detailed statistics and HTML reports
- **Flexible Input**: Support for TIFF images and ZIP ROI files

## Installation

The auto-threshold module is part of the PerCell package. Make sure you have the following dependencies:

- Python 3.7+
- ImageJ (for thresholding operations)
- pandas (for report generation)

## Usage

### Standalone Script

Run the auto-threshold analysis using the standalone launcher:

```bash
python percell_auto_threshold.py --input /path/to/images --ROIs /path/to/rois --channel ch0 --output /path/to/results --method otsu
```

### Basic Examples

1. **Simple Otsu thresholding with ROI processing**:
   ```bash
   python percell_auto_threshold.py --input ./images --ROIs ./rois --channel ch0 --output ./results --method otsu
   ```
   This will process files like `experiment1_s1_z0_ch0_t0.tif` and match them with `experiment1.zip` ROI files.

2. **Triangle method with quality assessment**:
   ```bash
   python percell_auto_threshold.py --input ./images --ROIs ./rois --channel ch1 --output ./results --method triangle --quality-assessment
   ```
   This will process files like `experiment1_s1_z0_ch1_t0.tif` and match them with `experiment1.zip` ROI files.

3. **Yen method with HTML report**:
   ```bash
   python percell_auto_threshold.py --input ./images --ROIs ./rois --channel ch0 --output ./results --method yen --generate-report
   ```

4. **Specify ImageJ path**:
   ```bash
   python percell_auto_threshold.py --input ./images --ROIs ./rois --channel ch0 --output ./results --method otsu --imagej-path /Applications/ImageJ.app/Contents/MacOS/ImageJ
   ```

### Command Line Arguments

| Argument | Description | Default | Required |
|----------|-------------|---------|----------|
| `--input`, `-i` | Input directory containing .tif images | - | Yes |
| `--ROIs`, `-r` | Directory containing .zip ROI files | - | Yes |
| `--channel`, `-c` | Channel number to match (e.g., ch0, ch1) - matches _ch{d+} pattern in filenames | - | Yes |
| `--output`, `-o` | Output directory for results | - | Yes |
| `--method`, `-m` | Thresholding method (currently fixed to Otsu) | otsu | No |
| `--quality-assessment` | Perform quality assessment | False | No |
| `--imagej-path` | Path to ImageJ executable (currently hardcoded to Fiji) | Hardcoded | No |
| `--generate-report` | Generate HTML report | False | No |
| `--verbose`, `-v` | Enable verbose logging | False | No |

### Thresholding Method

Currently, the module uses **Otsu's method** for automatic thresholding. This method automatically determines the optimal threshold value by maximizing the variance between foreground and background pixel intensities.

## Output Structure

The module creates the following directory structure:

```
output_directory/
├── thresholded_masks/          # Binary mask images (ROI-based)
├── statistics/                 # CSV files with measurements
│   └── roi_thresholding_stats.csv
├── quality_assessment/         # Quality metrics (if enabled)
│   ├── image1_roi1_quality.txt
│   ├── image1_roi2_quality.txt
│   └── ...
└── auto_threshold_report.html  # HTML report (if generated)
```

### Statistics File

The `roi_thresholding_stats.csv` file contains:
- Image name
- ROI name
- Channel information
- Area (pixels)
- Mean intensity
- Standard deviation
- Integrated density (IntDen)
- Raw integrated density (RawIntDen)

### Quality Assessment

When enabled, quality assessment provides:
- Number of ROIs processed
- Threshold value used
- Binary mask information
- Processing summary

## Integration with PerCell

While this module is designed to be standalone, it can be integrated with the main PerCell pipeline by importing the `AutoThresholdAnalyzer` class:

```python
from percell.modules.auto_threshold_analysis import AutoThresholdAnalyzer

analyzer = AutoThresholdAnalyzer(config)
success = analyzer.run_thresholding_analysis_with_rois(
    input_dir="/path/to/images",
    rois_dir="/path/to/rois",
    channel="ch0",
    output_dir="/path/to/results",
    method="otsu",
    quality_assessment=True
)
```

## Troubleshooting

### Common Issues

1. **ImageJ not found**: Specify the ImageJ path using `--imagej-path`
2. **No images found**: Check that the input directory contains supported image formats
3. **Permission errors**: Ensure write permissions for the output directory

### Supported File Formats

- **Images**: TIFF (.tif, .tiff) files containing microscopy data
- **ROIs**: ZIP (.zip) files containing ImageJ ROI definitions

### ImageJ/Fiji Requirements

The module currently uses a hardcoded path to Fiji:
- **macOS**: `/Applications/Fiji.app/Contents/MacOS/ImageJ-macosx`

Make sure Fiji is installed at this location, or modify the hardcoded path in the script.

## Development

The auto-threshold module is located at `percell/modules/auto_threshold_analysis.py`. To extend the functionality:

1. Add new thresholding methods to the `thresholding_methods` dictionary
2. Modify the ImageJ macro generation in `_generate_macro_content()`
3. Add new quality metrics in the macro template

## License

This module is part of the PerCell package and follows the same license terms.
