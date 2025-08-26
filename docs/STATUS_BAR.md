### Terminal Status Bar Module

This module provides reusable, minimal wrappers around the `alive-progress` library for consistent terminal progress bars and spinners across the project.

Location: `percell/core/progress.py`

#### Why this design
- **Decoupled**: Project code imports small helpers from `percell.core.progress` rather than `alive-progress` directly.
- **Safe fallback**: If `alive-progress` is not installed, helpers degrade to no-ops so code still runs without crashing.
- **Consistent UX**: Centralized configuration and unified API ensure the same look-and-feel in all modules.
- **Composable**: Supports simple manual updates, iterable wrapping, and spinner use-cases.

#### Installation
`alive-progress` is added to project requirements. If you are developing outside the installer, ensure the dependency is installed:

```bash
pip install alive-progress>=3.1.5
```

#### API Overview

Exported via `percell/core/__init__.py` for convenient import:
- `is_progress_available() -> bool`
- `configure_global(spinner=None, theme=None, enrich_print=None, title_length=None) -> None`
- `progress_bar(total=None, title=None, unit="items", manual=False)` — context manager yielding `update(delta:int)`
- `iter_with_progress(iterable, total=None, title=None, enrich_items=False)` — wraps iterables
- `spinner(title=None)` — spinner context manager

#### Quick examples

1) Manual updates (known total):
```python
from percell.core import progress_bar

items = range(100)
with progress_bar(total=len(items), title="Processing") as update:
    for _ in items:
        # do work
        update(1)
```

2) Unknown total (spinner):
```python
from percell.core import spinner

with spinner("Indexing files"):
    index_files()
```

3) Iterate with progress:
```python
from percell.core import iter_with_progress

for item in iter_with_progress(paths, title="Loading"):
    load(item)
```

4) Optional global configuration:
```python
from percell.core import configure_global

configure_global(theme="classic", spinner="dots", enrich_print=True)
```

#### Integration guidance

- Prefer `iter_with_progress` for straightforward loops over known collections.
- Use `progress_bar` when you need explicit control over increments or mixed work per step.
- Use `spinner` for tasks with unknown totals or where progress granularity is unclear.
- Keep existing logging via `percell.core.logger` for textual status; progress bars complement logs, not replace them.
- Avoid printing directly while a bar is active; if needed, consider enabling `enrich_print` via `configure_global` to harmonize output.

#### Patterns for pipeline stages

Within any stage implementation (see `percell/modules/*`), wrap file processing:
```python
from percell.core import iter_with_progress

def run_stage(file_paths):
    for path in iter_with_progress(file_paths, title="Stage: processing files"):
        process_file(path)
```

Or for dynamic workloads:
```python
from percell.core import progress_bar

def run_stage(tasks):
    with progress_bar(total=len(tasks), title="Stage: tasks") as update:
        for t in tasks:
            handle_task(t)
            update(1)
```

#### Notes
- The helpers use `force_tty=True` to render within various terminals; if unavailable, alive-progress silently degrades.
- If `alive-progress` is missing, all helpers are safe no-ops so existing modules won’t fail.


