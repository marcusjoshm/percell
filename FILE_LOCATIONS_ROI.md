# Percell ROI Code Locations - Detailed Reference

## Domain Layer (Business Logic)

### ROI Model Definition
- **File**: `/Users/leelab/percell/percell/domain/models.py`
- **Lines**: 128-142
- **Class**: `ROI`
- **Key Attributes**: `id`, `label`, `polygon`, `mask_path`

```python
@dataclass(slots=True)
class ROI:
    id: int
    label: Optional[str] = None
    polygon: Optional[list[Tuple[int, int]]] = None
    mask_path: Optional[Path] = None
```

### Cell Segmentation Service
- **File**: `/Users/leelab/percell/percell/domain/services/cell_segmentation_service.py`
- **Key Methods**:
  - `calculate_roi_scaling()` - Scale ROI coordinates by binning factor
  - `validate_segmentation_results()` - Validate ROI outputs against expectations
  
**Note**: No edge filtering logic here

### Intensity Analysis Service
- **File**: `/Users/leelab/percell/percell/domain/services/intensity_analysis_service.py`
- **Key Methods**:
  - `measure_cell_intensity()` - Calculate per-cell metrics
  - `group_cells_by_brightness()` - Group cells by intensity

**Note**: No edge filtering logic here

---

## Application Layer (Orchestration & Stages)

### ImageJ Task Helpers
**File**: `/Users/leelab/percell/percell/application/imagej_tasks.py`

**KEY FUNCTION - MEASURE ROI AREAS** (BEST EDGE FILTERING POINT)
- **Location**: Lines 284-338
- **Function**: `measure_roi_areas()`
- **Purpose**: Measure area of each ROI via ImageJ macro
- **Parameters**:
  - `input_dir`: Raw image directory
  - `output_dir`: Output directory
  - `imagej_path`: Path to ImageJ executable
  - `macro_path`: Path to measure_roi_area.ijm
  - `channels`: Optional channel filter
  - `auto_close`: Auto-close ImageJ flag
- **Returns**: `bool` (success/failure)

**Related Helper Functions**:
- `find_roi_image_pairs()` (Lines 203-281): Discover ROI-image pairs with channel filtering
- `create_measure_macro_with_parameters()` (Lines 166-200): Embed parameters in macro

**Other ROI-Related Functions**:
- `resize_rois()` (Lines 132-164) - Scale ROIs from binned to full resolution
  - Macro: `resize_rois.ijm`
- `extract_cells()` (Lines 767-889) - Extract cell patches using ROIs
  - Macro: `extract_cells.ijm`
- `create_cell_masks()` (Lines 599-659) - Create binary masks per ROI
  - Macro: `create_cell_masks.ijm`
- `analyze_masks()` (Lines 458-522) - Run Analyze Particles on masks
  - Macro: `analyze_cell_masks.ijm`

### Image Processing Tasks
**File**: `/Users/leelab/percell/percell/application/image_processing_tasks.py`

**ROI-Related Functions**:
- `track_rois()` (Lines 1233+) - Match ROIs across timepoints
  - Helper: `_match_rois_with_distance()` (Lines 822-877)
  - Helper: `_build_tracks_across_timepoints()` (Lines 880-1005)
  - Helper: `_roi_center()` (Lines 805-819) - Calculate ROI centroid
  - Helper: `_polygon_centroid()` (Lines 787-802) - Polygon area/centroid

- `duplicate_rois_for_channels()` (Lines 534-591) - Copy ROIs per channel

- `group_cells()` (Lines 370-531) - Organize cells into spatial bins
  - Helper: `_find_cell_dirs()` (Lines 355-368)

- `combine_masks()` (Lines 271-353) - Merge masks by condition

- `include_group_metadata()` (Lines 626-762) - Merge analysis with group info

**ROI Loading/Parsing**:
- `_load_roi_dict()` (Lines 763-772) - Load ROI ZIP as dictionary
- `_load_roi_bytes()` (Lines 774-785) - Load ROI ZIP as raw bytes

---

## Pipeline Stages

### Stage Registry
**File**: `/Users/leelab/percell/percell/application/stage_registry.py`
- **Function**: `register_all_stages()`
- **Purpose**: Register all 8 pipeline stages in execution order
- **Order**: 0=complete_workflow → 8=cleanup

### Process Single-Cell Data Stage (Stage 4)
**File**: `/Users/leelab/percell/percell/application/stages/process_single_cell_stage.py`
- **Class**: `ProcessSingleCellDataStage`
- **Key Sub-steps** (lines 73-154):
  1. ROI tracking (if multi-timepoint)
  2. ROI resizing
  3. ROI duplication for channels
  4. Cell extraction
  5. Cell grouping
- **No filtering at this stage**

### Measure ROI Area Stage (Stage 6) - RECOMMENDED EDGE FILTERING LOCATION
**File**: `/Users/leelab/percell/percell/application/stages/measure_roi_area_stage.py`
- **Class**: `MeasureROIAreaStage`
- **Lines 62-124**: Main `run()` method
- **Calls**: `_measure_roi_areas()` from `imagej_tasks.py`
- **Output**: CSV files in `analysis/` directory
- **Integration Point for Edge Filtering**: After CSV creation but before downstream stages

### Analysis Stage (Stage 7)
**File**: `/Users/leelab/percell/percell/application/stages/analysis_stage.py`
- **Class**: `AnalysisStage`
- **Key Sub-steps**:
  1. Combine masks
  2. Create cell masks
  3. Analyze cell masks
  4. Include group metadata

---

## ImageJ Macros

