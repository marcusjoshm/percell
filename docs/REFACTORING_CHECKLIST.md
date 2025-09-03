# Ports & Adapters Refactoring Checklist

Track migration progress for the ports_adapters_refactor branch.

## Core Architecture
- [x] Define outbound ports (percell/ports/outbound/*)
- [x] Dependency Injection container (percell/infrastructure/dependencies/container.py)
- [x] Domain MetadataService (percell/domain/services/metadata_service.py)
- [x] Domain WorkflowOrchestrator (skeleton) (percell/domain/services/workflow_orchestrator.py)

## Outbound Adapters
- [x] ImageJ adapter (percell/adapters/outbound/image_processing/imagej_adapter.py)
- [x] Cellpose adapter (percell/adapters/outbound/segmentation/cellpose_adapter.py)
- [x] Metadata adapter (percell/adapters/outbound/metadata/metadata_adapter.py)
- [x] Storage adapter (existing) (percell/adapters/outbound/storage/file_system_adapter.py)

## Application / Use Cases
- [x] RunCompleteWorkflow use case (percell/application/use_cases/run_complete_workflow.py)

## CLI / Entry
- [x] Add CLI flag for demo (--ports-adapters-demo)
- [x] Wire demo into percell/main/main.py

## Modules Refactored to Use MetadataService
- [x] percell/modules/bin_images.py
- [x] percell/modules/analyze_cell_masks.py
- [x] percell/modules/create_cell_masks.py
- [x] percell/modules/extract_cells.py
- [x] percell/modules/duplicate_rois_for_channels.py
- [x] percell/modules/combine_masks.py
- [x] percell/modules/group_cells.py
- [x] percell/modules/track_rois.py
- [x] percell/modules/measure_roi_area.py
- [n/a] percell/modules/resize_rois.py (macro invocation only)
- [n/a] percell/modules/otsu_threshold_grouped_cells.py (macro invocation only)

## Tests / Demos
- [x] Smoke test: tests/ports_adapters_smoke.py
- [x] End-to-end DI demo: examples/ports_adapters_di_demo.py

## End-to-end Validation
- [x] Complete workflow run succeeds on sample dataset

Notes:
- Items marked n/a are macro-only steps that do not perform filesystem parsing and thus do not benefit from MetadataService.
