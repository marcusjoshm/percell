from __future__ import annotations

import subprocess
import logging
from pathlib import Path
import re
from typing import List, Optional

from ..ports.driven.imagej_integration_port import ImageJIntegrationPort
from ..ports.driven.progress_report_port import ProgressReportPort
from percell.domain.exceptions import ImageJError, FileSystemError

logger = logging.getLogger(__name__)


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

    def run_macro(self, macro_path: Path, args: List[str]) -> int:
        # Use -macro without --headless to enable ROI Manager support
        # setBatchMode(true) in the macro will hide the GUI
        cmd: List[str] = [str(self._exe), "-macro", str(macro_path)]
        if args:
            # ImageJ -macro takes only a single string parameter;
            # join args appropriately if needed
            # Many macros handle a single arg;
            # callers can pre-serialize if required
            cmd.append(" ".join(args))

        try:
            # Start process with piped stdout to stream lines
            # Use temp directory as cwd to avoid "getcwd" errors
            import tempfile
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                cwd=tempfile.gettempdir(),
            )
            title = f"ImageJ: {Path(macro_path).stem}"
            print(title)

            # Phase 1: stream lines until we know total, printing logs
            total: Optional[int] = None
            while True:
                line = (
                    process.stdout.readline() if process.stdout else ""
                )
                if not line:
                    if process.poll() is not None:
                        break
                    continue
                stripped = line.strip()
                print(line.rstrip())
                # Generic TOTAL detector, e.g. RESIZE_TOTAL: N,
                # EXTRACT_TOTAL: N,
                # CREATE_TOTAL: N, ANALYZE_TOTAL: N, MEASURE_TOTAL: N
                m_total = re.match(r"^[A-Z_]+_TOTAL:\s*(\d+)$", stripped)
                if m_total:
                    try:
                        total = int(m_total.group(1))
                    except (ValueError, IndexError) as e:
                        logger.warning(f"Failed to parse ImageJ total count: {e}")
                        total = None
                    break

            # Phase 2: if we have a total, open a determinate bar
            # while still printing logs
            if total and total > 0 and process.poll() is None and self._progress:
                with self._progress.create_progress_bar(
                    total=total, title=title, manual=True
                ) as update:
                    progressed = 0
                    while True:
                        line = (
                            process.stdout.readline() if process.stdout else ""
                        )
                        if not line:
                            if process.poll() is not None:
                                break
                            continue
                        stripped = line.strip()
                        print(line.rstrip())
                        # Generic progress markers: *_ROI, *_CELL, *_MASK, *_FILE with formats like X/Y or just X
                        m_prog = re.match(r"^[A-Z_]+_(ROI|CELL|MASK|FILE):\s*(\d+)(?:/(\d+))?", stripped)
                        if m_prog:
                            try:
                                current = int(m_prog.group(2))
                                # If macro prints absolute current, advance delta; otherwise, step by 1
                                if current > progressed:
                                    delta = current - progressed
                                    for _ in range(delta):
                                        update(1)
                                    progressed = current
                                else:
                                    update(1)
                                    progressed += 1
                            except (ValueError, IndexError) as e:
                                logger.debug(f"Failed to parse ImageJ progress: {e}")
                                update(1)
                                progressed += 1
                    # ensure bar completes if macro finished early without full markers
                    remaining = (total - progressed) if total and progressed < total else 0
                    for _ in range(remaining):
                        update(1)
            elif total and total > 0 and process.poll() is None:
                # Fallback: no progress reporter, just continue reading output
                while True:
                    line = (
                        process.stdout.readline() if process.stdout else ""
                    )
                    if not line:
                        if process.poll() is not None:
                            break
                        continue
                    print(line.rstrip())

            # Finalize
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
