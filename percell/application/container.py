from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from percell.application.configuration_manager import ConfigurationManager
from percell.application.workflow_coordinator import WorkflowCoordinator
from percell.application.step_execution_coordinator import StepExecutionCoordinator
from percell.domain.services.workflow_orchestration_service import WorkflowOrchestrationService
from percell.adapters.imagej_macro_adapter import ImageJMacroAdapter
from percell.adapters.cellpose_subprocess_adapter import CellposeSubprocessAdapter
from percell.adapters.local_filesystem_adapter import LocalFileSystemAdapter
from percell.adapters.pil_image_processing_adapter import PILImageProcessingAdapter


@dataclass(slots=True)
class Container:
    cfg: ConfigurationManager
    orchestrator: WorkflowOrchestrationService
    workflow: WorkflowCoordinator
    step_exec: StepExecutionCoordinator
    imagej: ImageJMacroAdapter
    cellpose: CellposeSubprocessAdapter
    fs: LocalFileSystemAdapter
    imgproc: PILImageProcessingAdapter


def build_container(config_path: Path) -> Container:
    cfg = ConfigurationManager(config_path)
    cfg.load()

    orchestrator = WorkflowOrchestrationService()
    workflow = WorkflowCoordinator(orchestrator=orchestrator)
    step_exec = StepExecutionCoordinator()

    # Get project root for resolving relative paths to external resources
    from percell.application.paths_api import get_path_config
    project_root = get_path_config().get_project_root()

    imagej_path = Path(cfg.get("imagej_path", cfg.get_nested("paths.imagej") or "/Applications/ImageJ.app/Contents/MacOS/ImageJ"))
    imagej = ImageJMacroAdapter(imagej_path)

    # Resolve cellpose path relative to project root if it's a relative path
    cellpose_path_str = cfg.get("cellpose_path", cfg.get_nested("paths.cellpose") or "cellpose_venv/bin/python")
    if Path(cellpose_path_str).is_absolute():
        cellpose_python = Path(cellpose_path_str)
    else:
        cellpose_python = project_root / cellpose_path_str
    cellpose = CellposeSubprocessAdapter(cellpose_python)

    fs = LocalFileSystemAdapter()
    imgproc = PILImageProcessingAdapter()

    return Container(
        cfg=cfg,
        orchestrator=orchestrator,
        workflow=workflow,
        step_exec=step_exec,
        imagej=imagej,
        cellpose=cellpose,
        fs=fs,
        imgproc=imgproc,
    )


