# Percell Architecture Layer Assignment

Based on your inventory, here's a comprehensive breakdown of where each component should be placed in the Ports and Adapters architecture:

## 1. DOMAIN LAYER
*Pure business logic with no external dependencies*

### Domain Services (`percell/domain/services/`)
Extract these pure business logic functions from their current modules:

**From `group_cells.py`:**
- `compute_auc()` - pure AUC calculation
- Clustering logic from `group_and_sum_cells()` - GMM/KMeans binning decisions
- Cell aggregation rules (sum/mean per bin)
- Intensity calculation algorithms

**From `track_rois.py`:**
- `polygon_centroid()` - pure geometry calculation
- `get_roi_center()` - centroid extraction logic
- `match_rois()` - Hungarian algorithm matching logic (without I/O)

**From `combine_masks.py`:**
- Mask merging algorithm (pixel-wise operations)
- Channel combination rules

**From `bin_images.py`:**
- Binning algorithm (downscale calculations)

**From existing stage validation logic:**
- Stage ordering rules
- Input validation rules
- Workflow state transitions

### Domain Entities (`percell/domain/entities/`)
Create new entities to represent:
- `Cell` - id, region, timepoint, channel, intensity values
- `CellGroup` - aggregated cells with statistics
- `ROI` - region of interest with geometry
- `Mask` - segmentation mask with metadata
- `Experiment` - complete experimental setup

### Domain Value Objects (`percell/domain/value_objects/`)
Create immutable value objects from current implicit concepts:

**From `stage_classes.DataSelectionStage`:**
- `ExperimentMetadata` - extracted from `_extract_experiment_metadata()`
- `DataType` (SINGLE_TIMEPOINT, MULTI_TIMEPOINT)
- `Channel` - name, is_segmentation, is_analysis
- `Timepoint` - id, order
- `Region` - id, name
- `Condition` - experimental condition

**From various modules:**
- `BinningParameters` - num_bins, strategy (gmm/kmeans/uniform)
- `SegmentationParameters` - model, diameter, thresholds
- `ImageDimensions` - width, height, channels
- `Resolution` - x, y, units
- `IntensityProfile` - time series of intensities
- `ROIGeometry` - shape, coordinates

## 2. APPLICATION LAYER
*Use cases and orchestration*

### Application Services/Use Cases (`percell/application/use_cases/`)
Transform current stage logic into use cases:

**From `stage_classes.py`:**
- `DataSelectionUseCase` - from `DataSelectionStage.run()` orchestration logic
- `SegmentationUseCase` - from `SegmentationStage.run()` orchestration
- `ProcessSingleCellDataUseCase` - from `ProcessSingleCellDataStage.run()`
- `ThresholdGroupedCellsUseCase` - from `ThresholdGroupedCellsStage.run()`
- `MeasureROIAreaUseCase` - from `MeasureROIAreaStage.run()`
- `AnalysisUseCase` - from `AnalysisStage.run()`
- `CleanupUseCase` - from `CleanupStage.run()`
- `CompleteWorkflowUseCase` - from `CompleteWorkflowStage.run()`

**From `advanced_workflow.py`:**
- `AdvancedWorkflowUseCase` - from `AdvancedWorkflowStage.run()`

**From module main functions:**
- `BinImagesUseCase` - orchestration from `bin_images.main()`
- `CombineMasksUseCase` - orchestration from `combine_masks.main()`
- `GroupCellsUseCase` - orchestration from `group_cells.main()`
- `TrackROIsUseCase` - orchestration from `track_rois.main()`
- `CreateCellMasksUseCase` - orchestration from `create_cell_masks.main()`
- `ExtractCellsUseCase` - orchestration from `extract_cells.main()`
- `AnalyzeCellMasksUseCase` - orchestration from `analyze_cell_masks.main()`

### Command Objects (`percell/application/commands/`)
- Extract command patterns from current args handling in each module's `main()`

## 3. PORTS LAYER
*Interface definitions only*

### Inbound Ports (`percell/ports/inbound/`)
```python
- UserInterfacePort - menu display, user input
- ProgressReporterPort - progress feedback
- ConfigurationPort - config input
```

### Outbound Ports (`percell/ports/outbound/`)

**From current I/O operations:**
```python
- ImageReaderPort - from all tifffile.imread, cv2.imread, skimage.io.imread
- ImageWriterPort - from all tifffile.imwrite, cv2.imwrite, skimage.io.imsave
- MacroRunnerPort - from all ImageJ macro executions
- SegmenterPort - from Cellpose invocations
- ROIRepositoryPort - from read_roi operations
- MetadataStorePort - from CSV/JSON read/write operations
- FilesystemPort - from glob, pathlib, os operations
- ProcessRunnerPort - from subprocess operations
- PathResolverPort - from path resolution logic
```

## 4. ADAPTERS LAYER
*Concrete implementations*

### Inbound Adapters (`percell/adapters/inbound/`)

**CLI Adapters:**
- `CLIAdapter` - from `core/cli.py` (PipelineCLI class)
- `InteractiveMenuAdapter` - from `show_interactive_menu()`, menu methods
- `ArgumentParserAdapter` - from `_create_parser()`, `parse_args()`

**Stage Adapters (thin wrappers):**
- `StageAdapter` - refactored `StageBase` that delegates to use cases
- One adapter per current stage class (but now just wiring)

### Outbound Adapters (`percell/adapters/outbound/`)

**Image I/O Adapters:**
- `TifffileImageAdapter` - implements ImageReaderPort/WriterPort using tifffile
- `OpenCVImageAdapter` - implements ports using cv2
- `SkimageImageAdapter` - implements ports using skimage

