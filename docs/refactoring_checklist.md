# Hexagonal Refactoring Checklist

A consolidated, actionable checklist derived from the Revised Hexagonal Architecture Plan.

## Next Up
- [ ] Phase 2.4: Replace file I/O with File System Adapter (wiring)

---

## Phase 1: Extract Core Business Logic

### 1.1 Create Domain Services Structure — Completed
- [x] Create domain directories `percell/domain` and `percell/domain/services`
- [x] Add `__init__.py` files for domain and services
- [x] Add `percell/domain/models.py` with dataclasses and enums
- [x] Add six service skeletons under `percell/domain/services`
- [x] Configure `black`/`isort`/`ruff` in `pyproject.toml`

### 1.2 Extract File Naming Logic
- [x] Identify all file naming logic across the codebase
- [x] Write unit tests for `FileNamingService`
- [x] Implement `FileNamingService` methods
- [x] Refactor codebase to use `FileNamingService`

### 1.3 Extract Data Selection Logic
- [x] Extract selection algorithms into `DataSelectionService`
- [x] Write unit tests for `DataSelectionService`
- [x] Update CLI to use `DataSelectionService`

### 1.4 Extract Intensity Analysis Logic
- [x] Extract algorithms into `IntensityAnalysisService`
- [x] Write unit tests for `IntensityAnalysisService`
- [x] Update analysis modules to use `IntensityAnalysisService`

### 1.5 Extract Workflow Orchestration
- [x] Extract orchestration into `WorkflowOrchestrationService`
- [x] Write unit tests for `WorkflowOrchestrationService`
- [x] Update workflow execution to use orchestration service

---

## Phase 2: Create Ports and Adapters

### 2.1 Define Port Interfaces
- [x] Define driving port interfaces
- [x] Define driven port interfaces

### 2.2 Implement ImageJ Adapter
- [x] Implement `ImageJMacroAdapter` and tests
- [x] Replace direct ImageJ calls with adapter (modules updated: `analyze_cell_masks`, `create_cell_masks`, `extract_cells`, `measure_roi_area`, `resize_rois`)

### 2.3 Implement Cellpose Adapter
- [x] Implement `CellposeSubprocessAdapter` and tests
- [x] Update segmentation to use Cellpose adapter (GUI launch wired)

### 2.4 Implement File System Adapter
- [x] Implement `LocalFileSystemAdapter` and tests
- [ ] Replace file I/O with adapter (partial: `create_cell_masks`, `analyze_cell_masks`, `resize_rois`, `measure_roi_area`, `extract_cells`, `combine_masks`, `otsu_threshold_grouped_cells`)

### 2.5 Implement Image Processing Adapter
- [ ] Implement `PILImageProcessingAdapter` and tests
- [ ] Update code to use image processing adapter

---

## Phase 3: Application Layer Integration

### 3.1 Create Application Services
- [ ] Create `WorkflowCoordinator`
- [ ] Create `StepExecutionCoordinator`
- [ ] Add `ConfigurationManager`

### 3.2 Wire Everything Together
- [ ] Add dependency injection container
- [ ] Create application bootstrap and wire adapters
- [ ] Update main entry point with DI

### 3.3 Integration Testing
- [ ] Add end-to-end workflow tests
- [ ] Add custom workflow integration tests
- [ ] Add performance benchmarks

---

## Documentation
- [ ] Phase 1: Domain/business-logic docs and README updates
- [ ] Phase 2: Ports/adapters and external integrations docs
- [ ] Phase 3: Application layer, testing strategy, and README updates

---

## Quality Gates (Ongoing)
- [ ] Maintain feature parity and UX
- [ ] Preserve performance characteristics
- [ ] Achieve target test coverage thresholds
- [ ] Run regression and acceptance tests after each phase
