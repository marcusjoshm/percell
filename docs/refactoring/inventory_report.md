I'll scan the codebase to inventory Python modules, extract classes, functions, and imports, and detect I/O and external dependencies. Running multiple searches in parallel for speed.
Ran tool
Ran tool
Ran tool
Ran tool
Ran tool
Ran tool
Ran tool

I'll broaden the scan to capture internal imports, external tool usage, and key core modules' contents for accurate responsibilities and coupling.
Ran tool
Ran tool
Ran tool
Ran tool
Ran tool
Ran tool
Ran tool
Ran tool
Ran tool

I'll open a few core and orchestration modules to extract accurate responsibilities and key functions/methods, while relying on earlier scans for the rest.
Ran tool
Ran tool
Ran tool
Ran tool
Ran tool
Ran tool
Ran tool

I finished scanning modules, classes, functions, imports, and I/O/dependency usage across the repo. I’ll present the full ports-and-adapters oriented analysis below.

## 1. MODULE INVENTORY

### percell/core
- `percell/core/__init__.py`
  - Purpose: Facade re-export of core APIs (CLI, Config, Logger, Pipeline, Stages, Utils, Paths, Progress).
  - Classes: none.
  - Functions: none (exports only).
  - External deps: none direct.
  - Internal imports: `.cli`, `.config`, `.logger`, `.pipeline`, `.stages`, `.utils`, `.paths`, `.progress`.
  - Responsibility: API surface aggregation.

- `percell/core/config.py`
  - Purpose: Configuration load/save/validate and defaults.
  - Classes:
    - `ConfigError`: error type.
    - `Config`: load(), save(), get(), set(), validate(), to_dict(), update(), get_software_paths(), get_analysis_settings(), get_output_settings().
  - Functions: `create_default_config()`, `validate_software_paths()`, `detect_software_paths()`.
  - External deps: `json`, `os`, `logging`, `subprocess` (for detection).
  - Internal imports: none.
  - Responsibility: Configuration management. I/O: reads/writes JSON config; runs subprocess to detect Cellpose.

- `percell/core/logger.py`
  - Purpose: Structured pipeline and module logging + execution summary.
  - Classes:
    - `PipelineLogger`: manages handlers, writes logs, tracks execution stats; `save_execution_summary()`.
    - `ModuleLogger`: per-stage scoped logging helpers.
  - Functions: `create_logger()`.
  - External deps: `logging`, `sys`, `os`, `json`, `datetime`.
  - Internal imports: none.
  - Responsibility: Logging infra. I/O: writes log files and JSON summary.

- `percell/core/paths.py`
  - Purpose: Centralized path registry and helpers (package-root discovery).
  - Classes: `PathConfig` with `_find_package_root()`, `_initialize_paths()`, `get_path()`, `get_path_str()`, `exists()`, `ensure_executable()`, `list_paths()`, `get_package_root()`.
  - Functions: `get_path_config()`, `get_path()`, `get_path_str()`, `path_exists()`, `ensure_executable()`, `list_all_paths()`.
  - External deps: `os`, `sys`, `pathlib`.
  - Internal imports: none.
  - Responsibility: Path configuration; sets canonical paths to modules, macros, scripts. I/O: chmod only.

- `percell/core/stages.py`
  - Purpose: Stage base classes, registry, and executor.
  - Classes:
    - `StageError`.
    - `StageBase`: lifecycle: `execute()`, abstract `run()` and `validate_inputs()`, plus `setup()`, `cleanup()`, timing.
    - `FileProcessingStage`: per-file processing harness `_process_file_impl()`, tracking success/failure.
    - `StageRegistry`: register/get stages and order.
    - `StageExecutor`: executes one or many stages, reloads `Config` before stage execution; collects summary.
  - Functions: `register_stage()` decorator, `get_stage_registry()`.
  - External deps: `time`, `abc`, `typing`, `pathlib`.
  - Internal imports: `.config`, `.logger`.
  - Responsibility: Application orchestration scaffolding.

