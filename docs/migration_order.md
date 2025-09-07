## Migration Order (from docs/migration_guide.md)

### Phase 1: Pure Utilities (No dependencies)
1. core/utils.py → domain/services
2. core/paths.py → domain/services/file_naming_service.py

### Phase 2: Domain Logic (Minimal dependencies)
3. modules/measure_roi_area.py → domain/services/analysis_aggregation_service.py
4. modules/resize_rois.py → domain/services/segmentation_strategy_service.py
5. modules/group_cells.py → domain/services/intensity_analysis_service.py

### Phase 3: Integration Logic (External dependencies)
6. modules/bin_images.py → adapters/pil_image_processing_adapter.py
7. modules/create_cell_masks.py → adapters/imagej_macro_adapter.py
8. modules/extract_cells.py → adapters/cellpose_subprocess_adapter.py

### Phase 4: Orchestration (Depends on everything)
9. modules/stage_classes.py → application/step_execution_coordinator.py
10. core/pipeline.py → application/workflow_coordinator.py
11. core/cli.py → ports/driving/user_interface_port.py


