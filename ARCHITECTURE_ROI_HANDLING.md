# Percell ROI Handling Architecture & Edge Exclusion Integration Plan

## Executive Summary

Percell is a scientific image analysis framework for single-cell microscopy that integrates Cellpose segmentation with ImageJ macros using clean hexagonal architecture. ROIs (Regions of Interest) represent detected cells and flow through multiple processing stages from segmentation to analysis. Currently, there is **no edge cell exclusion logic**—all cells detected within image boundaries are processed.

---

## 1. ROI Handling Architecture

### 1.1 ROI Representation (Domain Model)

**File**: `/Users/leelab/percell/percell/domain/models.py` (lines 128-142)

```python
@dataclass(slots=True)
class ROI:
    """Region of interest representing a cell or object boundary.
    
    Attributes:
        id: ROI identifier.
        label: Optional label describing the ROI.
        polygon: Optional list of (x, y) vertices.
        mask_path: Optional path to a binary mask file representing the ROI.
    """
    
    id: int
    label: Optional[str] = None
    polygon: Optional[list[Tuple[int, int]]] = None
    mask_path: Optional[Path] = None
```

**Key Points**:
- ROIs have optional polygon vertices (x, y coordinates)
- Can reference binary mask files on disk
- Support both vector (polygon) and raster (mask) representations
- Minimal metadata—ID-centric design

### 1.2 ROI Storage & Format

ROIs are stored as **ZIP files** containing ImageJ ROI Manager format:

- **Location**: `{output_dir}/ROIs/{condition}/*.zip`
- **Content**: Serialized ROI data readable by ImageJ ROI Manager
- **Naming**: `{prefix}_{region}_{channel}_{timepoint}_rois.zip`
- **Examples**: `ROIs_R_1_ch00_t1_rois.zip`, `preprocessed_R_1_ch00_t1_rois.zip`

**Loading/Parsing**:
- `percell/application/image_processing_tasks.py` (lines 763-785): `_load_roi_dict()`, `_load_roi_bytes()`
- Uses `zipfile` module to extract ROI data
- Converts to dictionary with keys: `x`, `y`, `left`, `top`, `width`, `height`, `type`, etc.

---

## 2. Analysis Pipeline/Workflow Structure

### 2.1 Pipeline Stages (Execution Order)

**File**: `/Users/leelab/percell/percell/application/stage_registry.py`

```
Order  Stage Name                  File
---    ---------                  ----
0      complete_workflow          (meta-stage)
1      advanced_workflow          (interactive builder)
2      data_selection             data_selection_stage.py
3      segmentation               segmentation_stage.py
4      process_single_cell        process_single_cell_stage.py
5      threshold_grouped_cells    threshold_grouped_cells_stage.py
6      measure_roi_area           measure_roi_area_stage.py
7      analysis                   analysis_stage.py
8      cleanup                    cleanup_stage.py
```

### 2.2 ROI Processing Stages in Detail

#### **Stage 3: Segmentation**
- **Input**: Raw microscope images (binned 2x or 4x for performance)
- **Tool**: Cellpose (external segmentation model)
- **Output**: Initial ROI ZIP files → `{output_dir}/preprocessed/{condition}/*.zip`
- **Notes**: ROIs are created directly from Cellpose segmentation masks

#### **Stage 4: Process Single-Cell Data** (Key ROI Processing)
**File**: `/Users/leelab/percell/percell/application/stages/process_single_cell_stage.py`

**Sub-steps**:

1. **ROI Tracking** (if multiple timepoints)
   - Function: `track_rois()` in `image_processing_tasks.py`
   - Matches ROI centroids across timepoints using Hungarian algorithm
   - Calculates matching distances
   - **Location**: Lines 822-877 (matching logic), 880-1005 (track building)

2. **ROI Resizing**
   - Function: `resize_rois()` in `imagej_tasks.py` (lines 132-164)
   - **ImageJ Macro**: `/Users/leelab/percell/percell/macros/resize_rois.ijm`
   - **Purpose**: Scale ROIs from binned images back to original dimensions
   - **Process**:
     - Load binned ROI ZIP files
     - Create mask from each ROI via ImageJ "Create Mask" command
     - Resize mask by binning factor (4x or 2x)
     - Convert back to ROI polygon
     - Save resized ROIs → `{output_dir}/ROIs/{condition}/*.zip`

3. **ROI Duplication for Analysis Channels**
   - Function: `duplicate_rois_for_channels()` in `image_processing_tasks.py` (lines 534-591)
   - Copies ROI ZIP files for each analysis channel
   - Maintains same ROI geometry across channels
   - Output: `{output_dir}/ROIs/{condition}/*_ch00_rois.zip`, `*_ch01_rois.zip`, etc.