- `percell/core/pipeline.py`
  - Purpose: Top-level orchestrator turning CLI args into ordered stage execution.
  - Classes: `Pipeline`: `setup_directories()`, `_determine_stages()`, `get_pipeline_arguments()`, `run()`, `get_available_stages()`, `get_stage_order()`.
  - Functions: `create_pipeline()`.
  - External deps: `os`, `time`, `argparse`, `pathlib`.
  - Internal imports: `.config`, `.logger`, `.stages`.
  - Responsibility: Application orchestration. I/O: creates output directories, saves summary via logger.

- `percell/core/cli.py`
  - Purpose: CLI definition, validation, and interactive menu.
  - Classes:
    - `Colors` (ANSI constants),
    - `CLIError`,
    - `PipelineCLI`: `_create_parser()`, `parse_args()`, `_validate_args()`, `show_interactive_menu()`, `_get_directory_input()`, `_setup_output_structure()`.
  - Functions: `colorize()`, `show_header()`, `parse_arguments()`, `create_cli()`.
  - External deps: `argparse`, `sys`, `os`, `subprocess` within helper, `pathlib`.
  - Internal imports: `..modules.directory_setup`, `..modules.set_directories`, `..core.paths`.
  - Responsibility: UI/interaction (menus), argument parsing; limited infra actions (run shell script for structure). I/O: runs shell script; prompts.

- `percell/core/utils.py`
  - Purpose: Package resource resolution and executable helpers.
  - Classes: none.
  - Functions: `get_package_root()`, `get_package_resource()`, `get_bash_script()`, `get_config_file()`, `get_macro_file()`, `ensure_executable()`, `find_package_root_from_script()`.
  - External deps: `os`, `sys`, `pathlib`.
  - Internal imports: none.
  - Responsibility: Infra helpers. I/O: chmod.

- `percell/core/progress.py`
  - Purpose: Decouple progress indicators and subprocess execution from `alive-progress`.
  - Classes: none.
  - Functions: `is_progress_available()`, `configure_global()`, `progress_bar()`, `iter_with_progress()`, `spinner()`, `run_subprocess_with_spinner()`.
  - External deps: `alive_progress`, `subprocess`, `time`, `typing`, `contextlib`.
  - Internal imports: none.
  - Responsibility: UI feedback and subprocess wrapper. I/O: launches subprocesses.

### percell/main
- `percell/main/main.py`
  - Purpose: Application entrypoint; menu loop; pipeline lifecycle.
  - Classes: none.
  - Functions: `main()`.
  - External deps: `argparse`, `sys`, `os`, `pathlib`, `time`, `traceback`.
  - Internal imports: `percell.core` modules, `percell.modules.stage_registry`, `percell.modules.directory_setup`, `percell.core.paths`.
  - Responsibility: Program loop + orchestration. I/O: creates default config if missing; persists recent dirs.

### percell/modules (processing and orchestration)
- `percell/modules/stage_registry.py`
  - Purpose: Register all stages to `StageRegistry`.
  - Classes: none.
  - Functions: `register_all_stages()`.
  - External deps: none.
  - Internal imports: `..core.stages.register_stage`, `..modules.stage_classes`, optionally `.advanced_workflow`.
  - Responsibility: Application wiring.

- `percell/modules/stage_classes.py`
  - Purpose: Concrete stage implementations for the pipeline.
  - Classes:
    - `DataSelectionStage(StageBase)`: methods `validate_inputs()`, `run()`, `_setup_output_structure()`, `_copy_selected_files()`, `_prepare_input_structure()`, `_process_timepoint_directory()`, `_has_timepoint_pattern()`, `_has_channel_pattern()`, `_extract_experiment_metadata()`, interactive selection helpers, `_save_selections_to_config()`.
    - `SegmentationStage(StageBase)`: `validate_inputs()`, `run()`; invokes binning and external tools (Cellpose) via shell scripts/modules.
    - `ProcessSingleCellDataStage(StageBase)`: `validate_inputs()`, `run()` orchestrating ROI tracking, resizing, extraction, grouping; runs modules via subprocess.
    - `ThresholdGroupedCellsStage(StageBase)`: `validate_inputs()`, `run()`; executes ImageJ macro via Python glue.
    - `MeasureROIAreaStage(StageBase)`: `validate_inputs()`, `run()`; executes ImageJ macro.
    - `AnalysisStage(StageBase)`: `validate_inputs()`, `run()`; combine masks, analyze masks.
    - `CleanupStage(StageBase)`: `validate_inputs()`, `run()`; calls cleanup utility.
    - `CompleteWorkflowStage(StageBase)`: `validate_inputs()`, `run()` orchestrating all stages end-to-end.
  - Functions: `_create_stage_args()` (helper).
  - External deps: `subprocess`, `os`, `re`, `sys`, `shutil`, `pathlib`.
  - Internal imports: heavy `percell.core.paths` usage, `percell.core.run_subprocess_with_spinner`, `..core.stages.get_stage_registry`, and calls into sibling modules (`measure_roi_area.measure_roi_areas`, `cleanup_directories`).
  - Responsibility: Application orchestration; heavy infra coupling (subprocess/macros, filesystem).

