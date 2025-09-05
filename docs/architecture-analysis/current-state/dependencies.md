# Dependency Analysis (main branch)

Source: main branch at commit 925cee92e220a947ff10ce15415e2957f4812430

Artifacts:
- JSON graph: `../dependencies/percell_deps.json`
- SVG graph: `../dependencies/percell_deps.svg`

## Highlights

- Core package boundaries: `percell.core` orchestrates `config`, `logger`, `stages`, `pipeline`.
- `percell.main.main` depends on `core` and module registry.
- Modules import `percell` and `percell.core`, reflecting coupling to orchestration.
- No http/db libraries detected; strong reliance on `subprocess` and filesystem.

## Potential Hotspots

- `percell.modules.stage_classes` imports many modules including `cleanup_directories`, `measure_roi_area`.
- Multiple modules shell out to external tools; consider extracting outbound ports.
- CLI logic spread: `percell.core.cli`, `percell.main.main`, and module-level `argparse`.

## Circular/Tight Coupling

- No explicit cycles detected in summary, but `modules`↔`core` coupling is tight via direct imports.

## Next Steps

- Extract interfaces for outbound interactions (subprocess, filesystem).
- Consolidate argument parsing behind a `CommandPort`.
