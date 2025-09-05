# Component Classification (main branch)

Source: main branch at commit 925cee92e220a947ff10ce15415e2957f4812430

## Classification

- Business Logic (core candidates)
  - `percell.core.pipeline`, `percell.core.stages` (orchestration)
  - `percell.core.config` (configuration model)
  - `percell.core.utils` (generic utilities)

- External Interfaces (driving adapters today)
  - `percell.main.main` (CLI entrypoint)
  - `percell.core.cli` (CLI parser and menu)
  - Module-level CLI parsers in `percell/modules/*` (argparse)

- Infrastructure (driven adapters today)
  - Subprocess calls in `percell/core/progress.py`, `percell/modules/*`, `percell/setup/install.py`
  - Filesystem operations across modules and core
  - Image processing libs usage (cv2, skimage) within modules

- Mixed/Unclear
  - `percell.modules.*` combine orchestration logic with infrastructure operations.

## Notes

- Strong coupling between modules and core suggests a future `UseCase` layer to mediate.
- Consider extracting `Ports` for: Subprocess, FileSystem, ImageIO, ConfigStore, Logging.