4. **Cell Extraction**
   - Function: `extract_cells()` in `imagej_tasks.py` (lines 767-889)
   - **ImageJ Macro**: `/Users/leelab/percell/percell/macros/extract_cells.ijm`
   - **Purpose**: Extract individual cell images using ROIs as guides
   - **Process**:
     - Load ROI ZIP
     - Open raw image
     - For each ROI: duplicate image, apply ROI, run "Clear Outside", save as CELL{N}.tif
   - Output: `{output_dir}/cells/{condition}/{region}_{channel}_{timepoint}/CELL1.tif`, `CELL2.tif`, etc.

5. **Cell Grouping**
   - Function: `group_cells()` in `image_processing_tasks.py` (lines 370-531)
   - Organizes extracted cells into spatial bins for visualization
   - Creates directory structure for grouped cells
   - No cell filtering/exclusion—all cells are included

#### **Stage 5: Threshold Grouped Cells**
- **Input**: Grouped extracted cell images
- **Tool**: ImageJ interactive thresholding
- **Output**: Binary masks for each cell → `{output_dir}/grouped_masks/`
- **Note**: Manual user interaction; user adjusts thresholds per condition

#### **Stage 6: Measure ROI Area**
**File**: `/Users/leelab/percell/percell/application/stages/measure_roi_area_stage.py`

- Function: `measure_roi_areas()` in `imagej_tasks.py` (lines 284-338)
- **ImageJ Macro**: `/Users/leelab/percell/percell/macros/measure_roi_area.ijm`
- **Purpose**: Measure area of each ROI
- **Process**:
  - Load ROI ZIP file
  - Open corresponding raw image
  - Measure statistics for each ROI using ImageJ "getStatistics()"
  - Output: CSV with Area, Label, Cell_ID per ROI
- Output: `{output_dir}/analysis/*_cell_area.csv`
- **KEY INSIGHT**: Area measurements are calculated per ROI but NOT filtered by location—all ROIs measured regardless of proximity to image edges

#### **Stage 7: Analysis**
**File**: `/Users/leelab/percell/percell/application/stages/analysis_stage.py`

**Sub-steps**:

1. **Combine Masks** - Merge grouped masks by condition
2. **Create Cell Masks** - Apply ROIs to combined masks
   - **ImageJ Macro**: `/Users/leelab/percell/percell/macros/create_cell_masks.ijm`
3. **Analyze Cell Masks** - Run "Analyze Particles" in ImageJ
   - **ImageJ Macro**: `/Users/leelab/percell/percell/macros/analyze_cell_masks.ijm`
   - Output: Particle analysis CSV with size, shape metrics
4. **Include Group Metadata** - Merge group classification with analysis results

---

## 3. ImageJ Integration

### 3.1 Macro System Overview

**Location**: `/Users/leelab/percell/percell/macros/`

All macros follow a consistent pattern:

```
1. Load template macro file
2. Extract #@ parameter annotations
3. Embed parameter values directly
4. Write temporary macro file
5. Execute via ImageJ subprocess
6. Delete temporary file
```

**Helper Functions**: `percell/application/imagej_tasks.py`
- `run_imagej_macro()` - Execute macro with subprocess
- `create_*_macro_with_parameters()` - Embed parameters in temporary macros
- `find_*_files()` - Discover input files for processing

### 3.2 ROI-Related Macros

| Macro | Purpose | ROI Operation | Key Code |
|-------|---------|---------------|----------|
| `resize_rois.ijm` | Scale ROIs from binned to original dimensions | `roiManager("open")` → mask resize → `roiManager("Add")` | Lines 140-189 |
| `measure_roi_area.ijm` | Measure area of each ROI | `roiManager("Select", i)` → `getStatistics(area, ...)` | Lines 49-107 |
| `extract_cells.ijm` | Extract cell patches using ROIs | `roiManager("select", i)` → "Clear Outside" | Lines 61-83 |
| `create_cell_masks.ijm` | Create binary masks for each ROI | `roiManager("select", i)` → "Clear Outside" | Lines 61-83 |
| `create_cell_masks.ijm` | Create binary masks for each ROI | `roiManager("select", i)` → "Clear Outside" | Lines 61-83 |

### 3.3 Critical ImageJ Operations for ROI Handling

**"Clear Outside"** (Used in `extract_cells.ijm` & `create_cell_masks.ijm`):
- Sets all pixels outside the ROI to 0 (background)
- Does NOT exclude cells—just masks them to the ROI boundary
- All cells are extracted, even those touching image edges

**"Create Mask"** (Used in `resize_rois.ijm`):
- Converts ROI polygon to binary raster mask
- Used as intermediate step for scaling

---

