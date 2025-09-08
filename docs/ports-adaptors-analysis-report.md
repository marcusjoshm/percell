### Percell Ports & Adapters Architecture Analysis (Refactor)

Date: 2025-09-08

### Executive summary

- The refactor establishes clear boundaries: domain models/services are separated from application logic and concrete adapters.
- Ports are defined as `typing.Protocol` interfaces under `percell/ports`. Adapters implement these ports for ImageJ, Cellpose, filesystem, image processing, and CLI UI.
- A simple DI container exists, but several application helpers and stages instantiate adapters directly, bypassing ports and the container. This weakens substitutability and testability.
- Domain layer is mostly infrastructure-free, but a few services (e.g., intensity analysis) perform IO/format-specific work. Consider pushing IO to adapters so domain receives data, not file paths.
- Tests cover adapters and domain services well; add import rules and architecture tests to guard boundaries over time.

---

### 1) Ports and Adapters mapping

- Driven ports (outbound):
  - `percell/ports/driven/imagej_integration_port.py` → ImageJ macro execution
  - `percell/ports/driven/cellpose_integration_port.py` → Cellpose segmentation
  - `percell/ports/driven/image_processing_port.py` → Image IO and transforms
  - `percell/ports/driven/file_management_port.py` → Filesystem operations
- Driving ports (inbound):
  - `percell/ports/driving/user_interface_port.py` → User interaction
  - `percell/ports/driving/workflow_execution_port.py` → Orchestrated workflow execution (protocol; no concrete implementation yet)

Adapters implementing ports:
- `ImageJIntegrationPort` → `percell/adapters/imagej_macro_adapter.py` (subprocess-based, streams progress)
- `CellposeIntegrationPort` → `percell/adapters/cellpose_subprocess_adapter.py` (subprocess, GUI/no-args and batch variants)
- `ImageProcessingPort` → `percell/adapters/pil_image_processing_adapter.py` (Pillow + NumPy)
- `FileManagementPort` → `percell/adapters/local_filesystem_adapter.py` (stdlib `shutil`, `fnmatch`)
- `UserInterfacePort` → `percell/adapters/cli_user_interface_adapter.py` (stdin/stdout)
- `WorkflowExecutionPort` → Not yet implemented by any adapter

Observations:
- Adapters adhere to port method shapes. Error handling is pragmatic, generally avoiding raising, returning success/failure idioms.
- Progress is surfaced in the ImageJ adapter via streaming and the app-level `progress_api`.

Gaps:
- No driving adapter for `WorkflowExecutionPort`. If you plan to expose programmatic or service entrypoints, add an adapter for that port.

---

### 2) Dependency injection and wiring

- `percell/application/container.py` builds a `Container` with:
  - `ConfigurationManager`
  - `WorkflowOrchestrationService`, `WorkflowCoordinator`, `StepExecutionCoordinator`
  - Adapters: `ImageJMacroAdapter`, `CellposeSubprocessAdapter`, `LocalFileSystemAdapter`, `PILImageProcessingAdapter`
- `percell/main/bootstrap.py` returns `build_container(...)` and `main.py` attempts to initialize the container.

Findings:
- The container constructs adapters but application helpers often instantiate adapters directly:
  - `application/imagej_tasks.py` imports `ImageJMacroAdapter` and `LocalFileSystemAdapter` directly.
  - `application/image_processing_tasks.py` imports and constructs `PILImageProcessingAdapter` directly.
  - `application/stage_classes.py` constructs `CellposeSubprocessAdapter` directly for the segmentation stage when a path is present.

Impact:
- Bypassing ports/DI reduces substitutability (e.g., swapping to a different image stack or mock for tests) and increases coupling from application helpers to specific adapter types.

Recommendations:
- Pass port instances from the container into application services/stages. For example, change helpers to accept `ImageJIntegrationPort`/`ImageProcessingPort` parameters, defaulting to injected instances.
- Avoid importing adapters in application helpers; depend on ports.

---

### 3) Workflow orchestration and stages

