Percell Refactoring Progress

Phase: Phase 5 - Testing and Migration

Status
- [x] Create refactor branch and initial empty commit
- [x] Create ports-and-adapters directory structure with __init__.py files
- [x] Run tests after commit (pytest green)
- [x] Extract value objects (experiment.py, processing.py, imaging.py)
- [x] Define core port interfaces (ImageReaderPort, ImageWriterPort, MacroRunnerPort)
- [x] Extract ROI tracking domain service
- [x] Extract cell grouping domain service
- [x] Implement TifffileImageAdapter (read/write + metadata) with tests
- [x] Implement ImageJMacroAdapter with mocked subprocess tests
- [x] Implement PandasMetadataAdapter and tests
- [x] Implement PathlibFilesystemAdapter with temp-dir tests
- [x] Add adapter factory for DI selection
- [x] Implement GroupCellsUseCase
- [x] Implement TrackROIsUseCase
- [x] Implement SegmentationUseCase
- [x] Update stage classes to use application services (grouping)
- [x] Add command objects for GroupCells, TrackROIs, SegmentCells
- [x] Add DI container wiring adapters, services, and use cases
- [x] Integrate DI container with main application
- [x] Migrate configuration to infrastructure (JSON configuration adapter)
- [x] Add comprehensive domain tests
- [x] Add application use case tests (GroupCells, TrackROIs, Segmentation)

Notes
- Branch `refactor/ports-and-adapters` active for migration tasks.
- New architecture layers created and progressively integrated.
- All tests green (47 passed).

Next
- Add integration tests (Commit 21).

