from __future__ import annotations

from contextlib import contextmanager
from typing import Callable, Iterator
import time
from threading import Thread, Event

from percell.ports.driven.progress_report_port import ProgressReportPort

try:
    from alive_progress import alive_bar
except ImportError:
    alive_bar = None


class ConsoleProgressAdapter(ProgressReportPort):
    """Adapter for console-based progress reporting using alive-progress library.

    Falls back to no-op implementations if alive-progress is not available.
    """

    @contextmanager
    def create_progress_bar(
        self,
        total: int,
        title: str,
        manual: bool = False
    ) -> Iterator[Callable[[int], None]]:
        """Create a progress bar using alive-progress or fallback to no-op."""
        if alive_bar is None:
            # Fallback: just print title and provide no-op update function
            if title:
                print(f"{title}")

            def noop_update(delta: int) -> None:
                pass

            yield noop_update
            return

        # Use alive-progress
        if title:
            print(f"{title}")

        with alive_bar(total=None, manual=manual, force_tty=True) as bar:
            def update(delta: int = 1) -> None:
                try:
                    if manual:
                        bar(delta)
                    else:
                        for _ in range(delta):
                            bar()
                except Exception:
                    pass

            yield update

    @contextmanager
    def create_spinner(self, title: str) -> Iterator[None]:
        """Display an indeterminate spinner using ASCII animation."""
        if title:
            print(f"{title}")

        frames = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
        stop_event = Event()

        def _spin() -> None:
            idx = 0
            try:
                while not stop_event.is_set():
                    frame = frames[idx % len(frames)]
                    print(f"\r{frame}", end="", flush=True)
                    idx += 1
                    time.sleep(0.1)
            except Exception:
                pass
            finally:
                print("\r ", end="\r", flush=True)

        spinner_thread = Thread(target=_spin, daemon=True)
        spinner_thread.start()

        try:
            yield
        finally:
            stop_event.set()
            spinner_thread.join(timeout=0.5)