- Domain orchestrator: `domain/services/workflow_orchestration_service.py` validates step order, deduplicates, and manages `WorkflowState` transitions.
- Application coordinators: `WorkflowCoordinator` and `StepExecutionCoordinator` wrap orchestration and execution mapping.
- Stage registration and execution:
  - `application/stage_registry.py` registers stages from `application/stage_classes.py` and optional advanced workflow.
  - `application/stages_api.py` defines `StageBase`, `StageExecutor`, and a global `StageRegistry`.
  - `application/pipeline_api.py` selects which stages to run based on CLI args and executes them with `StageExecutor`.

Findings:
- Orchestration logic is cleanly separated. Stage execution composes app-level helpers that call adapters.
- `CompleteWorkflowStage` demonstrates domain normalization of steps before running the sequence, then uses the registry to instantiate stages.

Opportunities:
- `WorkflowCoordinator` currently delegates fully to the domain orchestrator. Over time, inject step executors through ports to converge the coordinator and the stage pipeline or clarify ownership between these two execution paths.

---

### 4) Configuration, paths, progress, and logging

- Config: `application/config_api.py` (`Config`) manages JSON, nested get/set, validation; `ConfigurationManager` provides simple get/set and atomic saves.
- Paths: `application/paths_api.py` centralizes package-relative paths, retains legacy keys (`core`, `modules`) for compatibility.
- Progress: `application/progress_api.py` wraps `alive_progress` with safe fallbacks; includes spinner and subprocess helpers.
- Logging: `application/logger_api.py` provides `PipelineLogger` and `ModuleLogger`, writing console and rotating files under `<output>/logs`.

Findings:
- Logging and progress are decoupled from domain and adapters, used at application level. Good layering.
- `paths_api` still references legacy directory names (`core`, `modules`) to locate assets; this is fine for migration, but consider pruning legacy keys once migration completes.

---

### 5) Domain layer assessment

- Domain models are pure dataclasses/enums in `domain/models.py`.
- Domain services:
  - `workflow_orchestration_service.py`: pure control logic, no IO.
  - `data_selection_service.py`: filesystem scanning and filename parsing heuristics (touches filesystem via Path.rglob).
  - `file_naming_service.py`: pure parsing/formatting logic.
  - `cell_segmentation_service.py`: strategy and validation rules, no external tool invocation.
  - `intensity_analysis_service.py`: reads images with `tifffile` and computes metrics with NumPy.

Findings:
- Most domain services avoid concrete frameworks. Two exceptions:
  - Data selection scans the filesystem; consider making the directory scan an adapter concern and pass `List[Path]` into domain for parsing/validation.
  - Intensity analysis reads files via `tifffile`; prefer moving IO to an adapter and passing arrays into the domain to keep file formats out of the core.

Tradeoffs:
- Allowing NumPy in domain is commonly acceptable for pure computation. The stronger boundary is to avoid direct file IO (tifffile reads) inside domain services.

---

### 6) Tests overview and boundary coverage

- Unit tests (domain): cover `workflow_orchestration_service`, `data_selection_service`, naming, intensity, package resources.
- Integration tests (adapters): cover `ImageJMacroAdapter`, `CellposeSubprocessAdapter`, `LocalFileSystemAdapter`, `PILImageProcessingAdapter`.
- Integration tests (application): container building, workflow/step coordinators, ImageJ helper integrations.

Gaps to consider:
- Add tests asserting adapters conform to ports (mypy Protocol checks are implicit; can add `isinstance` checks or protocol compliance tests where appropriate).
- Add import-linter contract test to enforce no imports from `adapters`/`application` in `domain`.
- Add fitness tests for DI usage in helpers (e.g., ensure helpers accept ports and do not instantiate adapters directly).

---

### 7) Dependency rule adherence

Positive:
- `application` depends on `domain` and adapters, not vice versa.
- `ports` are simple, and adapters import them rather than the reverse.

