"""
Logging adapter for the Percell infrastructure layer.

This module provides a concrete implementation of the LoggingPort
using the infrastructure logging utilities.
"""

from __future__ import annotations

from typing import Any, Optional
import tempfile
from pathlib import Path

from percell.domain.ports import LoggingPort
from percell.infrastructure.logging.logger import PipelineLogger


class LoggingAdapter(LoggingPort):
    """
    Logging adapter implementing the LoggingPort interface.
    
    Provides logging functionality using the infrastructure
    logging utilities.
    """
    
    def __init__(self, output_dir: Optional[str] = None, log_level: str = "INFO"):
        """
        Initialize the logging adapter.
        
        Args:
            output_dir: Directory for log files. If None, uses temp directory.
            log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        """
        if output_dir is None:
            # Use temporary directory for testing/development
            output_dir = tempfile.mkdtemp(prefix="percell_logs_")
        
        self.output_dir = output_dir
        self.log_level = log_level
        self._loggers: dict[str, Any] = {}
        self._pipeline_logger: PipelineLogger | None = None
    
    def get_logger(self, name: str) -> Any:
        """
        Get a logger instance.
        
        Args:
            name: Name of the logger
            
        Returns:
            Logger instance
        """
        if name not in self._loggers:
            self._loggers[name] = self.create_logger(name)
        return self._loggers[name]
    
    def create_logger(self, name: str, level: Optional[str] = None) -> Any:
        """
        Create a new logger instance.
        
        Args:
            name: Name of the logger
            level: Logging level (optional)
            
        Returns:
            New logger instance
        """
        # For now, return a simple logger that uses the pipeline logger
        # This can be enhanced later with more sophisticated logging
        if self._pipeline_logger is None:
            self._pipeline_logger = PipelineLogger(
                output_dir=self.output_dir,
                log_level=level or self.log_level
            )
        
        # Create a simple logger that delegates to the pipeline logger
        class SimpleLogger:
            def __init__(self, name: str, pipeline_logger: PipelineLogger):
                self.name = name
                self.pipeline_logger = pipeline_logger
            
            def info(self, message: str) -> None:
                self.pipeline_logger.logger.info(f"[{self.name}] {message}")
            
            def warning(self, message: str) -> None:
                self.pipeline_logger.logger.warning(f"[{self.name}] {message}")
            
            def error(self, message: str) -> None:
                self.pipeline_logger.logger.error(f"[{self.name}] {message}")
            
            def debug(self, message: str) -> None:
                self.pipeline_logger.logger.debug(f"[{self.name}] {message}")
            
            def setLevel(self, level: str) -> None:
                # This is a simple implementation - in practice, you might want
                # to handle this differently
                pass
        
        return SimpleLogger(name, self._pipeline_logger)
    
    def log_info(self, message: str) -> None:
        """
        Log an info message.
        
        Args:
            message: Message to log
        """
        logger = self.get_logger("default")
        logger.info(message)
    
    def log_warning(self, message: str) -> None:
        """
        Log a warning message.
        
        Args:
            message: Message to log
        """
        logger = self.get_logger("default")
        logger.warning(message)
    
    def log_error(self, message: str) -> None:
        """
        Log an error message.
        
        Args:
            message: Message to log
        """
        logger = self.get_logger("default")
        logger.error(message)
    
    def log_debug(self, message: str) -> None:
        """
        Log a debug message.
        
        Args:
            message: Message to log
        """
        logger = self.get_logger("default")
        logger.debug(message)
