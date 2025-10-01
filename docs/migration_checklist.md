# Code Migration Checklist

## Validation Checklist Per File
- [ ] Business logic moved to domain service
- [ ] I/O moved to adapters
- [ ] External tools moved to adapters
- [ ] Type hints added
- [ ] Docstrings indicate source
- [ ] No circular deps
- [ ] Domain has no framework deps
- [ ] Original tests pass
- [ ] New unit tests for services
- [ ] Backward-compat wrapper created (if needed)
- [ ] No duplicated logic

## File Status

### Phase 1: Utilities
- [x] core/utils.py → domain/services (migrated/removed)
- [x] core/paths.py → file_naming_service (migrated/removed)

### Phase 2: Domain Logic
- [x] modules/measure_roi_area.py → analysis_aggregation_service
- [x] modules/resize_rois.py → segmentation_strategy_service
- [x] modules/group_cells.py → intensity_analysis_service

### Phase 3: Integration Logic
- [x] modules/bin_images.py → pil_image_processing_adapter
- [x] modules/create_cell_masks.py → imagej_macro_adapter
- [x] modules/extract_cells.py → cellpose_subprocess_adapter
- [x] modules/combine_masks.py → pil_image_processing_adapter

### Phase 4: Orchestration
- [x] modules/stage_classes.py → individual stage files in application/stages/
- [x] core/pipeline.py → application/pipeline_api.py
- [x] core/cli.py → main/main.py + application/menu/menu_system.py

## Recent Improvements (2025-10-01)
- [x] Fixed progress reporting architecture (proper port/adapter pattern)
- [x] Migrated Config to ConfigurationService in domain layer
- [x] Split stage_classes.py into individual stage files
- [x] Extracted business logic to domain services
- [x] Fixed group_cells lambda progress fallback bug

## Remaining Tasks
- [ ] Review and remove any remaining old wrapper code
- [ ] Verify all old module files are deleted
- [ ] Update user-facing documentation
- [ ] Consider adding integration tests for full workflows


