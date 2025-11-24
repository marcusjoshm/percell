# Percell ROI Architecture Documentation Index

This documentation provides a comprehensive analysis of how ROIs (Regions of Interest) are handled in Percell and where edge cell exclusion can be integrated.

## Documents Overview

### 1. QUICK_REFERENCE_ROI.txt (START HERE - 6.8 KB)
**Purpose**: One-page visual reference for quick lookup

**Contains**:
- Pipeline stages visualization
- ImageJ macros overview
- Current filtering status assessment
- Recommended edge exclusion point
- Required data for edge detection
- Implementation pseudocode

**Best for**: Getting a quick understanding of the architecture and where to implement edge exclusion.

---

### 2. ARCHITECTURE_ROI_HANDLING.md (COMPREHENSIVE - 17 KB)
**Purpose**: Complete architectural analysis with implementation guidance

**Contains**:
- Executive summary
- ROI representation and storage (Section 1)
- Analysis pipeline structure (Section 2)
- ImageJ integration system (Section 3)
- Current filtering status assessment (Section 4)
- Edge exclusion implementation architecture (Section 5)
- ROI lifecycle summary table (Section 6)
- Key files reference (Section 7)
- Implementation recommendations (Section 8)

**Best for**: Understanding the full system and detailed implementation planning.

**Key Sections**:
- **Section 2.2**: Detailed breakdown of each pipeline stage with code references
- **Section 3.2**: ROI-related macros table showing lines and operations
- **Section 4.1**: Specific points where filtering could be implemented
- **Section 5**: Architecture for edge exclusion with pseudocode
- **Section 8**: Short-term and long-term implementation strategies

---

### 3. FILE_LOCATIONS_ROI.md (CODE REFERENCE - 9.4 KB)
**Purpose**: Exact file locations with line numbers and modification points

**Contains**:
- Domain layer classes and services with file paths
- Application layer orchestration functions with signatures
- Pipeline stage files with code line numbers
- ImageJ macro locations with specific modification points
- ROI storage locations throughout pipeline
- Import statements needed for implementation
- Test file locations
- Step-by-step code change locations

**Best for**: Implementation work - locate exact code and understand what to modify.

**Key Sections**:
- **ImageJ Task Helpers**: measure_roi_areas() location (BEST FILTERING POINT)
- **measure_roi_area.ijm**: Exact line numbers for macro modification
- **Summary Table**: Quick reference for all code change locations
- **Import Statements**: Copy-paste ready imports for implementation

---

## Quick Navigation by Use Case

### "I need to understand how ROIs work in Percell"
1. Read: QUICK_REFERENCE_ROI.txt (overview)
2. Read: ARCHITECTURE_ROI_HANDLING.md Section 1-2 (ROI handling and pipeline)

### "I need to implement edge exclusion"
1. Read: QUICK_REFERENCE_ROI.txt (implementation overview)
2. Read: ARCHITECTURE_ROI_HANDLING.md Section 5 (implementation architecture)
3. Read: FILE_LOCATIONS_ROI.md (exact code locations)
4. Implement: ~60 lines of code in 3 files

### "I need to modify a specific stage or macro"
1. Read: FILE_LOCATIONS_ROI.md (find the file and line numbers)
2. Read: ARCHITECTURE_ROI_HANDLING.md Section 2.2 or 3 (understand the operation)

### "I need to understand the complete pipeline"
1. Read: ARCHITECTURE_ROI_HANDLING.md (complete reference)
2. Reference: FILE_LOCATIONS_ROI.md (for specific implementations)

---

## Key Findings Summary

### Current State
- **ROI Representation**: ImageJ ROI Manager ZIP files in `{output_dir}/ROIs/{condition}/*.zip`
- **Pipeline Structure**: 8 stages from data selection to cleanup
- **Filtering Status**: NO edge exclusion logic exists; all cells processed
- **ImageJ Integration**: 6 ROI-related macros using parameter embedding pattern

### ROI Lifecycle
```
Segmentation (Stage 3)
  ↓ Creates ROI ZIPs
Process Single-Cell (Stage 4)
  ├─ Track ROIs (if multi-timepoint)
  ├─ Resize ROIs (binned → full-res)
  ├─ Duplicate ROIs (per channel)
  ├─ Extract cells
  └─ Group cells
Measure ROI Area (Stage 6) ← RECOMMENDED EDGE FILTERING POINT
  ↓ Measures all ROIs, outputs CSV
Analysis (Stage 7)
  ↓ Creates masks and runs analysis
```

### Recommended Implementation Point
**Stage 6: Measure ROI Area** (`measure_roi_areas()` function)

**Why**:
- ROI measurements already calculated
- CSV format easy to filter
- Filters before downstream stages
- Minimal code changes needed
- Logical point to evaluate ROI properties

**Where**:
- Python: `percell/application/imagej_tasks.py` (lines 284-338)
- ImageJ: `percell/macros/measure_roi_area.ijm` (lines 78-107)
- Stage: `percell/application/stages/measure_roi_area_stage.py` (lines 62-124)

