"""
Logging Framework for Microscopy Single-Cell Analysis Pipeline

Provides comprehensive logging functionality for the microscopy analysis pipeline.
"""

import logging
import sys
import os
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime
import json


class PipelineLogger:
    """
    Main pipeline logger for microscopy analysis.
    
    Handles logging configuration, file output, and console formatting.
    """
    
    def __init__(self, output_dir: str, log_level: str = "INFO", 
                 log_to_file: bool = True, log_to_console: bool = True):
        """
        Initialize the pipeline logger.
        
        Args:
            output_dir: Directory for log files
            log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
            log_to_file: Whether to log to file
            log_to_console: Whether to log to console
        """
        self.output_dir = Path(output_dir)
        self.log_level = getattr(logging, log_level.upper())
        self.log_to_file = log_to_file
        self.log_to_console = log_to_console
        
        # Create logs directory
        self.logs_dir = self.output_dir / "logs"
        self.logs_dir.mkdir(parents=True, exist_ok=True)
        
        # Setup logging
        self._setup_logging()
        
        # Track execution statistics
        self.execution_stats = {
            'start_time': datetime.now().isoformat(),
            'stages_completed': [],
            'stages_failed': [],
            'total_duration': 0.0
        }
    
    def _setup_logging(self) -> None:
        """Set up logging configuration."""
        # Create formatters
        detailed_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        console_formatter = logging.Formatter(
            '%(levelname)s - %(name)s - %(message)s'
        )
        
        # Create handlers
        handlers = []
        
        if self.log_to_console:
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setFormatter(console_formatter)
            console_handler.setLevel(self.log_level)
            handlers.append(console_handler)
        
        if self.log_to_file:
            # Main log file
            main_log_file = self.logs_dir / f"microscopy_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
            file_handler = logging.FileHandler(main_log_file)
            file_handler.setFormatter(detailed_formatter)
            file_handler.setLevel(self.log_level)
            handlers.append(file_handler)
            
            # Error log file
            error_log_file = self.logs_dir / f"errors_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
            error_handler = logging.FileHandler(error_log_file)
            error_handler.setFormatter(detailed_formatter)
            error_handler.setLevel(logging.ERROR)
            handlers.append(error_handler)
        
        # Configure root logger
        logging.basicConfig(
            level=self.log_level,
            handlers=handlers,
            force=True
        )
        
        # Create pipeline logger
        self.logger = logging.getLogger('MicroscopyPipeline')
        self.logger.info(f"Pipeline logger initialized. Output directory: {self.output_dir}")
    
    def info(self, message: str) -> None:
        """Log info message."""
        self.logger.info(message)
    
    def debug(self, message: str) -> None:
        """Log debug message."""
        self.logger.debug(message)
    
    def warning(self, message: str) -> None:
        """Log warning message."""
        self.logger.warning(message)
    
    def error(self, message: str) -> None:
        """Log error message."""
        self.logger.error(message)
    
    def critical(self, message: str) -> None:
        """Log critical message."""
        self.logger.critical(message)
    
    def log_stage_start(self, stage_name: str) -> None:
        """Log stage start."""
        self.info(f"Starting stage: {stage_name}")
    
    def log_stage_complete(self, stage_name: str, duration: float) -> None:
        """Log stage completion."""
        self.info(f"Completed stage: {stage_name} (duration: {duration:.2f}s)")
        self.execution_stats['stages_completed'].append({
            'stage': stage_name,
            'duration': duration,
            'timestamp': datetime.now().isoformat()
        })
    
    def log_stage_failed(self, stage_name: str, error: str) -> None:
        """Log stage failure."""
        self.error(f"Failed stage: {stage_name} - {error}")
        self.execution_stats['stages_failed'].append({
            'stage': stage_name,
            'error': error,
            'timestamp': datetime.now().isoformat()
        })
    
    def save_execution_summary(self) -> None:
        """Save execution summary to JSON file."""
        self.execution_stats['end_time'] = datetime.now().isoformat()
        
        summary_file = self.logs_dir / f"execution_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(summary_file, 'w') as f:
            json.dump(self.execution_stats, f, indent=2)
        
        self.info(f"Execution summary saved to: {summary_file}")


class ModuleLogger:
    """
    Logger for individual pipeline modules/stages.
    
    Provides module-specific logging with consistent formatting.
    """
    
    def __init__(self, module_name: str, pipeline_logger: PipelineLogger):
        """
        Initialize module logger.
        
        Args:
            module_name: Name of the module/stage
            pipeline_logger: Parent pipeline logger
        """
        self.module_name = module_name
        self.pipeline_logger = pipeline_logger
        self.logger = logging.getLogger(f'MicroscopyPipeline.{module_name}')
    
    def info(self, message: str) -> None:
        """Log info message."""
        self.logger.info(message)
    
    def debug(self, message: str) -> None:
        """Log debug message."""
        self.logger.debug(message)
    
    def warning(self, message: str) -> None:
        """Log warning message."""
        self.logger.warning(message)
    
    def error(self, message: str) -> None:
        """Log error message."""
        self.logger.error(message)
    
    def critical(self, message: str) -> None:
        """Log critical message."""
        self.logger.critical(message)
    
    def log_progress(self, current: int, total: int, description: str = "") -> None:
        """Log progress information."""
        percentage = (current / total) * 100 if total > 0 else 0
        message = f"Progress: {current}/{total} ({percentage:.1f}%)"
        if description:
            message += f" - {description}"
        self.info(message)
    
    def log_file_processed(self, file_path: str, success: bool = True) -> None:
        """Log file processing result."""
        status = "SUCCESS" if success else "FAILED"
        self.info(f"File processed: {file_path} - {status}")


def create_logger(output_dir: str, **kwargs) -> PipelineLogger:
    """
    Create a pipeline logger instance.
    
    Args:
        output_dir: Directory for log files
        **kwargs: Additional logger configuration
        
    Returns:
        Configured pipeline logger
    """
    return PipelineLogger(output_dir, **kwargs) 