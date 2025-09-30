from __future__ import annotations

"""Application-level Pipeline API."""

import argparse
from pathlib import Path
from typing import Dict, List, Any, Optional

from percell.domain.services.configuration_service import (
    ConfigurationService,
    create_configuration_service
)
from percell.application.logger_api import PipelineLogger
from percell.application.stages_api import get_stage_registry, StageExecutor


class Pipeline:
    def __init__(
        self,
        config: Config,
        logger: PipelineLogger,
        args: argparse.Namespace,
        ports: Optional[Dict[str, Any]] = None,
    ):
        self.config = config
        self.logger = logger
        self.args = args
        self.ports: Dict[str, Any] = ports or {}

        self.setup_directories()

        self.registry = get_stage_registry()
        self.executor = StageExecutor(config, logger, self.registry, ports=self.ports)

        self.stages_to_run = self._determine_stages()

    def setup_directories(self) -> None:
        logs_dir = Path(self.args.output) / "logs"
        logs_dir.mkdir(parents=True, exist_ok=True)
        self.logger.debug(f"Created directory: {logs_dir}")

        needed_dirs = {"preprocessed": Path(self.args.output) / "preprocessed", "logs": logs_dir}
        for name, path in needed_dirs.items():
            if name != "logs":
                path.mkdir(parents=True, exist_ok=True)
                self.logger.debug(f"Created directory: {path}")
        self.directories = needed_dirs

    def _determine_stages(self) -> List[str]:
        stages: List[str] = []
        if self.args.complete_workflow:
            stages.append("complete_workflow")
            return stages
        if getattr(self.args, "advanced_workflow", False):
            stages.append("advanced_workflow")
            return stages
        if self.args.data_selection:
            stages.append("data_selection")
        if self.args.segmentation:
            stages.append("segmentation")
        if self.args.process_single_cell:
            stages.append("process_single_cell")
        if self.args.threshold_grouped_cells:
            stages.append("threshold_grouped_cells")
        if self.args.measure_roi_area:
            stages.append("measure_roi_area")
        if self.args.analysis:
            stages.append("analysis")
        if self.args.cleanup:
            stages.append("cleanup")
        if self.args.skip_steps:
            stages = [s for s in stages if s not in self.args.skip_steps]
        if self.args.start_from:
            try:
                idx = stages.index(self.args.start_from)
                stages = stages[idx:]
            except ValueError:
                self.logger.warning(f"Start stage '{self.args.start_from}' not found in pipeline")
        return stages

    def get_pipeline_arguments(self) -> Dict[str, Any]:
        return {
            "input_dir": self.args.input,
            "output_dir": self.args.output,
            "datatype": self.args.datatype,
            "conditions": self.args.conditions,
            "timepoints": self.args.timepoints,
            "regions": self.args.regions,
            "segmentation_channel": self.args.segmentation_channel,
            "analysis_channels": self.args.analysis_channels,
            "bins": self.args.bins,
            "directories": self.directories,
        }

    def run(self) -> bool:
        try:
            self.logger.info("Starting microscopy single-cell analysis pipeline")
            self.logger.info(f"Stages to run: {', '.join(self.stages_to_run)}")
            args = self.get_pipeline_arguments()
            success = self.executor.execute_stages(self.stages_to_run, **args)
            if success:
                self.logger.info("Pipeline completed successfully")
                self.logger.save_execution_summary()
                summary = self.executor.get_execution_summary()
                self.logger.info(f"Execution summary:")
                self.logger.info(f"  Total stages: {summary['total_stages']}")
                self.logger.info(f"  Successful: {summary['successful_stages']}")
                self.logger.info(f"  Failed: {summary['failed_stages']}")
                self.logger.info(f"  Success rate: {summary['success_rate']:.1%}")
                self.logger.info(f"  Total duration: {summary['total_duration']:.2f}s")
            else:
                self.logger.error("Pipeline failed")
            return success
        except Exception as e:
            self.logger.error(f"Pipeline execution error: {e}")
            return False

    def get_available_stages(self) -> List[str]:
        return self.registry.get_available_stages()

    def get_stage_order(self) -> List[str]:
        return self.registry.get_stage_order()


def create_pipeline(config: Config, logger: PipelineLogger, args: argparse.Namespace) -> Pipeline:
    return Pipeline(config, logger, args)


