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
- [ ] core/utils.py → domain/services
- [ ] core/paths.py → file_naming_service

### Phase 2: Domain Logic
- [x] modules/measure_roi_area.py → analysis_aggregation_service (implemented earlier)
- [x] modules/resize_rois.py → segmentation_strategy_service (implemented earlier)
- [x] modules/group_cells.py → intensity_analysis_service (implemented earlier)

### Phase 3: Integration Logic
- [x] modules/bin_images.py → pil_image_processing_adapter (wired)
- [x] modules/create_cell_masks.py → imagej_macro_adapter (wired)
- [x] modules/extract_cells.py → cellpose_subprocess_adapter (wired)
- [x] modules/combine_masks.py → pil_image_processing_adapter (wired)

### Phase 4: Orchestration
- [x] modules/stage_classes.py → step_execution_coordinator (implemented)
- [x] core/pipeline.py → workflow_coordinator (implemented)
- [ ] core/cli.py → user_interface_port (pending)

## Cleanup
- [ ] Remove old wrappers
- [ ] Delete obsolete files after verification
- [ ] Update docs and examples


