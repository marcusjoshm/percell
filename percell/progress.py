from __future__ import annotations

# Compatibility alias for tooling that expects percell.progress
from typing import Any, Callable, Dict, Iterable, Iterator, List, Optional

from percell.core import progress as _core_progress


def is_progress_available() -> bool:
    return _core_progress.is_progress_available()


def configure_global(
    spinner: Optional[str] = None,
    theme: Optional[str] = None,
    enrich_print: Optional[bool] = None,
    title_length: Optional[int] = None,
    unknown: Optional[str] = None,
) -> None:
    return _core_progress.configure_global(
        spinner=spinner,
        theme=theme,
        enrich_print=enrich_print,
        title_length=title_length,
        unknown=unknown,
    )


def progress_bar(
    total: Optional[int] = None,
    title: Optional[str] = None,
    unit: str = "items",
    manual: bool = False,
) -> Iterator[Callable[[int], None]]:
    return _core_progress.progress_bar(total=total, title=title, unit=unit, manual=manual)


def iter_with_progress(
    iterable: Iterable[Any],
    total: Optional[int] = None,
    title: Optional[str] = None,
    enrich_items: bool = False,
) -> Iterable[Any]:
    return _core_progress.iter_with_progress(
        iterable=iterable, total=total, title=title, enrich_items=enrich_items
    )


def spinner() -> Iterator[None]:
    return _core_progress.spinner()


def run_subprocess_with_spinner(
    cmd: List[str],
    title: Optional[str] = None,
    capture_output: bool = True,
    text: bool = True,
    check: bool = False,
    env: Optional[Dict[str, str]] = None,
    cwd: Optional[str] = None,
    stdin: Any = None,
):
    return _core_progress.run_subprocess_with_spinner(
        cmd=cmd,
        title=title,
        capture_output=capture_output,
        text=text,
        check=check,
        env=env,
        cwd=cwd,
        stdin=stdin,
    )


__all__ = [
    "is_progress_available",
    "configure_global",
    "progress_bar",
    "iter_with_progress",
    "spinner",
    "run_subprocess_with_spinner",
]


