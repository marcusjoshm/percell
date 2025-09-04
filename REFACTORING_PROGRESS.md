Percell Refactoring Progress

Phase: Phase 1 - Foundation

Status
- [x] Create refactor branch and initial empty commit
- [x] Create ports-and-adapters directory structure with __init__.py files
- [x] Run tests after commit (pytest green)
- [x] Extract value objects (experiment.py, processing.py, imaging.py)
- [x] Define core port interfaces (ImageReaderPort, ImageWriterPort, MacroRunnerPort)
- [x] Extract ROI tracking domain service
- [ ] Extract cell grouping domain service
 - [x] Extract cell grouping domain service

Notes
- Created branch `refactor/ports-and-adapters` and initialized the migration.
- Added base directory skeleton for domain, application, ports, adapters, and infrastructure layers.
- All existing tests pass (1 passed).

Next
- Extract ROI tracking domain service and add pure unit tests.

