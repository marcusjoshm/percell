# Migration Roadmap (toward Ports & Adapters)

Source analyzed: main branch at commit 925cee92e220a947ff10ce15415e2957f4812430

## Phases

### Phase A: Interface Extraction (Low Risk)
- Define `ProcessExecutionPort`, `FileSystemPort`, `ImageIOPort`, `LoggingPort`, `CommandPort`.
- Create interfaces in a `percell/ports` package (no implementation changes yet).

### Phase B: Adapter Creation (Medium Risk)
- Implement adapters in `percell/adapters`: subprocess, fs, imageio, logging, cli.
- Replace direct calls in modules with ports via dependency injection entrypoints.

### Phase C: Core Isolation (Higher Risk)
- Introduce `use_cases` layer coordinating stages via ports.
- Move orchestration rules from modules into core use cases.
- Remove direct framework/library imports from core.

### Phase D: Testing & Validation (Critical)
- Unit tests for ports/adapters and use cases.
- Contract tests for adapters against real tools.
- Integration flow tests for pipelines.

## Risk Assessment
- Breaking changes: CLI entrypoints and module signatures during DI introduction.
- Testing: need coverage on file/process-heavy flows.
- Rollback: Keep feature flags or compatibility wrappers for CLI.
- Effort: Phase A (S), B (M), C (L), D (M).

## File Priorities
- High: `percell/core/*` (pipeline, stages, cli), `percell/modules/stage_classes.py`.
- Medium: remaining modules invoking subprocess/FS.
- Low: config, utils, setup scripts.
