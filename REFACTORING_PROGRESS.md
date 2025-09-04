Percell Refactoring Progress

Phase: Phase 1 - Foundation

Status
- [x] Create refactor branch and initial empty commit
- [x] Create ports-and-adapters directory structure with __init__.py files
- [x] Run tests after commit (pytest green)
- [ ] Extract value objects (experiment.py, processing.py, imaging.py)
- [ ] Define core port interfaces (ImageReaderPort, ImageWriterPort, MacroRunnerPort)
- [ ] Extract ROI tracking domain service
- [ ] Extract cell grouping domain service

Notes
- Created branch `refactor/ports-and-adapters` and initialized the migration.
- Added base directory skeleton for domain, application, ports, adapters, and infrastructure layers.
- All existing tests pass (1 passed).

Next
- Implement value objects per `docs/refactoring/layer_assignments.md`.
- Commit value objects and add unit tests under `tests/domain/value_objects/`.