## 4. Existing Cell Filtering/Exclusion Logic

**CURRENT STATUS**: NO EDGE EXCLUSION LOGIC EXISTS

Search results:
- No `edge`, `boundary`, or `exclude` keywords in Python codebase except in model definitions
- ImageJ macros contain `"Clear Outside"` but this is ROI masking, not cell exclusion
- No size-based filtering in ROI measurement or analysis stages

### 4.1 Where Filtering Could Occur (But Doesn't)

#### **Stage: Measure ROI Area** (BEST CANDIDATE)
**File**: `/Users/leelab/percell/percell/application/stages/measure_roi_area_stage.py`

Current flow:
```python
# Get all ROI-image pairs
pairs = find_roi_image_pairs(input_dir, output_dir, channels=channels)

# Measure each ROI without filtering
for roi_zip, img_path, csv_path in pairs:
    # Create macro
    macro_file = create_measure_macro_with_parameters(...)
    # Run macro (ALL ROIs measured)
    run_imagej_macro(...)
```

**Integration Point**: After `measure_roi_areas()` returns, before saving CSV

#### **Stage: Analyze Cell Masks** (SECONDARY CANDIDATE)
**File**: `/Users/leelab/percell/percell/application/stages/analysis_stage.py`

Current flow:
```python
ok_analyze = _analyze_masks(
    input_dir=f"{output_dir}/masks",
    output_dir=f"{output_dir}/analysis",
    ...
)
```

**Integration Point**: Post-analysis CSV filtering before returning results

#### **Python-Level Filtering Options**:
1. **After `measure_roi_areas()`** - Filter CSV results by ROI properties
2. **After `analyze_masks()`** - Filter particle analysis results by position/size
3. **In `find_roi_image_pairs()`** - Pre-filter ROI files before processing

#### **ImageJ-Level Filtering Options**:
1. Modify `measure_roi_area.ijm` to:
   - Calculate ROI boundaries (using Roi.getBounds() or equivalent)
   - Compare to image dimensions
   - Flag or skip edge ROIs
   - Only output non-edge ROIs to CSV

2. Modify `analyze_cell_masks.ijm` to:
   - Add size/position filtering to "Analyze Particles" parameters

---

## 5. Architecture for Edge Exclusion Implementation

### 5.1 Where Edge Exclusion Fits

**RECOMMENDED LOCATION**: Stage 6 (Measure ROI Area) - Post-measurement filtering

**Reasoning**:
- ROI measurement is the logical point to evaluate ROI properties
- Measurements already calculated (area, position can be derived)
- Filtering before downstream analysis stages reduces unnecessary processing
- Results already in CSV format—easy to filter

### 5.2 Key Data Flow Points

```
Segmentation (Stage 3)
    ↓
    Creates: ROI ZIP files with polygon coordinates
    ↓
Resize ROIs (Stage 4.2)
    ↓
    Creates: Scaled ROI ZIP files
    ↓
Measure ROI Area (Stage 6) ← EDGE EXCLUSION FILTER HERE
    ├─ Current: Measures ALL ROIs
    └─ Proposed: Filter by edge proximity during measurement
    ↓
Extract Cells / Analyze Masks (Stages 4.4 & 7)
    ↓
    Processes: Only non-edge ROIs (after filtering)
```

### 5.3 Required Information for Edge Detection

From `ROI` model and ImageJ data:

**ROI Polygon Coordinates**:
- Accessible via `roiManager("getBounds")` in ImageJ
- Or `polygon[i][0]`, `polygon[i][1]` from loaded ROI dict
- Need bounding box: min_x, max_x, min_y, max_y

**Image Dimensions**:
- From image file metadata or ImageJ `getWidth()`, `getHeight()`
- Can be extracted by opening image

**Edge Proximity Calculation**:
```python
def is_roi_at_edge(roi_bounds, image_width, image_height, margin_pixels=5):
    min_x, max_x, min_y, max_y = roi_bounds
    return (min_x <= margin_pixels or 
            max_x >= image_width - margin_pixels or
            min_y <= margin_pixels or
            max_y >= image_height - margin_pixels)
```

### 5.4 Integration Points in Current Code

**Python Level** - `percell/application/imagej_tasks.py`:
```python
def measure_roi_areas(
    input_dir: str | Path,
    output_dir: str | Path,
    ...
    exclude_edge_rois: bool = False,  # NEW PARAMETER
    edge_margin_pixels: int = 5,      # NEW PARAMETER
    ...
) -> bool:
    pairs = find_roi_image_pairs(input_dir, output_dir, channels=channels)
    
    for roi_zip, img_path, csv_path in pairs:
        # Existing measurement code
        ...
        
        # NEW: Filter edge ROIs from results before saving
        if exclude_edge_rois:
            results_df = pd.read_csv(csv_path)
            results_df = _filter_edge_rois(
                results_df, 
                img_path, 
                edge_margin_pixels
            )
            results_df.to_csv(csv_path, index=False)
```