- `percell/modules/advanced_workflow.py`
  - Purpose: Interactive “builder” to compose and run high-level steps.
  - Classes: `AdvancedWorkflowStage(StageBase)` with `validate_inputs()`, `run()`, `_execute_step()`, `_run_py_module()`, `_prompt_for_bins()`.
  - External deps: `subprocess`.
  - Internal imports: `..core.stages`, `..core.progress.run_subprocess_with_spinner`, `..core.paths`.
  - Responsibility: Application orchestration and UI; runs modules via subprocess.

- `percell/modules/bin_images.py`
  - Purpose: Downscale/bin microscopy images.
  - Classes: none.
  - Functions: `bin_image()`, `process_images()`, `main()`.
  - External deps: `numpy`, `skimage.io`, `skimage.exposure`, `skimage.transform.downscale_local_mean`, `tifffile`, `glob`, `re`, `logging`, `argparse`, `pathlib`.
  - Internal imports: none.
  - Responsibility: Data processing + file I/O (read/write TIFFs).

- `percell/modules/combine_masks.py`
  - Purpose: Combine per-channel masks into a single mask.
  - Classes: none.
  - Functions: `get_mask_prefix()`, `find_mask_groups()`, `read_image_with_metadata()`, `combine_masks()`, `process_all_masks()`, `main()`.
  - External deps: `numpy`, `cv2`, `tifffile`, `logging`, `argparse`, `pathlib`.
  - Internal imports: none.
  - Responsibility: Data processing + file I/O.

- `percell/modules/create_cell_masks.py`
  - Purpose: Generate per-cell masks from ROIs + combined masks via ImageJ macro.
  - Classes: none.
  - Functions: `find_matching_mask_for_roi()`, `create_output_dir_for_roi()`, `create_macro_with_parameters()`, `run_imagej_macro()`, `check_macro_file()`, `create_mask_macro()`, `main()`.
  - External deps: `numpy`, `cv2`, `subprocess`, `tempfile`, `glob`, `shutil`, `argparse`, `pathlib`, `logging`, `re`.
  - Internal imports: `percell.core.run_subprocess_with_spinner`.
  - Responsibility: External tool integration (ImageJ macro) + file I/O; some macro templating.

- `percell/modules/duplicate_rois_for_channels.py`
  - Purpose: Duplicate ROI archives across channels for analysis.
  - Classes: none.
  - Functions: `extract_channel_from_filename()`, `create_roi_filename_for_channel()`, `duplicate_rois_for_channels()`, `main()`.
  - External deps: `argparse`, `pathlib`, `logging`, `os`, `sys`, `re`, `shutil`.
  - Responsibility: File I/O and naming conventions.

- `percell/modules/extract_cells.py`
  - Purpose: Extract cell sub-images from ROIs via ImageJ macro.
  - Classes: none.
  - Functions: `create_macro_with_parameters()`, `run_imagej_macro()`, `check_macro_file()`, `find_image_for_roi()`, `create_output_dir_for_roi()`, `main()`.
  - External deps: `subprocess`, `tempfile`, `time`, `argparse`, `pathlib`, `re`, `logging`.
  - Internal imports: `percell.core.run_subprocess_with_spinner`.
  - Responsibility: External tool (ImageJ) integration + file I/O; macro templating.