Issues/risks:
- Domain services performing IO (`tifffile.imread`) and filesystem scans blur the boundary. Risk: future format/tool changes ripple into domain.
- Application helpers import concrete adapters directly, rather than depending on ports and injection.

Suggested import rules (import-linter):
```
[importlinter]
root_package = percell

[importlinter:contract:1]
name = Domain independence
type = forbidden
source_modules = percell.domain
forbidden_modules = percell.adapters, percell.application

[importlinter:contract:2]
name = Ports layering
type = forbidden
source_modules = percell.ports
forbidden_modules = percell.adapters, percell.application

[importlinter:contract:3]
name = Application does not import main
type = forbidden
source_modules = percell.application
forbidden_modules = percell.main
```

---

### 8) Recommended changes (prioritized)

1) Invert dependencies in application helpers (High)
- Change `application/imagej_tasks.py` and `application/image_processing_tasks.py` to accept port instances (e.g., `ImageJIntegrationPort`, `FileManagementPort`, `ImageProcessingPort`) as parameters.
- Thread these ports from `Pipeline`/`Container` to stages and helpers.

2) Stop instantiating adapters in stages (High)
- In `SegmentationStage`, inject a `CellposeIntegrationPort` instead of creating `CellposeSubprocessAdapter` inside the stage.

3) Move file IO out of domain (Medium)
- Refactor `IntensityAnalysisService` to accept arrays and ROIs; perform file reading via an image IO adapter at the application layer.
- Refactor `DataSelectionService.scan_available_data` to be driven by a file enumeration adapter if you want a strict hex boundary.

4) Add architecture guards (Medium)
- Add import-linter with the contracts above.
- Add a simple AST-based test to assert domain does not import adapters/application.

5) Introduce `WorkflowExecutionPort` adapter (Optional)
- Provide a driving adapter for programmatic entrypoints (e.g., a REST or CLI orchestration adapter) if needed.

6) Prune legacy path keys (Low)
- Once migration completes, remove `core`/`modules` references from `paths_api` and stage registration shims, or conditionally gate them behind a migration flag.

---

### 9) Quick wins and code pointers

- Replace direct adapter imports in helpers:
  - `application/imagej_tasks.py`: remove imports of `ImageJMacroAdapter` and `LocalFileSystemAdapter`; accept `ImageJIntegrationPort` and `FileManagementPort` params.
  - `application/image_processing_tasks.py`: accept `ImageProcessingPort` param and default to injected instance.
- Propagate dependencies:
  - `application/pipeline_api.py` → get ports from container and pass through `StageExecutor` to stages.
  - `application/stage_classes.py` → stages accept ports in `__init__` and store them for `run`.

---

### 10) Suggested fitness functions and tooling

- Import rules: import-linter config as above; add CI job to run it.
- Dependency visualization: `pydeps percell --max-bacon 2 --cluster -o dependencies.svg`.
- UML: `pyreverse -o png -p Percell percell/`.
- Metrics: `radon cc percell -s` and `radon mi percell -s` to watch for complexity/maintainability regressions.

---

### 11) Appendix: Current state snapshot

- Ports defined: 6 (4 driven, 2 driving). 5 have adapters; 1 missing.
- Container builds: config manager, domain orchestrator, coordinators, 4 adapters.
- Key application modules:
  - `stage_classes.py`: concrete pipeline stages
  - `stages_api.py`: stage runtime abstractions
  - `pipeline_api.py`: CLI-driven pipeline
  - `imagej_tasks.py`, `image_processing_tasks.py`: helper functions (need DI)
  - `paths_api.py`, `logger_api.py`, `progress_api.py`
- Domain purity: high, with noted IO exceptions to consider refactoring.
- Tests: solid coverage for domain and adapters; add architecture tests.

---

### 12) Action checklist

- [x] Refactor helpers to consume ports instead of concrete adapters
- [x] Inject ports from container into pipeline/stages/helpers
- [ ] Move IO from domain services to adapters where feasible
- [ ] Add import-linter and CI check
- [ ] Add architecture fitness tests
- [ ] Optional: implement `WorkflowExecutionPort` adapter


