from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import logging

from percell.domain.services.configuration_service import create_configuration_service, ConfigurationService
from percell.application.workflow_coordinator import WorkflowCoordinator
from percell.application.step_execution_coordinator import StepExecutionCoordinator
from percell.domain.services.workflow_orchestration_service import WorkflowOrchestrationService
from percell.adapters.imagej_macro_adapter import ImageJMacroAdapter
from percell.adapters.cellpose_subprocess_adapter import CellposeSubprocessAdapter
from percell.adapters.cellpose_conda_adapter import CellposeCondaAdapter
from percell.adapters.local_filesystem_adapter import LocalFileSystemAdapter
from percell.adapters.pil_image_processing_adapter import PILImageProcessingAdapter
from percell.adapters.console_progress_adapter import ConsoleProgressAdapter
from percell.domain.exceptions import ConfigurationError
from percell.ports.driven.cellpose_integration_port import CellposeIntegrationPort

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class Container:
    cfg: ConfigurationService
    orchestrator: WorkflowOrchestrationService
    workflow: WorkflowCoordinator
    step_exec: StepExecutionCoordinator
    imagej: ImageJMacroAdapter
    cellpose: CellposeIntegrationPort
    fs: LocalFileSystemAdapter
    imgproc: PILImageProcessingAdapter


def build_container(config_path: Path) -> Container:
    """Build and configure the application container with proper error handling.

    Args:
        config_path: Path to the configuration file

    Returns:
        Configured Container instance

    Raises:
        ConfigurationError: If configuration cannot be loaded or is invalid
    """
    try:
        # Create configuration service with proper error handling
        cfg = create_configuration_service(config_path, create_if_missing=True)
        logger.info(f"Loaded configuration from {config_path}")

        orchestrator = WorkflowOrchestrationService()
        workflow = WorkflowCoordinator(orchestrator=orchestrator)
        step_exec = StepExecutionCoordinator()

        # Create progress reporter adapter
        progress_reporter = ConsoleProgressAdapter()

        # Get project root for resolving relative paths to external resources
        from percell.application.paths_api import get_path_config
        project_root = get_path_config().get_project_root()

        # Get ImageJ path with unified dot-notation access
        imagej_path = Path(cfg.get("imagej_path") or
                          cfg.get("paths.imagej") or
                          "/Applications/ImageJ.app/Contents/MacOS/ImageJ")
        imagej = ImageJMacroAdapter(imagej_path, progress_reporter)

        # Determine cellpose adapter type based on configuration
        cellpose_type = cfg.get("cellpose_type") or "subprocess"

        if cellpose_type == "conda":
            # Use conda adapter for conda-based cellpose installations
            conda_env_name = cfg.get("cellpose_conda_env") or "cellpose_env"
            conda_path_str = cfg.get("conda_path")
            conda_path = Path(conda_path_str) if conda_path_str else None
            cellpose = CellposeCondaAdapter(conda_env_name, conda_path)
            logger.info(
                f"Using CellposeCondaAdapter with env: {conda_env_name}"
            )
        else:
            # Use subprocess adapter (default)
            cellpose_python = (
                cfg.get_resolved_path("cellpose_path", project_root) or
                cfg.get_resolved_path("paths.cellpose", project_root) or
                project_root / "cellpose_venv/bin/python"
            )
            cellpose = CellposeSubprocessAdapter(cellpose_python)
            logger.info(
                f"Using CellposeSubprocessAdapter with python: "
                f"{cellpose_python}"
            )

        fs = LocalFileSystemAdapter()
        imgproc = PILImageProcessingAdapter()

        logger.info("Successfully built application container")
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

    except ConfigurationError:
        logger.error(f"Failed to build container: configuration error with {config_path}")
        raise
    except Exception as e:
        error_msg = f"Failed to build container: {e}"
        logger.error(error_msg)
        raise ConfigurationError(error_msg) from e