- `percell/modules/group_cells.py`
  - Purpose: Group and sum cells into intensity bins; compute statistics; write grouped outputs and metadata.
  - Classes: none.
  - Functions: `compute_auc()`, `read_image()`, `find_cell_directories()`, `resize_image_to_target()`, `group_and_sum_cells()`, `process_cell_directory()`, `main()`.
  - External deps: `numpy`, `cv2`, `tifffile`, optional `skimage.io`, `sklearn.mixture.GaussianMixture`, `sklearn.cluster.KMeans`, `matplotlib.pyplot`, `scipy.stats`, `csv`, `json`, `glob`, `shutil`, `argparse`, `logging`, `pathlib`, `re`.
  - Responsibility: Algorithms (AUC, clustering, aggregation), plus heavy file I/O (TIFF read/write, CSV writes). Mixed concerns.

- `percell/modules/include_group_metadata.py`
  - Purpose: Merge group metadata CSVs into analysis results.
  - Classes: none.
  - Functions: `read_csv_robust()`, `find_group_metadata_files()`, `find_analysis_file()`, `load_group_metadata()`, `merge_metadata_with_analysis()`, `main()`.
  - External deps: `pandas`, `glob`, `argparse`, `logging`, `pathlib`, `re`.
  - Responsibility: Data processing + file I/O.

- `percell/modules/measure_roi_area.py`
  - Purpose: Measure ROI areas in raw images via ImageJ macro.
  - Classes: none.
  - Functions: `create_macro_with_parameters()`, `run_imagej_macro()`, `check_macro_file()`, `validate_inputs()`, `find_roi_image_pairs()`, `measure_roi_areas()`.
  - External deps: `subprocess`, `tempfile`, `argparse`, `logging`, `pathlib`.
  - Internal imports: `percell.core.run_subprocess_with_spinner`.
  - Responsibility: External tool integration + file I/O; macro templating.

- `percell/modules/otsu_threshold_grouped_cells.py`
  - Purpose: Threshold grouped images using ImageJ macro (Otsu).
  - Classes: none.
  - Functions: CLI entrypoint and macro handling (by naming/argparse and subprocess patterns).
  - External deps: `argparse`, `subprocess`, likely `pathlib`, `logging`.
  - Responsibility: External tool integration + file I/O.

- `percell/modules/resize_rois.py`
  - Purpose: Resize ROIs from binned images via ImageJ macro.
  - Classes: none.
  - Functions: `create_macro_with_parameters()`, `run_imagej_macro()`, `validate_inputs()`, `check_macro_file()`, `main()`.
  - External deps: `subprocess`, `tempfile`, `argparse`, `logging`, `pathlib`.
  - Internal imports: `percell.core.run_subprocess_with_spinner`.
  - Responsibility: External tool integration + file I/O; macro templating.

- `percell/modules/analyze_cell_masks.py`
  - Purpose: Run ImageJ macro to analyze masks; generate and combine CSV outputs.
  - Classes: none.
  - Functions: `create_macro_with_parameters()`, `run_imagej_macro()`, `check_macro_file()`, `find_mask_files()`, `generate_csv_filename()`, `process_mask_directory()`, `create_analysis_macro()`, `combine_csv_files()`, `main()`.
  - External deps: `pandas`, `numpy`, `cv2`, `subprocess`, `tempfile`, `glob`, `csv`, `shutil`, `argparse`, `logging`, `pathlib`, `time`, `re`.
  - Internal imports: `percell.core.progress.spinner`.
  - Responsibility: External tool integration + data processing + file I/O. Mixed concerns.

- `percell/modules/cleanup_directories.py`
  - Purpose: Remove heavy intermediate directories while preserving key outputs.
  - Classes: none.
  - Functions: `main()` plus helpers within file (scan/cleanup).
  - External deps: `os`, `shutil`, `json`, `argparse`, `logging`, `pathlib`.
  - Responsibility: Infra cleanup. I/O: deletes and writes.

- `percell/modules/directory_setup.py` and `percell/modules/set_directories.py`
  - Purpose: Interactive directory management with recent history and saving defaults.
  - Classes: none.
  - Functions:
    - `directory_setup`: `validate_directory_path()`, `get_recent_directories()`, `add_recent_directory()`, `prompt_for_directory()`, `get_paths_interactively()`, `save_config()`, `load_config()`, `save_recent_directories_automatically()`.
    - `set_directories`: `set_default_directories()`, `check_default_directories()`, `get_default_directories()`.
  - External deps: `json`, `pathlib`.
  - Responsibility: UI + config I/O.

