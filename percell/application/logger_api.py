from __future__ import annotations

"""Application-level logging API compatible with legacy core.logger exports."""

import json
import logging
import sys
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Dict, Any


class PipelineLogger:
    def __init__(self, output_dir: str, log_level: str = "INFO", log_to_file: bool = True, log_to_console: bool = True):
        self.output_dir = Path(output_dir)
        self.log_level = getattr(logging, log_level.upper())
        self.log_to_file = log_to_file
        self.log_to_console = log_to_console

        self.logs_dir = self.output_dir / "logs"
        self.logs_dir.mkdir(parents=True, exist_ok=True)

        self._setup_logging()
        self.execution_stats: Dict[str, Any] = {
            "start_time": datetime.now().isoformat(),
            "stages_completed": [],
            "stages_failed": [],
            "total_duration": 0.0,
        }

    def _setup_logging(self) -> None:
        detailed_formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
        console_formatter = logging.Formatter("%(levelname)s - %(name)s - %(message)s")

        handlers = []
        if self.log_to_console:
            ch = logging.StreamHandler(sys.stdout)
            ch.setFormatter(console_formatter)
            ch.setLevel(self.log_level)
            handlers.append(ch)
        if self.log_to_file:
            main_log = self.logs_dir / f"microscopy_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
            fh = logging.FileHandler(main_log)
            fh.setFormatter(detailed_formatter)
            fh.setLevel(self.log_level)
            handlers.append(fh)

            err_log = self.logs_dir / f"errors_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
            eh = logging.FileHandler(err_log)
            eh.setFormatter(detailed_formatter)
            eh.setLevel(logging.ERROR)
            handlers.append(eh)

        logging.basicConfig(level=self.log_level, handlers=handlers, force=True)
        self.logger = logging.getLogger("MicroscopyPipeline")
        self.logger.info(f"Pipeline logger initialized. Output directory: {self.output_dir}")

    def info(self, message: str) -> None:
        self.logger.info(message)

    def debug(self, message: str) -> None:
        self.logger.debug(message)

    def warning(self, message: str) -> None:
        self.logger.warning(message)

    def error(self, message: str) -> None:
        self.logger.error(message)

    def critical(self, message: str) -> None:
        self.logger.critical(message)

    def log_stage_start(self, stage_name: str) -> None:
        self.info(f"Starting stage: {stage_name}")

    def log_stage_complete(self, stage_name: str, duration: float) -> None:
        self.info(f"Completed stage: {stage_name} (duration: {duration:.2f}s)")
        self.execution_stats["stages_completed"].append({
            "stage": stage_name,
            "duration": duration,
            "timestamp": datetime.now().isoformat(),
        })

    def log_stage_failed(self, stage_name: str, error: str) -> None:
        self.error(f"Failed stage: {stage_name} - {error}")
        self.execution_stats["stages_failed"].append({
            "stage": stage_name,
            "error": error,
            "timestamp": datetime.now().isoformat(),
        })

    def save_execution_summary(self) -> None:
        self.execution_stats["end_time"] = datetime.now().isoformat()
        summary_file = self.logs_dir / f"execution_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        summary_file.write_text(json.dumps(self.execution_stats, indent=2), encoding="utf-8")
        self.info(f"Execution summary saved to: {summary_file}")


class ModuleLogger:
    def __init__(self, module_name: str, pipeline_logger: PipelineLogger):
        self.module_name = module_name
        self.pipeline_logger = pipeline_logger
        self.logger = logging.getLogger(f"MicroscopyPipeline.{module_name}")

    def info(self, message: str) -> None:
        self.logger.info(message)

    def debug(self, message: str) -> None:
        self.logger.debug(message)

    def warning(self, message: str) -> None:
        self.logger.warning(message)

    def error(self, message: str) -> None:
        self.logger.error(message)

    def critical(self, message: str) -> None:
        self.logger.critical(message)

    def log_progress(self, current: int, total: int, description: str = "") -> None:
        percentage = (current / total) * 100 if total > 0 else 0
        msg = f"Progress: {current}/{total} ({percentage:.1f}%)"
        if description:
            msg += f" - {description}"
        self.info(msg)

    def log_file_processed(self, file_path: str, success: bool = True) -> None:
        status = "SUCCESS" if success else "FAILED"
        self.info(f"File processed: {file_path} - {status}")


def create_logger(output_dir: str, **kwargs) -> PipelineLogger:
    return PipelineLogger(output_dir, **kwargs)


