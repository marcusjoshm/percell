#!/usr/bin/env python3
"""
Smoke test for ports/adapters using a real dataset path.

This does NOT run the full legacy pipeline. It:
 - Instantiates the DI container
 - Probes ImageJ and Cellpose availability/version
 - Lists available macros
 - Parses a few sample filenames via Metadata adapter
 - Executes the domain orchestrator (skeleton) to ensure wiring works
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from percell.infrastructure.dependencies.container import Container, AppConfig
from percell.application.use_cases.run_complete_workflow import RunCompleteWorkflow
from percell.adapters.outbound.metadata.metadata_adapter import FileNameMetadataAdapter
from percell.domain.value_objects.file_path import FilePath


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    input_dir = Path(args.input)
    output_dir = Path(args.output)

    # Basic path checks
    print(f"Input directory: {input_dir}")
    print(f"Output directory: {output_dir}")
    if not input_dir.exists():
        print("ERROR: Input directory does not exist.")
        return 2
    output_dir.mkdir(parents=True, exist_ok=True)

    # Use ImageJ path from package config if available
    imagej_path = None
    try:
        from percell.core.paths import get_path_str
        imagej_path = get_path_str("imagej_path")
    except Exception:
        # Fallback to config.json
        try:
            import json
            cfg = json.loads((Path(__file__).parent.parent / "percell" / "config" / "config.json").read_text())
            imagej_path = cfg.get("imagej_path")
        except Exception:
            imagej_path = None

    # Cellpose python path from config if present
    cellpose_py = None
    try:
        import json
        cfg = json.loads((Path(__file__).parent.parent / "percell" / "config" / "config.json").read_text())
        cellpose_py = cfg.get("directories", {}).get("cellpose_path")
    except Exception:
        cellpose_py = None

    container = Container(
        AppConfig(
            storage_base_path=str(output_dir),
            cellpose_path=cellpose_py,
            imagej_path=imagej_path,
        )
    )

    # Probe adapters
    imgj = container.imagej_adapter
    cellpose = container.cellpose_adapter
    print(f"ImageJ available: {imgj.is_available()} (path={imagej_path})")
    print(f"Available macros (count): {len(imgj.get_available_macros())}")
    print(f"Cellpose available: {cellpose.is_available()}")
    print(f"Cellpose version: {cellpose.get_version()}")

    # Metadata parsing on a few sample files
    meta = FileNameMetadataAdapter()
    tifs = list(input_dir.rglob("*.tif")) + list(input_dir.rglob("*.tiff"))
    sample_files = tifs[:5]
    print(f"Sample image files found: {len(tifs)} (showing up to 5)")
    for p in sample_files:
        md = meta.extract_metadata_from_filename(FilePath(p))
        print(f"  {p.name} -> cond={md.condition} t={md.timepoint} reg={md.region} ch={md.channel}")

    # Run orchestrator skeleton to validate wiring
    use_case = RunCompleteWorkflow(container.workflow_orchestrator())
    summary = use_case.execute(workflow_id="smoke_test")
    print(f"Workflow executed. Status={summary.get('status')} steps={len(summary.get('steps', []))}")

    print("SMOKE TEST OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())