- `percell/modules/stage_classes` support imports to sibling modules: `cleanup_directories`, `measure_roi_area`; to `percell.core.paths` frequently; to `percell.core.progress` utilities.

- `percell/modules/track_rois.py`
  - Purpose: Track ROIs between timepoints; match and write new zip ordering.
  - Classes: none.
  - Functions: `load_roi_dict()`, `load_roi_bytes()`, `polygon_centroid()`, `get_roi_center()`, `match_rois()`, `save_zip_from_bytes()`, `process_roi_pair()`, `find_roi_files_recursive()`, `batch_process_directory()`, `main()`.
  - External deps: `numpy`, `scipy.optimize.linear_sum_assignment`, `read_roi.read_roi_zip`, `zipfile`, `logging`, `argparse`, `glob`, `re`, `pathlib`.
  - Responsibility: Algorithms (matching via Hungarian method) + file I/O for ROI zips. Mixed concerns.

- `percell/modules/include_group_metadata.py`, `percell/modules/stage_registry.py`, etc. covered above.

### percell/setup
- `percell/setup/install.py`
  - Purpose: Installer: create venv, install requirements, validate dependencies, smoke test percell CLI.
  - Classes: `Colors` (ANSI).
  - Functions: multiple steps to create venv, pip install, run checks.
  - External deps: `venv`, `subprocess`, `json`, `argparse`, `pathlib`, `shutil`.
  - Responsibility: Out-of-band tooling. I/O: filesystem and subprocess.

- `percell/setup/requirements.txt`, `requirements_cellpose.txt`
  - Purpose: dependency lists.

### image_metadata (auxiliary workflow scripts)
- `image_metadata/zstack_creator.py`, `max_projection.py`, `microscopy_metadata_extractor.py`, `workflow_orchestrator.py`, `microscopy_stitcher.py`, `tiff_metadata_extractor.py`, `merge_channels_tiff.py`
  - Purpose: TIFF resolution extraction, Z-stacks, projections, stitching, metadata extraction/merge.
  - Classes: each defines one or more tool classes, e.g., `TiffResolutionExtractor`, `ZStackCreator`, `MaxProjection`, `MicroscopyMetadataExtractor`.
  - Functions: CLI mains and many helpers; heavy use of `tifffile`, `PIL.Image`, `numpy`.
  - External deps: `tifffile`, `PIL`, `numpy`, `argparse`, `csv`, `json`, `pathlib`, `subprocess` (rare), `re`.
  - Responsibility: Data processing + file I/O; infra for TIFF metadata handling.

### tests/examples
- `tests/test_paths.py`: tests path registry; reads central paths.
- `examples/progress_*`: demo usage of progress utilities.

## 2. DEPENDENCY ANALYSIS

- External library usage by module (high level):
  - `numpy`: binning, mask ops, ROI handling: `bin_images.py`, `combine_masks.py`, `group_cells.py`, `analyze_cell_masks.py`, many image_metadata scripts, `track_rois.py`.
  - `cv2`: image read/write/normalize/resize: `group_cells.py`, `combine_masks.py`, `analyze_cell_masks.py`, `create_cell_masks.py` (minor).
  - `skimage`: IO/transform/exposure: `bin_images.py`; optional IO in `group_cells.py`.
  - `tifffile`: reading/writing TIFF with metadata: `bin_images.py`, `group_cells.py`, `combine_masks.py`, image_metadata scripts.
  - `pandas`: CSV processing: `analyze_cell_masks.py`, `include_group_metadata.py`.
  - `sklearn`: GMM/KMeans: `group_cells.py`.
  - `matplotlib`: plotting maybe (grouping visualization): `group_cells.py`.
  - `scipy`: `stats` (grouping), `optimize.linear_sum_assignment` (ROI matching): `group_cells.py`, `track_rois.py`.
  - `PIL`: image_metadata scripts.
  - `alive_progress`: `core/progress.py`.
  - `subprocess`: many integration points: `core/progress.py`, `core/config.py` (detection), most ImageJ-related modules, `stage_classes.py`, `advanced_workflow.py`, `core/cli.py`, installer, some image_metadata.

