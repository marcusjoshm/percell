#!/usr/bin/env python3
"""
Script to split stage_classes.py into separate files.

Extracts each Stage class into its own file in application/stages/
"""

from pathlib import Path
import re

# Stage definitions: (class_name, start_line, end_line, filename)
STAGES = [
    ("DataSelectionStage", 24, 727, "data_selection_stage.py"),
    ("SegmentationStage", 728, 860, "segmentation_stage.py"),
    ("ProcessSingleCellDataStage", 861, 999, "process_single_cell_stage.py"),
    ("ThresholdGroupedCellsStage", 1000, 1074, "threshold_grouped_cells_stage.py"),
    ("MeasureROIAreaStage", 1075, 1168, "measure_roi_area_stage.py"),
    ("AnalysisStage", 1169, 1295, "analysis_stage.py"),
    ("CleanupStage", 1296, 1390, "cleanup_stage.py"),
    ("CompleteWorkflowStage", 1391, 1500, "complete_workflow_stage.py"),
]

COMMON_HEADER = '''"""
{stage_name} - Application Layer Stage

Auto-generated from stage_classes.py split.
"""

from __future__ import annotations

import subprocess
import os
import re
import sys
import shutil
from pathlib import Path
from typing import Dict, Any, List, Set, Optional

from percell.application.progress_api import run_subprocess_with_spinner
from percell.domain import WorkflowOrchestrationService
from percell.domain.models import WorkflowStep, WorkflowState, WorkflowConfig
from percell.domain import DataSelectionService, FileNamingService
from percell.application.stages_api import StageBase


'''

def extract_stage(source_file: Path, class_name: str, start_line: int, end_line: int, output_file: Path):
    """Extract a stage class from the source file."""
    with open(source_file, 'r') as f:
        lines = f.readlines()

    # Extract the class (lines are 1-indexed, but list is 0-indexed)
    class_lines = lines[start_line-1:end_line]

    # Create header with stage name
    header = COMMON_HEADER.format(stage_name=class_name)

    # Combine header and class
    content = header + ''.join(class_lines)

    # Write to output file
    with open(output_file, 'w') as f:
        f.write(content)

    print(f"✓ Extracted {class_name} to {output_file.name} ({len(class_lines)} lines)")


def main():
    source_file = Path("percell/application/stage_classes.py")
    output_dir = Path("percell/application/stages")

    if not source_file.exists():
        print(f"Error: {source_file} not found")
        return 1

    output_dir.mkdir(parents=True, exist_ok=True)
    print(f"Creating stages in {output_dir}/\n")

    for class_name, start, end, filename in STAGES:
        output_file = output_dir / filename
        extract_stage(source_file, class_name, start, end, output_file)

    print(f"\n✅ Extracted {len(STAGES)} stage classes")
    print(f"\nNext steps:")
    print(f"1. Create percell/application/stages/__init__.py")
    print(f"2. Update percell/application/stage_registry.py imports")
    print(f"3. Test imports")
    print(f"4. Remove percell/application/stage_classes.py")

    return 0


if __name__ == '__main__':
    import sys
    sys.exit(main())