### measure_roi_area.ijm (RECOMMENDED FILTERING LOCATION)
**File**: `/Users/leelab/percell/percell/macros/measure_roi_area.ijm`
- **Lines 1-8**: Parameter declarations
- **Lines 40-52**: Debug output, ROI counting
- **Lines 54-59**: List all ROI names (debug)
- **Lines 78-107**: Measurement loop
  - **Line 89**: `roiManager("Select", i)` - Select ROI
  - **Line 93**: `getStatistics(area, ...)` - Get area
  - **Line 103-106**: Add to results table
- **Line 127**: `saveAs("Results", csv_file)` - Save CSV

**EDGE FILTERING IMPLEMENTATION**: Insert after line 93, before line 103:
```javascript
roi_bounds = Roi.getBounds();  // [x, y, width, height]
image_width = getWidth();
image_height = getHeight();
margin = 5;  // pixels (make configurable)

is_edge = (roi_bounds[0] <= margin ||
           roi_bounds[0] + roi_bounds[2] >= image_width - margin ||
           roi_bounds[1] <= margin ||
           roi_bounds[1] + roi_bounds[3] >= image_height - margin);

if (is_edge) {
    print("Skipping edge ROI: " + roi_name);
    continue;
}
```

### Other Macros

**resize_rois.ijm**
- **File**: `/Users/leelab/percell/percell/macros/resize_rois.ijm`
- **Lines 140-189**: ROI processing loop
- **Purpose**: Scale ROIs from binned images

**extract_cells.ijm**
- **File**: `/Users/leelab/percell/percell/macros/extract_cells.ijm`
- **Lines 61-83**: ROI-based cell extraction
- **Line 71**: `run("Clear Outside")` - Mask to ROI

**create_cell_masks.ijm**
- **File**: `/Users/leelab/percell/percell/macros/create_cell_masks.ijm`
- **Lines 61-83**: ROI-based mask creation
- **Line 71**: `run("Clear Outside")` - Mask to ROI

**analyze_cell_masks.ijm**
- **File**: `/Users/leelab/percell/percell/macros/analyze_cell_masks.ijm`
- **Lines 34-71**: Process each mask file
- **Line 61**: `run("Analyze Particles...")` - Particle analysis

---

## Data Flow & File Locations

### ROI Storage Locations

**After Segmentation (Stage 3)**:
- Location: `{output_dir}/preprocessed/{condition}/*.zip`
- Files: `preprocessed_*.zip`
- Format: ImageJ ROI Manager ZIP

**After Resizing (Stage 4.2)**:
- Location: `{output_dir}/ROIs/{condition}/*.zip`
- Files: `ROIs_*_rois.zip`
- Format: Scaled to full image dimensions

**After Duplication (Stage 4.3)**:
- Location: `{output_dir}/ROIs/{condition}/*.zip`
- Files: `ROIs_*_ch00_rois.zip`, `ROIs_*_ch01_rois.zip`, etc.

### Output Files

**After Measure ROI Area (Stage 6)**:
- Location: `{output_dir}/analysis/`
- Files: `{condition}_{region}_{channel}_{timepoint}_cell_area.csv`
- Columns: Label, Area, Image, Cell_ID
- **This is the filtering point**

**After Analysis (Stage 7)**:
- Location: `{output_dir}/analysis/`
- Files: `{condition}_{region}_{channel}_{timepoint}_particle_analysis.csv`
- Columns: Particle metrics (Area, Perimeter, etc.)

---

## Import Statements for Integration

### For Python-Level Edge Filtering

```python
# In imagej_tasks.py or stages/measure_roi_area_stage.py
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Optional

# For ROI bounds from ZIP files
from percell.application.image_processing_tasks import _load_roi_dict

# For image dimension extraction
import tifffile  # Already in dependencies
```

### For ImageJ Macro Modifications

No additional imports needed in ImageJ macros—all functionality available in standard ImageJ/Fiji.

---

## Testing Locations

### Unit Tests
- **File**: `tests/unit/domain/test_intensity_analysis_service.py`
- **File**: `tests/unit/application/test_menu_system.py`
- Add new tests for edge filtering logic here

### Integration Tests
- **Files**: `tests/integration/test_imagej_integration_in_measure_roi_area.py`
- **File**: `tests/integration/test_workflow_coordinator.py`
- Add integration tests for full pipeline with edge exclusion

---

## Summary: Where to Make Changes

### For Minimal Edge Exclusion Feature

1. **Modify ImageJ Macro**:
   - File: `/Users/leelab/percell/percell/macros/measure_roi_area.ijm`
   - Add: ROI bounds check before adding to results table
   - Scope: ~10 lines of code

2. **Modify Python Stage** (Optional, for bypass):
   - File: `/Users/leelab/percell/percell/application/stages/measure_roi_area_stage.py`
   - Add: CSV filtering after macro execution
   - Scope: ~15 lines of code

3. **Modify Task Function**:
   - File: `/Users/leelab/percell/percell/application/imagej_tasks.py`
   - Add: Parameters `exclude_edge_rois`, `edge_margin_pixels`
   - Add: Helper function `_filter_edge_rois()`
   - Scope: ~30-40 lines of code

### For Full Feature Integration

4. Add CLI parameter:
   - File: `percell/application/cli_parser.py`
   
5. Add configuration:
   - File: `percell/domain/models.py` - New `EdgeExclusionConfig` class
   
6. Add domain service:
   - File: `percell/domain/services/` - New `EdgeDetectionService`

7. Add tests:
   - Files: `tests/unit/` and `tests/integration/`

