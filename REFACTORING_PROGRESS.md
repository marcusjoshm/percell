Percell Refactoring Progress

Phase: Phase 2 - Adapters

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

Notes
- Created branch `refactor/ports-and-adapters` and initialized the migration.
- Added base directory skeleton for domain, application, ports, adapters, and infrastructure layers.
- All existing tests pass (1 passed).

Next
- Implement PathlibFilesystemAdapter with temp-dir tests (Commit 9).

