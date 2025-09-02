"""
Subprocess adapter implementing SubprocessPort.

This adapter provides concrete implementations for subprocess execution
with progress reporting capabilities.
"""

import subprocess
import os
from typing import List, Optional, Dict
from pathlib import Path

from percell.domain.ports import SubprocessPort, ProgressReporter
from percell.domain.exceptions import SubprocessError


class SubprocessAdapter(SubprocessPort):
    """Concrete implementation of SubprocessPort using subprocess module."""
    
    def __init__(self, progress_reporter: ProgressReporter):
        self.progress_reporter = progress_reporter
    
    def run_with_progress(
        self, 
        command: List[str], 
        title: Optional[str] = None,
        cwd: Optional[str] = None,
        env: Optional[Dict[str, str]] = None
    ) -> int:
        """Run a subprocess command with progress reporting."""
        try:
            # Start progress indicator
            if title:
                self.progress_reporter.start(title)
            
            # Run the subprocess
            result = subprocess.run(
                command,
                cwd=cwd,
                env=env,
                capture_output=True,
                text=True,
                check=False
            )
            
            # Stop progress indicator
            self.progress_reporter.stop()
            
            return result.returncode
            
        except Exception as e:
            self.progress_reporter.stop()
            raise SubprocessError(f"Failed to run command {command}: {str(e)}") from e
    
    def run_simple(
        self, 
        command: List[str],
        cwd: Optional[str] = None,
        env: Optional[Dict[str, str]] = None
    ) -> int:
        """Run a subprocess command without progress reporting."""
        try:
            result = subprocess.run(
                command,
                cwd=cwd,
                env=env,
                capture_output=True,
                text=True,
                check=False
            )
            return result.returncode
            
        except Exception as e:
            raise SubprocessError(f"Failed to run command {command}: {str(e)}") from e
