# Current State Architecture (Analysis of main branch content)

Source: main branch at commit 925cee92e220a947ff10ce15415e2957f4812430

This document summarizes the current architecture, directory structure, and dependencies of the Percell project as it exists on the main branch. No source changes were made as part of this analysis.

## Directory Structure (high-level)

- percell/: Python package with core, modules, main entrypoint, adapters/utilities
- percell/core/: Core orchestration: config, logger, pipeline, stages, progress, paths, utils
- percell/main/: CLI entrypoint wrapper
- percell/modules/: Operational steps for image processing and workflows
- percell/adapters/: CLI and outbound adapters (shell wrappers)
- percell/services, application, domain, ports, infrastructure: present but currently thin or transitional
- image_metadata/: standalone scripts/tools for TIFF metadata and workflows
- tests/: unit/integration tests
- docs/: documentation

## Notable Architectural Patterns

- Central orchestration via `percell.core.pipeline` and `percell.core.stages`
- CLI parsing centralized in `percell.core.cli` and `percell.main.main`
- ImageJ and external tool invocation via `subprocess` from modules and progress utilities
- Heavy filesystem usage (`pathlib`, glob, shutil) for data flow between steps

## Dependency Overview

- Internal dependency graph artifacts generated with pydeps:
  - JSON: docs/architecture-analysis/dependencies/percell_deps.json
  - SVG: docs/architecture-analysis/dependencies/percell_deps.svg

## External Touchpoints (initial)

- Subprocess invocations: ImageJ macros, Python scripts, environment setup
- Filesystem: reading TIFF/CSV, writing outputs, copying/moving files
- No direct DB or HTTP client usage found in package

## Next

- See `components.md`, `dependencies.md`, and `dataflow.md` for deeper analysis.
