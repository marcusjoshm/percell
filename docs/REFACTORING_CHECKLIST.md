## Migration status per docs/ports_adapters_guide.md

### Phase 1: Setup Structure
- [x] Create directory structure: `percell/domain`, `percell/ports`, `percell/adapters`, `percell/infrastructure`
- [x] Set up dependency injection: minimal container `percell/infrastructure/dependencies/container.py`
- [x] Create base port interfaces: `percell/ports/inbound/*`, `percell/ports/outbound/*`

### Phase 2: Extract Domain
Completed
- [x] Identify and extract entities: `percell/domain/entities/{cell,image,metadata,roi,workflow}.py`
- [x] Create value objects: `percell/domain/value_objects/{file_path,dimensions,intensity}.py`
- [x] Domain services: `percell/domain/services/metadata_service.py` (complete and integrated)
- [x] Workflow orchestrator (skeleton): `percell/domain/services/workflow_orchestrator.py`

Remaining
- [ ] Move more business logic from `percell/modules/*` into domain services (beyond orchestrator skeleton)

### Phase 3: Implement Adapters
Completed
- [x] Storage adapter: `percell/adapters/outbound/storage/file_system_adapter.py`
- [x] Cellpose adapter: `percell/adapters/outbound/segmentation/cellpose_adapter.py` (minimal invoke via configured python)
- [x] ImageJ adapter: `percell/adapters/outbound/image_processing/imagej_adapter.py` (macro exec + local ops)
- [x] Metadata adapter: `percell/adapters/outbound/metadata/metadata_adapter.py` (filename parsing + summarizers)

Remaining
- [ ] Improve Cellpose adapter to parse real masks/ROIs from Cellpose outputs (beyond bbox fallback)
- [ ] Harden ImageJ adapter macro interactions (parameter validation, robust error handling)
- [ ] Add adapter-level configuration validation and clearer error messages

### Phase 4: Build Application Layer
Completed
- [x] Implement use case: `percell/application/use_cases/run_complete_workflow.py`
- [x] Wire adapters and orchestrator in DI container
- [x] CLI integration (demo flag): `--ports-adapters-demo` in `percell/core/cli.py`, handled in `percell/main/main.py`

Remaining
- [ ] Create a ports-based CLI adapter separate from legacy CLI
- [ ] Add additional use cases (segmentation-only, analysis-only, etc.) using ports
- [ ] Consider a real DI framework per guide (e.g., `dependency_injector`)

### Phase 5: Testing & Refinement
Completed
- [x] Smoke test: `tests/ports_adapters_smoke.py`
- [x] End‑to‑end DI demo: `examples/ports_adapters_di_demo.py`
- [x] Full workflow run on sample dataset completes successfully

Remaining
- [ ] Unit tests for domain entities/value objects/services
- [ ] Integration tests for each adapter (mock tools + small fixtures)
- [ ] Continuous refinement based on tests (stability, error paths, performance)
- [ ] Optional CI workflow for linting/tests

### Module Refactors to use MetadataService
Completed
- [x] `percell/modules/bin_images.py`
- [x] `percell/modules/analyze_cell_masks.py`
- [x] `percell/modules/create_cell_masks.py`
- [x] `percell/modules/extract_cells.py`
- [x] `percell/modules/duplicate_rois_for_channels.py`
- [x] `percell/modules/combine_masks.py`
- [x] `percell/modules/group_cells.py`
- [x] `percell/modules/track_rois.py`
- [x] `percell/modules/measure_roi_area.py`
- [n/a] `percell/modules/resize_rois.py` (macro invocation only)
- [n/a] `percell/modules/otsu_threshold_grouped_cells.py` (macro invocation only)

Remaining
- [ ] `percell/modules/advanced_workflow.py`
- [ ] `percell/modules/cleanup_directories.py`
- [ ] `percell/modules/directory_setup.py`
- [ ] `percell/modules/include_group_metadata.py`
- [ ] `percell/modules/set_directories.py`

### Optional / Stretch (from guide’s design decisions)
- [ ] Plugin port and adapters (discover/load/register)
- [ ] Inbound adapters beyond CLI (REST/GUI) if desired
- [ ] Performance optimizations and caching strategies where appropriate

Notes:
- MetadataService is complete and is the primary mechanism for file discovery and metadata extraction post‑refactor.
- Items marked n/a are macro‑only steps that do not perform filesystem parsing and thus do not benefit from MetadataService.