**ImageJ Level** - `percell/macros/measure_roi_area.ijm`:
```javascript
// After measuring each ROI, check if at edge
roiManager("Select", i);
roi_bounds = Roi.getBounds();  // [x, y, width, height]
width = getWidth();
height = getHeight();

is_edge = (roi_bounds[0] <= margin || 
           roi_bounds[0] + roi_bounds[2] >= width - margin ||
           roi_bounds[1] <= margin ||
           roi_bounds[1] + roi_bounds[3] >= height - margin);

// Only add to results if not at edge
if (!is_edge) {
    setResult("Label", result_index, roi_name);
    ...
}
```

---

## 6. Summary Table: ROI Lifecycle

| Stage | Operation | File/Macro | ROI Input | ROI Output | Filtering |
|-------|-----------|-----------|-----------|-----------|-----------|
| Segmentation (3) | Cellpose detection | cellpose_integration_port.py | Images | ROI ZIPs (preprocessed) | None |
| Process Single-Cell (4.1) | Tracking | image_processing_tasks.py | ROI ZIPs | Tracked ROI ZIPs | None |
| Process Single-Cell (4.2) | Resizing | resize_rois.ijm | Binned ROI ZIPs | Full-res ROI ZIPs | None |
| Process Single-Cell (4.3) | Duplication | duplicate_rois_for_channels() | ROI ZIPs | Channel-duplicated ROI ZIPs | None |
| Process Single-Cell (4.4) | Extraction | extract_cells.ijm | ROI ZIPs + Images | CELL*.tif patches | None |
| Process Single-Cell (4.5) | Grouping | group_cells() | CELL*.tif | Grouped directories | None |
| Measure ROI Area (6) | Measurement | measure_roi_area.ijm | ROI ZIPs + Images | *_cell_area.csv | **← Edge exclusion recommended here** |
| Analysis (7.1-7.4) | Masking + Analysis | create_cell_masks.ijm, analyze_cell_masks.ijm | ROI ZIPs + Masks | particle_analysis.csv | None |

---

## 7. Key Files Reference

### Core ROI Classes
- `/Users/leelab/percell/percell/domain/models.py` - `ROI` dataclass

### ROI Handling Services
- `/Users/leelab/percell/percell/application/image_processing_tasks.py` - Track, duplicate, group operations
- `/Users/leelab/percell/percell/application/imagej_tasks.py` - ImageJ macro execution & ROI measurement

### Stages Using ROIs
- `/Users/leelab/percell/percell/application/stages/process_single_cell_stage.py` - Main ROI processing pipeline
- `/Users/leelab/percell/percell/application/stages/measure_roi_area_stage.py` - **EDGE EXCLUSION POINT**
- `/Users/leelab/percell/percell/application/stages/analysis_stage.py` - Final analysis with ROIs

### ImageJ Macros
- `resize_rois.ijm` - ROI scaling
- `measure_roi_area.ijm` - **EDGE EXCLUSION POINT**
- `extract_cells.ijm` - Cell extraction
- `create_cell_masks.ijm` - Mask creation
- `analyze_cell_masks.ijm` - Particle analysis

---

## 8. Recommendations for Edge Exclusion Feature

### Short-term (Minimal Changes)
1. Add `--exclude-edge-rois` CLI parameter to data selection stage
2. Pass parameter through to `measure_roi_areas()` function
3. Implement Python-level post-processing filtering in `imagej_tasks.py`
4. Filter CSV results before downstream stages

### Long-term (Full Integration)
1. Add configurable edge margin parameters to domain models
2. Implement edge detection service in domain layer
3. Integrate filtering into ImageJ macros directly
4. Add reporting of excluded ROI counts at each stage
5. Provide visualization of edge ROIs vs. accepted ROIs

### Testing Strategy
- Unit tests: Edge detection logic with various image sizes/ROI positions
- Integration tests: Full pipeline with/without edge exclusion
- Regression tests: Verify non-edge ROI measurements unchanged

---

## Conclusion

Percell's ROI architecture is clean and well-separated:
- **Domain**: ROI dataclass with polygon/mask storage
- **Application**: Orchestration of ROI operations through stages
- **Adapter**: ImageJ macros for segmentation, measurement, extraction

**Edge exclusion can be implemented at Stage 6 (Measure ROI Area)** with minimal changes to existing code. This is the logical point to evaluate ROI properties before downstream processing. The recommended approach combines Python-level CSV filtering with optional ImageJ-level macro modifications for consistency.

