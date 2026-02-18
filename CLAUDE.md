# PerCell — Single-Cell Microscopy Analysis Tool

## Project
Python 3.8+ CLI tool. Hexagonal architecture (domain → application → adapters).
Cellpose for segmentation, ImageJ macros for thresholding/analysis.
MIT licensed. Repo: https://github.com/marcusjoshm/percell

## Architecture
- `percell/domain/` — Core business logic (cell analysis, workflow orchestration). Never import adapters here.
- `percell/application/` — Pipeline orchestration, configuration management.
- `percell/adapters/` — External tool integration (ImageJ, Cellpose, file system).
- `percell/ports/` — Interface definitions (abstract base classes).
- `tests/` — Mirrors source structure.

## Commands
- Install: `pip install -e .`
- Run: `python -m percell.main.main`
- Tests: `pytest tests/ -v`
- Lint: `ruff check percell/`
- Type check: `mypy percell/`

## Code Conventions
- Follow existing hexagonal architecture. New features go through ports → adapters.
- Type hints on all public functions.
- Docstrings: Google style.
- For ImageJ macro patterns, see `percell/adapters/imagej/`.
- For Cellpose integration patterns, see `percell/adapters/cellpose/`.

## Known Harmless Warnings
- **"Unable to locate a Java Runtime"** — On macOS, ImageJ/Fiji prints this stderr message
  twice per invocation. It is cosmetic and does NOT affect macro execution. Always ignore it.

## Context Rules
- When compacting, always preserve: list of modified files, test commands, current task.
- Commit after each completed task with descriptive messages.
- Before starting implementation, read relevant existing files first.
- Use subagents for codebase exploration — don't read dozens of files in main context.

## Feature Development Workflow

MANDATORY for all new features: use `/new-feature <description>` to start.
This enforces: branch creation → planning → review gates → implementation →
testing → benchmarks → documentation → master guide update → merge.

- Never skip review checkpoints. Always stop and present findings to the user.
- Every phase ends with a git commit.
- Update the feature guide (docs/features/<name>.md) at every step.
- Update MASTER_GUIDE.md before merging.
- Use subagents for codebase research to preserve main context.
- Use the feature-reviewer agent for all review checkpoints.
- After merging, run the Compound step: update this file with lessons learned.