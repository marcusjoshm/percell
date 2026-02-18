from __future__ import annotations

import glob
import os
import queue
import subprocess
import logging
import tempfile
import threading
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

# Sentinel value to signal the reader thread has finished
_SENTINEL = object()

# Macro completion marker printed by every .ijm macro as its last
# meaningful output line.  The adapter watches for this to know
# that the macro's work is done (even if the JVM hangs afterwards).
MACRO_DONE_SENTINEL = "MACRO_DONE"


class ImageJMacroAdapter(ImageJIntegrationPort):
    """Adapter for executing ImageJ macros via the command line.

    This adapter is responsible only for process execution. Higher layers
    decide what macro to run and how to interpret results.
    """

    # Seconds to wait for additional output *after* the MACRO_DONE
    # sentinel has been seen.  This is kept short because once the
    # sentinel arrives, the macro's work is definitively done and we
    # only need to give the JVM a moment to shut down gracefully
    # (on Windows the JVM often hangs and must be force-killed).
    _POST_SENTINEL_GRACE = 3

    def __init__(
        self,
        imagej_executable: Path,
        progress_reporter: Optional[ProgressReportPort] = None
    ) -> None:
        self._exe = Path(imagej_executable)
        self._progress = progress_reporter
        self._output_queue: queue.Queue = queue.Queue()
        self._force_killed = False
        self._sentinel_seen = False

    @staticmethod
    def _cleanup_imagej_stubs() -> None:
        """Remove stale ImageJ stub files from the temp directory.

        On Windows, ImageJ creates ``ImageJ-*.stub`` files for single-instance
        communication. If ImageJ doesn't exit cleanly (e.g. force-killed),
        these files persist and block subsequent launches with the error
        "Could not connect to existing ImageJ instance".
        """
        temp_dir = tempfile.gettempdir()
        for stub in glob.glob(os.path.join(temp_dir, "ImageJ-*.stub")):
            try:
                os.remove(stub)
                logger.debug("Removed stale ImageJ stub file: %s", stub)
            except OSError:
                pass

    def _start_output_reader(self, process: subprocess.Popen) -> None:
        """Start a daemon thread that reads process stdout into a queue.

        This decouples reading from the pipe (which can block indefinitely
        on Windows if ImageJ hangs) from the main thread, allowing us to
        apply a timeout via ``queue.get(timeout=...)``.
        """
        self._output_queue = queue.Queue()

        def worker() -> None:
            try:
                while True:
                    line = process.stdout.readline()
                    if not line:
                        break
                    self._output_queue.put(line)
            except (ValueError, OSError):
                # Pipe closed or process killed
                pass
            finally:
                self._output_queue.put(_SENTINEL)

        t = threading.Thread(target=worker, daemon=True)
        t.start()

    def _read_line(self, process: subprocess.Popen) -> Optional[str]:
        """Read a line from the output queue.

        Before ``MACRO_DONE`` is seen, blocks indefinitely — the reader
        thread will push ``_SENTINEL`` when the process exits or its
        stdout closes, which unblocks this call.  After the sentinel,
        uses a short grace period before force-killing the JVM (handles
        Windows where the JVM often hangs after macro completion).
        """
        timeout = self._POST_SENTINEL_GRACE if self._sentinel_seen else None
        try:
            line = self._output_queue.get(timeout=timeout)
            if line is _SENTINEL:
                return None
            # Check for the macro-done sentinel
            if line.strip() == MACRO_DONE_SENTINEL:
                self._sentinel_seen = True
                logger.debug("MACRO_DONE sentinel received")
            return line
        except queue.Empty:
            # Only reachable after sentinel (timeout=None never raises)
            logger.info(
                "Macro completed (sentinel seen); no further output "
                "for %d s — force-killing hung JVM",
                self._POST_SENTINEL_GRACE,
            )
            self._force_killed = True
            try:
                process.kill()
            except OSError:
                pass
            return None

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
        self._force_killed = False
        self._sentinel_seen = False

        # Remove stale stub files that would block ImageJ from starting
        self._cleanup_imagej_stubs()

        try:
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                cwd=tempfile.gettempdir(),
            )

            # Read output via a background thread so we can apply a timeout
            self._start_output_reader(process)

            title = f"ImageJ: {Path(macro_path).stem}"
            self._handle_process_output(process, title)

            # Wait for process to exit.  If sentinel was seen the macro
            # finished; give the JVM a short window then force-kill.
            # Otherwise the process should already be gone (stdout closed).
            if self._sentinel_seen and not self._force_killed:
                try:
                    process.wait(timeout=self._POST_SENTINEL_GRACE)
                except subprocess.TimeoutExpired:
                    logger.info(
                        "ImageJ JVM did not exit within %d s after "
                        "MACRO_DONE — force-killing",
                        self._POST_SENTINEL_GRACE,
                    )
                    self._force_killed = True
                    process.kill()
                    process.wait()
            else:
                process.wait()

            return_code = process.returncode

            # If we had to force-kill a hung ImageJ, treat as success
            # ONLY when the MACRO_DONE sentinel was seen (macro
            # definitively completed its work before the JVM hung).
            if self._force_killed:
                if self._sentinel_seen:
                    logger.info(
                        "ImageJ was force-killed after MACRO_DONE "
                        "(exit code %d treated as success)",
                        return_code,
                    )
                    return 0
                else:
                    error_msg = (
                        "ImageJ was force-killed and MACRO_DONE was "
                        "never received — macro did not complete"
                    )
                    logger.error(error_msg)
                    raise ImageJError(error_msg, return_code)

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

        finally:
            # Clean up stub files again in case ImageJ was killed
            self._cleanup_imagej_stubs()
