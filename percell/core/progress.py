"""
Progress utilities built on alive-progress.

This module provides a small, reusable facade around alive-progress so any
part of the project can display consistent terminal progress bars and spinners
without depending directly on the third-party library.

Design goals:
- Decouple project code from alive-progress specifics
- Provide simple context managers and helper functions
- Support nested progress (task + subtasks) when needed
- Work well alongside existing logging in percell.core.logger
"""

from __future__ import annotations

from contextlib import contextmanager
from typing import Iterable, Iterator, Optional, Callable, Any, List, Dict
import subprocess
import time


try:
    # Import lazily to avoid import errors during environments without the dep
    from alive_progress import alive_bar, alive_it, config_handler
except Exception:  # pragma: no cover - handled at runtime if missing
    alive_bar = None  # type: ignore
    alive_it = None  # type: ignore
    config_handler = None  # type: ignore


def is_progress_available() -> bool:
    """Return True if alive-progress is importable."""
    return alive_bar is not None


def configure_global(
    spinner: Optional[str] = None,
    theme: Optional[str] = None,
    enrich_print: Optional[bool] = None,
    title_length: Optional[int] = None,
    unknown: Optional[str] = None,
) -> None:
    """
    Optionally configure alive-progress global behavior.

    Args:
        spinner: Name of spinner preset, e.g. 'dots', 'twirls'
        theme: Theme name, e.g. 'classic', 'smooth', 'rainbow'
        enrich_print: Whether to patch print for bar-friendly output
        title_length: Max title length in bar display
        unknown: Style name for unknown-total bars (e.g. 'smooth', 'triangles')
    """
    if config_handler is None:
        return
    # alive-progress exposes configuration via config_handler.set_global/reset
    kwargs = {}
    if spinner is not None:
        kwargs["spinner"] = spinner
    if theme is not None:
        kwargs["theme"] = theme
    if enrich_print is not None:
        kwargs["enrich_print"] = enrich_print
    if title_length is not None:
        kwargs["title_length"] = title_length
    if kwargs:
        try:
            config_handler.set_global(**kwargs)  # type: ignore[attr-defined]
        except Exception:
            # Don't break callers if the underlying API changes
            pass


@contextmanager
def progress_bar(
    total: Optional[int] = None,
    title: Optional[str] = None,
    unit: str = "items",
    manual: bool = False,
) -> Iterator[Callable[[int], None]]:
    """
    Context manager that yields an updater function for progress.

    Usage:
        with progress_bar(total=100, title="Processing") as update:
            for i in range(100):
                # work
                update(1)

    Args:
        total: Total steps; if None, a spinner is shown instead of a bar
        title: Optional title displayed to the left of the bar
        unit: Label for units (shown in bar suffix)
        manual: If True, caller controls increments; otherwise, updater is a no-op

    Returns:
        A callable update(delta: int) -> None that advances the bar
    """
    if alive_bar is None:
        # Fallback: provide a no-op updater
        def noop_update(_: int) -> None:
            return

        yield noop_update
        return

    # alive_bar supports total=None for spinner
    with alive_bar(total, title=title or "", manual=manual, force_tty=True) as bar:
        def update(delta: int = 1) -> None:
            try:
                if manual:
                    bar(delta)
                else:
                    # In automatic mode, alive-progress expects bar() with no args
                    bar()
            except Exception:
                # Avoid breaking the caller due to bar errors
                pass

        yield update


def iter_with_progress(
    iterable: Iterable[Any],
    total: Optional[int] = None,
    title: Optional[str] = None,
    enrich_items: bool = False,
) -> Iterable[Any]:
    """
    Wrap an iterable with a progress indicator.

    Args:
        iterable: Source iterable
        total: Total length; if None and iterable has __len__, it is inferred
        title: Optional title shown on the bar
        enrich_items: If True, show each item string representation as the bar text

    Returns:
        An iterator yielding the original items while showing progress
    """
    if alive_it is None:
        return iterable
    return alive_it(
        iterable,
        total=total,
        title=title or "",
        enrich_print=enrich_items,
        force_tty=True,
    )


@contextmanager
def spinner(title: Optional[str] = None) -> Iterator[None]:
    """
    A simple spinner when total is unknown.

    Usage:
        with spinner("Indexing files"):
            do_work()
    """
    if alive_bar is None:
        yield
        return
    with alive_bar(None, title=title or "", force_tty=True):
        yield



# Set a default spinner style globally across the application.
try:
    configure_global(spinner="it")
except Exception:
    # Safe to ignore if alive-progress is unavailable at import time
    pass


def run_subprocess_with_spinner(
    cmd: List[str],
    title: Optional[str] = None,
    capture_output: bool = True,
    text: bool = True,
    check: bool = False,
    env: Optional[Dict[str, str]] = None,
    cwd: Optional[str] = None,
    stdin: Any = None,
) -> subprocess.CompletedProcess:
    """
    Run a subprocess while showing a spinner until it finishes.

    Args:
        cmd: The command list to execute
        title: Spinner title to display
        capture_output: If True, capture stdout/stderr
        text: If True, decode output as text
        check: If True, raise on non-zero return code
        env: Optional environment variables
        cwd: Optional working directory
        stdin: Optional stdin to pass to process

    Returns:
        subprocess.CompletedProcess with stdout/stderr if captured
    """
    if alive_bar is None:
        return subprocess.run(
            cmd,
            capture_output=capture_output,
            text=text,
            check=check,
            env=env,
            cwd=cwd,
            stdin=stdin,
        )

    stdout_pipe = subprocess.PIPE if capture_output else None
    stderr_pipe = subprocess.PIPE if capture_output else None
    process = subprocess.Popen(
        cmd,
        stdout=stdout_pipe,
        stderr=stderr_pipe,
        text=text,
        env=env,
        cwd=cwd,
        stdin=stdin,
    )

    with spinner(title or "Running..."):
        while True:
            ret = process.poll()
            if ret is not None:
                break
            time.sleep(0.1)

    stdout, stderr = process.communicate()
    completed = subprocess.CompletedProcess(cmd, process.returncode, stdout=stdout, stderr=stderr)
    if check and completed.returncode != 0:
        raise subprocess.CalledProcessError(completed.returncode, cmd, output=stdout, stderr=stderr)
    return completed


