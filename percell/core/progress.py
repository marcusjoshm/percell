"""
Progress utilities built on alive-progress.

This module provides a small, reusable facade around alive-progress so any
part of the project can display consistent terminal progress bars and spinners
without depending directly on the third-party library.

Design goals:
- Decouple project code from alive-progress specifics
- Provide simple context managers and helper functions
- Support nested progress (task + subtasks) when needed
- Work well alongside logging via percell.application.logger_api
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
    
    For 80x24 terminal compatibility, this always shows a spinner instead of a bar.

    Usage:
        with progress_bar(total=100, title="Processing") as update:
            for i in range(100):
                # work
                update(1)

    Args:
        total: Total steps; ignored (always shows spinner for compact display)
        title: Optional title displayed to the left of the spinner
        unit: Label for units (ignored for spinner display)
        manual: If True, caller controls increments; otherwise, updater is a no-op

    Returns:
        A callable update(delta: int) -> None that advances the spinner
    """
    if alive_bar is None:
        # Fallback: provide a no-op updater
        def noop_update(_: int) -> None:
            return

        yield noop_update
        return

    # Always use spinner (total=None) for compact 80x24 terminal display
    # Print title separately if provided
    if title:
        print(f"{title}")
    
    with alive_bar(None, manual=manual, force_tty=True) as bar:
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
    
    For 80x24 terminal compatibility, this always shows a spinner instead of a bar.

    Args:
        iterable: Source iterable
        total: Total length; ignored (always shows spinner for compact display)
        title: Optional title shown on the spinner
        enrich_items: If True, show each item string representation as the spinner text

    Returns:
        An iterator yielding the original items while showing progress
    """
    if alive_it is None:
        return iterable
    # Always use spinner (total=None) for compact 80x24 terminal display
    # Print title separately if provided
    if title:
        print(f"{title}")
    
    return alive_it(
        iterable,
        total=None,  # Force spinner mode
        enrich_print=enrich_items,
        force_tty=True,
    )


@contextmanager
def spinner(title: Optional[str] = None) -> Iterator[None]:
    """
    A simple spinner when total is unknown.

    If a title is provided, it is printed once above the spinner for compact
    80x24 terminal layouts.

    Usage:
        with spinner("Indexing files"):
            do_work()
    """
    if alive_bar is None:
        yield
        return
    if title:
        print(f"{title}")
    with alive_bar(None, force_tty=True):
        yield


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

    # Print title separately above the spinner for better 80x24 terminal layout
    if title:
        print(f"{title}")
    
    with spinner():  # No title in spinner since we printed it above
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


# ------------------------------------------------------------
# Global default progress configuration (easy to change here)
# ------------------------------------------------------------
# Compact settings optimized for 80x24 terminal windows
DEFAULT_PROGRESS_THEME = "smooth"
DEFAULT_PROGRESS_SPINNER = "it"  # More compact than "it"
DEFAULT_PROGRESS_UNKNOWN = "it"  # style for unknown-total bars

try:
    # Apply defaults once on import; safe no-op if alive-progress unavailable
    configure_global(
        theme=DEFAULT_PROGRESS_THEME,
        spinner=DEFAULT_PROGRESS_SPINNER,
        unknown=DEFAULT_PROGRESS_UNKNOWN,
        enrich_print=True,
        title_length=0,  # No title in bar - we'll print it separately
    )
except Exception:
    # Avoid import-time failures in environments lacking alive-progress
    pass