### Implementation Scope
- **Minimal**: ~60 lines of code across 3 files
- **Full**: ~150-200 lines including configuration and testing

---

## Key Code Locations

### Core ROI Classes
- **ROI Model**: `percell/domain/models.py` (lines 128-142)

### Best Filtering Points
1. **Primary**: `percell/application/imagej_tasks.py` → `measure_roi_areas()` (lines 284-338)
2. **Secondary**: `percell/macros/measure_roi_area.ijm` (lines 78-107)
3. **Stage Handler**: `percell/application/stages/measure_roi_area_stage.py` (lines 62-124)

### Support Functions
- **ROI Tracking**: `image_processing_tasks.py` → `track_rois()`
- **ROI Resizing**: `imagej_tasks.py` → `resize_rois()`
- **Cell Extraction**: `imagej_tasks.py` → `extract_cells()`
- **ROI Duplication**: `image_processing_tasks.py` → `duplicate_rois_for_channels()`

---

## Implementation Checklist

### Minimal Edge Exclusion (~60 lines)
- [ ] Understand measure_roi_areas() function
- [ ] Understand measure_roi_area.ijm macro
- [ ] Add exclude_edge_rois parameter
- [ ] Implement ROI bounds checking
- [ ] Test with sample data

### Full Feature (~150-200 lines)
- [ ] All minimal steps above
- [ ] Add EdgeExclusionConfig domain model
- [ ] Create EdgeDetectionService
- [ ] Integrate CLI parameter
- [ ] Add comprehensive tests
- [ ] Update documentation
- [ ] Add visualization support

---

## Documentation Metadata

| Document | Size | Audience | Read Time |
|----------|------|----------|-----------|
| QUICK_REFERENCE_ROI.txt | 6.8 KB | All levels | 10 min |
| ARCHITECTURE_ROI_HANDLING.md | 17 KB | Engineers/Scientists | 30-45 min |
| FILE_LOCATIONS_ROI.md | 9.4 KB | Implementers | 20-30 min |

---

## Related Files in Repository

### Architecture Documentation
- `CLAUDE.md` - Project instructions for Claude
- `README.md` - Main project documentation

### Source Code
- `percell/domain/` - Domain models and services
- `percell/application/` - Application orchestration
- `percell/macros/` - ImageJ macros
- `percell/adapters/` - External integrations
- `percell/ports/` - Hexagonal architecture ports

### Tests
- `tests/unit/` - Unit tests
- `tests/integration/` - Integration tests
- `tests/migration/` - Migration tests

---

## Questions & Answers

### Q: Where are ROIs stored?
A: `{output_dir}/ROIs/{condition}/*.zip` as ImageJ ROI Manager format files
(See FILE_LOCATIONS_ROI.md - ROI Storage Locations section)

### Q: How do I add edge exclusion?
A: Modify `measure_roi_areas()` in `imagej_tasks.py` and `measure_roi_area.ijm`
(See ARCHITECTURE_ROI_HANDLING.md - Section 5.4)

### Q: What's the current filtering status?
A: No filtering exists; ALL detected ROIs are processed
(See QUICK_REFERENCE_ROI.txt - Section 4)

### Q: Which stage should I modify?
A: Stage 6 (Measure ROI Area) is recommended
(See ARCHITECTURE_ROI_HANDLING.md - Section 5.1)

### Q: How many lines of code are needed?
A: Minimal implementation: ~60 lines across 3 files
(See ARCHITECTURE_ROI_HANDLING.md - Section 8)

---

## Document History

Created: November 21, 2025
Repository: /Users/leelab/percell
Branch: new_automation

**Files**:
- ARCHITECTURE_ROI_HANDLING.md (17 KB)
- FILE_LOCATIONS_ROI.md (9.4 KB)
- QUICK_REFERENCE_ROI.txt (6.8 KB)
- ROI_DOCUMENTATION_INDEX.md (this file)

---

## Next Steps

1. **Understanding Phase** (20 min):
   - Read QUICK_REFERENCE_ROI.txt
   - Skim ARCHITECTURE_ROI_HANDLING.md Sections 1-2

2. **Planning Phase** (30 min):
   - Read ARCHITECTURE_ROI_HANDLING.md Section 5 (Implementation)
   - Review FILE_LOCATIONS_ROI.md for code locations

3. **Implementation Phase** (2-4 hours):
   - Modify 3 files: imagej_tasks.py, measure_roi_area.ijm, measure_roi_area_stage.py
   - Follow pseudocode in ARCHITECTURE_ROI_HANDLING.md Section 5.4

4. **Testing Phase** (2-4 hours):
   - Write unit tests for edge detection logic
   - Run full pipeline with/without edge exclusion
   - Verify existing tests still pass

---

**Start with QUICK_REFERENCE_ROI.txt for a quick overview, then dive into detailed docs for implementation.**

