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
from typing import Iterable, Iterator, Optional, Callable, Any


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
) -> None:
    """
    Optionally configure alive-progress global behavior.

    Args:
        spinner: Name of spinner preset, e.g. 'dots', 'twirls'
        theme: Theme name, e.g. 'classic', 'smooth', 'rainbow'
        enrich_print: Whether to patch print for bar-friendly output
        title_length: Max title length in bar display
    """
    if config_handler is None:
        return
    with config_handler.handler(
        spinner=spinner, theme=theme, enrich_print=enrich_print, title_length=title_length
    ):
        # the context applies immediately for global settings
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

    # alive_bar supports total=None for spinner; set calibrate for consistent speed
    with alive_bar(total, title=title or "", manual=manual, refresh_per_second=8, force_tty=True) as bar:
        def update(delta: int = 1) -> None:
            try:
                bar(delta)
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