- Modules performing file I/O:
  - Write/read image/ROI files: `bin_images.py`, `combine_masks.py`, `create_cell_masks.py`, `extract_cells.py`, `group_cells.py`, `analyze_cell_masks.py`, `measure_roi_area.py`, `resize_rois.py`, `track_rois.py`, image_metadata/*.py
  - Config/paths/logs: `core/config.py`, `core/logger.py`, `modules/directory_setup.py`, `set_directories.py`, `core/paths.py` (chmod), `core/pipeline.py` (mkdir), `core/cli.py` (runs bash to set up).
  - CSV I/O: `analyze_cell_masks.py`, `include_group_metadata.py`, `group_cells.py`.

- Pure business logic vs. infrastructure:
  - Mostly pure logic (algorithmic):
    - `group_cells.py`: compute_auc, clustering decisions, aggregation rules (mixed with I/O).
    - `track_rois.py`: centroid extraction, matching algorithm (mixed with I/O).
    - Part of `combine_masks.py`: merging logic (mixed).
  - Pure infrastructure:
    - `core/logger.py`, `core/paths.py`, `core/progress.py` (UI wrappers), `core/utils.py`, `setup/install.py`, CLI menu bits in `core/cli.py`.
  - Application orchestration:
    - `core/stages.py`, `core/pipeline.py`, `modules/stage_registry.py`, `modules/stage_classes.py`, `modules/advanced_workflow.py`.

- Modules that mix responsibilities:
  - `group_cells.py`, `analyze_cell_masks.py`, `combine_masks.py`, `track_rois.py`, `create_cell_masks.py`, `extract_cells.py`, `measure_roi_area.py`, `resize_rois.py`: each mixes algorithm/flow, external tool invocation, and filesystem I/O.

## 3. BUSINESS LOGIC IDENTIFICATION

- Core Domain Logic:
  - ROI and cell grouping analytics: `group_cells.py` (AUC computations, binning strategy, clustering with GMM/KMeans, resizing policy, per-bin aggregation).
  - ROI matching strategy across timepoints: `track_rois.py` (centroid, Hungarian matching).
  - Mask combination semantics: `combine_masks.py` (prefix matching, per-pixel merge).
  - Workflow rules (ordering, validation across selection/segmentation/analysis): `core/stages.py` (Executor) and high-level rules embedded in `stage_classes.py` and `advanced_workflow.py`.

- External Tool Integration:
  - ImageJ/Fiji macro execution: `create_cell_masks.py`, `extract_cells.py`, `measure_roi_area.py`, `resize_rois.py`, `analyze_cell_masks.py`, `otsu_threshold_grouped_cells.py`. Uses `subprocess` and macro templating.
  - Cellpose segmentation: `stage_classes.py` segmentation step; uses shell scripts or module invocations to call external tools.
  - TIFF image IO and metadata: `tifffile`, `PIL` across many modules and image_metadata.
  - CLI progress: `core/progress.py` with `alive_progress`.
  - Shell scripts for structure prep: `core/cli.py` uses bash.

- User Interface:
  - CLI: `core/cli.py` (parser, interactive menu).
  - Menus and prompts: `core/cli.py`, `advanced_workflow.py`, `modules/directory_setup.py` and `set_directories.py`.
  - Progress feedback: `core/progress.py`.

- Configuration:
  - `core/config.py` plus `modules/directory_setup.py`/`set_directories.py`.
  - `core/paths.py` (central path registry for macros/scripts/modules).

- Data Processing:
  - Image reading/writing, conversions: `bin_images.py`, `group_cells.py`, `combine_masks.py`, `analyze_cell_masks.py`, image_metadata scripts.
  - CSV read/write and merge: `analyze_cell_masks.py`, `include_group_metadata.py`.
  - ROI zip handling: `track_rois.py`.

## 4. COUPLING ANALYSIS

- Tightly coupled to concrete implementations:
  - `stage_classes.py`: imports `percell.core.paths` directly, calls concrete sibling modules and shell scripts; inlined subprocess invocation; hard references to macro file names and module file paths.
  - ImageJ macro runners (`create_cell_masks.py`, `extract_cells.py`, `measure_roi_area.py`, `resize_rois.py`, `analyze_cell_masks.py`): directly call `subprocess` and rely on macro templates at fixed paths.
  - `advanced_workflow.py`: delegates via registry but also directly composes command lists for module scripts.
  - Data I/O modules directly depend on `cv2`, `tifffile`, `skimage` with no abstraction.

- Difficult to test in isolation:
  - Any module invoking `subprocess` without injectable runner: most ImageJ/Cellpose steps, `core/cli.py` helper, installer.
  - Modules mixing filesystem with logic (e.g., `group_cells.py`, `track_rois.py`, `combine_masks.py`).

- Hard-coded dependencies:
  - Macro/template paths resolved via `core/paths.py` names; stage logic assumes these names exist.
  - Specific CLI prompts/menus embedded in code.
  - Cellpose/ImageJ expectations embedded in stages.

- Business logic mixed with infrastructure:
  - `group_cells.py`: clustering logic and saving TIFF/CSV.
  - `track_rois.py`: matching + zip read/write.
  - `analyze_cell_masks.py`: macro generation + pandas combination.
  - `create_cell_masks.py`, `extract_cells.py`, `measure_roi_area.py`, `resize_rois.py`: macro templating + subprocess + filesystem.

## 5. REFACTORING CANDIDATES (Ports and Adapters)

- Domain Services (move to `percell/domain/services`):
  - ROI tracking service: pure methods for `polygon_centroid`, `get_roi_center`, `match_rois` (decouple from zip I/O).
  - Cell grouping service: `compute_auc`, clustering selection and binning rules, aggregation policy (decouple from image I/O).
  - Mask combination service: pure mask merge logic.
  - Workflow policy service: decision rules for stage ordering and validation (extract from `stage_classes.py` where applicable).

- Port Interfaces (define in `percell/ports`):
  - `ImageReaderPort` / `ImageWriterPort`: read/write images with metadata.
  - `MacroRunnerPort`: run ImageJ macros with parameterized templates.
  - `SegmenterPort`: run segmentation (Cellpose).
  - `ROIRepositoryPort`: read/write ROI archives and ROI objects.
  - `MetadataStorePort`: CSV/DF storage for analysis outputs.
  - `FilesystemPort`: glob, mkdir, delete; abstract filesystem interactions for tests.
  - `ProgressPort`: progress/spinner API (wrap existing `core/progress`).
  - `PathProviderPort`: to resolve macro/module paths (wrap `core/paths`).

- Adapter Implementations (in `percell/adapters/outbound/...`):
  - Image adapters: `tifffile`, `cv2`, `skimage` implementations of `ImageReaderPort`/`ImageWriterPort`.
  - Macro/ImageJ adapter: wraps `subprocess` using `run_subprocess_with_spinner`, translating domain macro params to files.
  - Segmenter adapter: Cellpose CLI/py adapter.
  - ROI adapter: `read_roi_zip`, zipfile operations.
  - Pandas adapter: DataFrame/CSV merge/save for analysis/results.
  - Filesystem adapter: `pathlib` + `shutil` wrappers.

- Application Services (in `percell/application/use_cases`):
  - Use cases coordinating ports and domain services:
    - `RunDataSelection` (prompts delegated to UI port), `RunSegmentation`, `ProcessSingleCellData`, `ThresholdGroupedCells`, `MeasureRoiArea`, `AnalyzeMasks`, `Cleanup`.
  - `AdvancedWorkflow` orchestrator: accept selected steps; coordinate via ports/services without direct subprocess calls.

- Value Objects (in `percell/domain/value_objects`):
  - `DirectorySelection` (input/output, validation).
  - `Channel`, `Region`, `Timepoint`, `Condition`.
  - `BinningParameters` (num_bins, strategy).
  - `SegmentationParameters` (model, diameter, thresholds).
  - `ResolutionMetadata` (x,y, units).
  - `ROI` / `ROISet` (geometry, ID).
  - `ImagePath`, `MaskPath` (typed paths).

- Entities (in `percell/domain/entities`):
  - `Cell`: id, region, timepoint, channel, intensities; behaviors for aggregation.
  - `CellGroup`: bins with statistics.
  - `AnalysisRun`: captures workflow run, steps executed, outputs.

## 6. MIGRATION PRIORITY

- High Priority (business logic mixed with infra; heavy coupling):
  - `percell/modules/stage_classes.py` (central coordinator calling concrete modules; extract use-case services and ports; invert path/macro/runner dependencies).
  - `percell/modules/group_cells.py` (separate clustering/aggregation domain logic from I/O; introduce `ImageReaderPort`, `MetadataStorePort`).
  - `percell/modules/analyze_cell_masks.py` (split macro generation/runner vs. CSV aggregation; port + domain service).
  - `percell/modules/track_rois.py` (extract matching into domain; ROI repo adapter).
  - `percell/modules/create_cell_masks.py`, `extract_cells.py`, `resize_rois.py`, `measure_roi_area.py` (introduce `MacroRunnerPort`, `PathProviderPort`, move macro paramization to domain service).

- Medium Priority (clear responsibilities but still concrete deps):
  - `percell/core/cli.py` (introduce UI/input ports; isolate subprocess call for setup script).
  - `percell/modules/combine_masks.py` (separate combine logic from image I/O).
  - `percell/modules/include_group_metadata.py` (wrap pandas I/O behind port).
  - `percell/modules/bin_images.py` (wrap image I/O; keep algorithm pure).

- Low Priority (pure infra or presentation):
  - `percell/core/{paths,logger,progress,stages,pipeline}` (already layered; perhaps surface ports).
  - `percell/modules/{directory_setup,set_directories,cleanup_directories}` (infra/UI; can remain adapters).
  - `percell/setup/install.py`, examples, tests.
  - image_metadata/* (adjacent tools; refactor later or keep as separate adapters + domain bits if reused).

### Notes on business concepts to preserve/promote to domain
- Experiment selection model: datatype (single/multi timepoint), conditions, timepoints, regions, segmentation/analysis channels, inferred metadata and directory schemas (currently built in `DataSelectionStage`).
- Segmentation parameters and outcomes: model, diameter, thresholds; standardize as `SegmentationParameters`.
- ROI semantics: size normalization, resizing from binned images, cross-timepoint tracking and ID mapping.
- Grouping policy: bin count, method (GMM/KMeans), AUC/intensity computations, aggregation per bin; keep reproducible.
- Mask combination rules: per-channel merging and metadata-preserving saves.
- Analysis outputs: filenames and CSV schemas; build typed structures.

### Example port boundaries to insert in hot spots
- In `stage_classes.SegmentationStage.run()`: depend on `SegmenterPort` and `ImageReaderPort` instead of calling scripts; use `ProgressPort` and `PathProviderPort`.
- In `group_cells.group_and_sum_cells()`: split to `GroupCellsService` (pure) + `ImageRepo` read/write adapter + `MetadataStorePort` for CSV.
- In macro modules: replace direct `subprocess` with `MacroRunnerPort.run(macro: MacroTemplate, params: Dict) -> Result`.

---

Dependency maps and I/O summaries (concise):
- External-tool integrators: `create_cell_masks.py`, `extract_cells.py`, `measure_roi_area.py`, `resize_rois.py`, `analyze_cell_masks.py`, `otsu_threshold_grouped_cells.py`, `stage_classes.py`, `advanced_workflow.py`, `core/cli.py` (script run), `core/progress.py` (runner).
- Image I/O heavy: `bin_images.py`, `group_cells.py`, `combine_masks.py`, `analyze_cell_masks.py`, image_metadata/.
- Core domain-heavy logic (to lift): `group_cells.py` (metrics/clustering), `track_rois.py` (matching), `combine_masks.py` merge logic.

Testing pain points today:
- Direct `subprocess` calls; no injectable runner or fakes.
- Interleaving file I/O and logic; no seam for in-memory tests.
- Hard-coded macro paths and directory schemas via `core/paths` without abstraction.

Refactor impact:
- After introducing ports, most module scripts become thin adapters or application services; domain logic becomes testable functions/classes with zero side effects.

Summary
- High-signal modules identified for decoupling: `stage_classes.py`, `group_cells.py`, macro-based modules, `track_rois.py`.
- Proposed ports: Image IO, MacroRunner, Segmenter, ROI Repo, Metadata Store, Filesystem, Path Provider, Progress.
- Domain services to extract: ROI matching, cell grouping/aggregation, mask combination, workflow policy.
- Entities/VOs recommended: ROI, Cell, CellGroup, DirectorySelection, Channels/Regions/Timepoints, Segmentation/Binning params, ResolutionMetadata.
- Migration priority ranks given to guide ports-and-adapters refactor across layers.