**External Tool Adapters:**
- `ImageJMacroAdapter` - from all macro execution code
  - Consolidates: `create_macro_with_parameters()`, `run_imagej_macro()`, `check_macro_file()`
- `CellposeAdapter` - from Cellpose invocation in SegmentationStage
- `FijiAdapter` - from Fiji-specific operations

**Data Storage Adapters:**
- `PandasCSVAdapter` - from pandas operations in `analyze_cell_masks.py`, `include_group_metadata.py`
- `NumpyAdapter` - from numpy I/O operations
- `JSONConfigAdapter` - from `config.py` load/save operations
- `ZipROIAdapter` - from `track_rois.py` zip operations

**Filesystem Adapters:**
- `PathlibFilesystemAdapter` - from all Path/glob operations
- `ShutilAdapter` - from shutil operations

**Process Adapters:**
- `SubprocessAdapter` - from all subprocess calls
- `ProgressAdapter` - from `core/progress.py` implementations

## 5. INFRASTRUCTURE LAYER
*Framework, utilities, and bootstrap*

### Configuration (`percell/infrastructure/config/`)
**From `core/config.py`:**
- `Config` class (keep as infrastructure)
- `create_default_config()`
- `validate_software_paths()`
- `detect_software_paths()`

### Logging (`percell/infrastructure/logging/`)
**From `core/logger.py`:**
- `PipelineLogger` class
- `ModuleLogger` class
- `create_logger()`

### Path Management (`percell/infrastructure/paths/`)
**From `core/paths.py`:**
- `PathConfig` class
- Path initialization and discovery logic
- But create `PathResolverPort` interface

### Progress (`percell/infrastructure/progress/`)
**From `core/progress.py`:**
- Keep as infrastructure utilities
- `alive_progress` integration

### Bootstrap (`percell/infrastructure/bootstrap/`)
**New components:**
- Dependency injection container
- Application initialization
- Module wiring

### Utilities (`percell/infrastructure/utils/`)
**From `core/utils.py`:**
- `get_package_root()`
- `get_package_resource()`
- `ensure_executable()`
- Other utility functions

**From `core/pipeline.py` and `core/stages.py`:**
- `Pipeline` class → becomes thin orchestrator using use cases
- `StageRegistry` → infrastructure for wiring
- `StageExecutor` → delegates to use cases

## 6. MODULES TO COMPLETELY RESTRUCTURE

These modules will be split across multiple layers:

### `stage_classes.py` → Split into:
- **Domain**: Validation rules, business logic
- **Application**: Use cases for each stage
- **Adapters**: Thin stage adapters for CLI compatibility

### `group_cells.py` → Split into:
- **Domain**: `compute_auc()`, clustering algorithms, aggregation logic
- **Application**: `GroupCellsUseCase`
- **Adapters**: Image I/O, CSV writing

### `track_rois.py` → Split into:
- **Domain**: ROI matching algorithm
- **Application**: `TrackROIsUseCase`
- **Adapters**: ZIP file I/O

### `analyze_cell_masks.py` → Split into:
- **Domain**: Analysis algorithms
- **Application**: `AnalyzeMasksUseCase`
- **Adapters**: ImageJ macro, pandas CSV operations

## 7. MODULES TO KEEP AS UTILITIES OR REMOVE

### Keep in Infrastructure:
- `setup/install.py` - installation utility
- `directory_setup.py`, `set_directories.py` - configuration utilities
- `cleanup_directories.py` - cleanup utility

### Keep Separate (not part of core refactoring):
- `image_metadata/*.py` - auxiliary tools, can be refactored later

### Testing:
- `tests/*` - rewrite for new architecture

## 8. IMPORT DEPENDENCIES TO BREAK

### Remove from Domain:
- ❌ All `subprocess` imports
- ❌ All `pathlib`, `os`, `glob` imports
- ❌ All `cv2`, `tifffile`, `skimage` imports
- ❌ All `pandas`, `csv` imports
- ❌ All file I/O operations

### Domain should only import:
- ✅ `numpy` (for calculations)
- ✅ `scipy` (for algorithms)
- ✅ `sklearn` (for ML algorithms)
- ✅ Standard library for calculations (math, etc.)
- ✅ Type hints from `typing`

## 9. FUNCTION MIGRATIONS

### Functions that become Domain Services:

**Cell Grouping Service:**
- `compute_auc()` from `group_cells.py`
- `group_and_sum_cells()` logic (pure parts)
- `resize_image_to_target()` algorithm

**ROI Tracking Service:**
- `polygon_centroid()` from `track_rois.py`
- `get_roi_center()` from `track_rois.py`
- `match_rois()` algorithm from `track_rois.py`

**Mask Combination Service:**
- Core merging logic from `combine_masks()`

**Image Processing Service:**
- `bin_image()` algorithm from `bin_images.py`

### Functions that become Port Methods:

**ImageReaderPort:**
- `read_image()` from `group_cells.py`
- `read_image_with_metadata()` from `combine_masks.py`

**MacroRunnerPort:**
- `run_imagej_macro()` from multiple modules
- `create_macro_with_parameters()` from multiple modules

**MetadataStorePort:**
- CSV operations from `analyze_cell_masks.py`
- `merge_metadata_with_analysis()` from `include_group_metadata.py`

## Summary of Major Moves:

1. **Pure algorithms** → Domain Services
2. **Orchestration logic** → Application Use Cases
3. **I/O operations** → Port interfaces + Adapter implementations
4. **Framework/utility code** → Infrastructure
5. **External tool calls** → Adapters
6. **Business rules/validation** → Domain layer
7. **User interaction** → Inbound adapters
8. **Configuration/logging** → Infrastructure

This separation ensures that your domain logic is completely isolated from external dependencies, making it testable, maintainable, and adaptable to future changes.