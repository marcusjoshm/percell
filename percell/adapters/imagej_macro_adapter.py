from __future__ import annotations

import subprocess
import logging
import tempfile
from pathlib import Path
import re
from typing import List, Optional, Tuple, Callable

from ..ports.driven.imagej_integration_port import ImageJIntegrationPort
from ..ports.driven.progress_report_port import ProgressReportPort
from percell.domain.exceptions import ImageJError, FileSystemError

logger = logging.getLogger(__name__)

# Regex patterns for parsing ImageJ output
TOTAL_PATTERN = re.compile(r"^[A-Z_]+_TOTAL:\s*(\d+)$")
PROGRESS_PATTERN = re.compile(r"^[A-Z_]+_(ROI|CELL|MASK|FILE):\s*(\d+)(?:/(\d+))?")


class ImageJMacroAdapter(ImageJIntegrationPort):
    """Adapter for executing ImageJ macros via the command line.

    This adapter is responsible only for process execution. Higher layers
    decide what macro to run and how to interpret results.
    """

    def __init__(
        self,
        imagej_executable: Path,
        progress_reporter: Optional[ProgressReportPort] = None
    ) -> None:
        self._exe = Path(imagej_executable)
        self._progress = progress_reporter

    def _read_line(self, process: subprocess.Popen) -> Optional[str]:
        """Read a line from process stdout, returning None if process ended."""
        line = process.stdout.readline() if process.stdout else ""
        if not line:
            return None if process.poll() is not None else ""
        return line

    def _parse_total(self, line: str) -> Optional[int]:
        """Parse total count from a TOTAL marker line."""
        match = TOTAL_PATTERN.match(line.strip())
        if match:
            try:
                return int(match.group(1))
            except (ValueError, IndexError) as e:
                logger.warning(f"Failed to parse ImageJ total count: {e}")
        return None

    def _parse_progress(self, line: str) -> Optional[int]:
        """Parse current progress from a progress marker line."""
        match = PROGRESS_PATTERN.match(line.strip())
        if match:
            try:
                return int(match.group(2))
            except (ValueError, IndexError):
                pass
        return None

    def _stream_until_total(self, process: subprocess.Popen) -> Optional[int]:
        """Stream output lines until a TOTAL marker is found or process ends."""
        while True:
            line = self._read_line(process)
            if line is None:
                return None
            if line == "":
                continue
            print(line.rstrip())
            total = self._parse_total(line)
            if total is not None:
                return total

    def _stream_with_progress(
        self,
        process: subprocess.Popen,
        total: int,
        update: Callable[[int], None]
    ) -> None:
        """Stream output with progress bar updates."""
        progressed = 0
        while True:
            line = self._read_line(process)
            if line is None:
                break
            if line == "":
                continue
            print(line.rstrip())
            current = self._parse_progress(line)
            if current is not None:
                progressed = self._update_progress(current, progressed, update)

        # Ensure bar completes if macro finished early
        remaining = max(0, total - progressed)
        for _ in range(remaining):
            update(1)

    def _update_progress(
        self,
        current: int,
        progressed: int,
        update: Callable[[int], None]
    ) -> int:
        """Update progress bar and return new progressed count."""
        if current > progressed:
            delta = current - progressed
            for _ in range(delta):
                update(1)
            return current
        update(1)
        return progressed + 1

    def _stream_without_progress(self, process: subprocess.Popen) -> None:
        """Stream output without progress tracking."""
        while True:
            line = self._read_line(process)
            if line is None:
                break
            if line == "":
                continue
            print(line.rstrip())

    def _build_command(self, macro_path: Path, args: List[str]) -> List[str]:
        """Build the ImageJ command line."""
        cmd: List[str] = [str(self._exe), "-macro", str(macro_path)]
        if args:
            cmd.append(" ".join(args))
        return cmd

    def _handle_process_output(
        self,
        process: subprocess.Popen,
        title: str
    ) -> None:
        """Handle streaming process output with optional progress reporting."""
        print(title)
        total = self._stream_until_total(process)

        if not total or total <= 0 or process.poll() is not None:
            return

        if self._progress:
            with self._progress.create_progress_bar(
                total=total, title=title, manual=True
            ) as update:
                self._stream_with_progress(process, total, update)
        else:
            self._stream_without_progress(process)

    def run_macro(self, macro_path: Path, args: List[str]) -> int:
        """Execute an ImageJ macro and return the exit code."""
        cmd = self._build_command(macro_path, args)

        try:
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                cwd=tempfile.gettempdir(),
            )
            title = f"ImageJ: {Path(macro_path).stem}"
            self._handle_process_output(process, title)

            process.wait()
            return_code = process.returncode

            if return_code != 0:
                error_msg = f"ImageJ macro execution failed with return code {return_code}"
                logger.error(error_msg)
                raise ImageJError(error_msg, return_code)

            return return_code

        except FileNotFoundError as e:
            error_msg = f"ImageJ executable not found: {self._exe}"
            logger.error(error_msg)
            raise FileSystemError(error_msg) from e

        except subprocess.SubprocessError as e:
            error_msg = f"ImageJ subprocess error: {e}"
            logger.error(error_msg)
            raise ImageJError(error_msg) from e

        except OSError as e:
            error_msg = f"System error running ImageJ: {e}"
            logger.error(error_msg)
            raise ImageJError(error_msg) from e
