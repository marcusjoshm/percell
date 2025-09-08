from __future__ import annotations

"""Application-level progress API mirroring legacy core.progress."""

from contextlib import contextmanager
from typing import Iterable, Iterator, Optional, Callable, Any, List, Dict
import subprocess
import time
from threading import Thread, Event

try:
    from alive_progress import alive_bar, alive_it, config_handler
except Exception:  # pragma: no cover
    alive_bar = None  # type: ignore
    alive_it = None  # type: ignore
    config_handler = None  # type: ignore


def is_progress_available() -> bool:
    return alive_bar is not None


def configure_global(
    spinner: Optional[str] = None,
    theme: Optional[str] = None,
    enrich_print: Optional[bool] = None,
    title_length: Optional[int] = None,
    unknown: Optional[str] = None,
) -> None:
    if config_handler is None:
        return
    kwargs: Dict[str, Any] = {}
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
            pass


@contextmanager
def progress_bar(
    total: Optional[int] = None,
    title: Optional[str] = None,
    unit: str = "items",
    manual: bool = False,
) -> Iterator[Callable[[int], None]]:
    if alive_bar is None:
        def noop_update(_: int) -> None:
            return
        yield noop_update
        return
    if title:
        print(f"{title}")
    with alive_bar(None, manual=manual, force_tty=True) as bar:
        def update(delta: int = 1) -> None:
            try:
                if manual:
                    bar(delta)
                else:
                    bar()
            except Exception:
                pass
        yield update


def iter_with_progress(
    iterable: Iterable[Any],
    total: Optional[int] = None,
    title: Optional[str] = None,
    enrich_items: bool = False,
) -> Iterable[Any]:
    if alive_it is None:
        return iterable
    if title:
        print(f"{title}")
    return alive_it(iterable, total=None, enrich_print=enrich_items, force_tty=True)


@contextmanager
def spinner(title: Optional[str] = None) -> Iterator[None]:
    if alive_bar is None:
        yield
        return
    if title:
        print(f"{title}")
    stop_event: Event = Event()
    with alive_bar(None, force_tty=True) as bar:
        def _tick() -> None:
            while not stop_event.is_set():
                try:
                    bar()
                except Exception:
                    pass
                time.sleep(0.1)
        ticker = Thread(target=_tick, daemon=True)
        ticker.start()
        try:
            yield
        finally:
            stop_event.set()
            ticker.join(timeout=0.5)


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
    if title:
        print(f"{title}")
    with spinner():
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


# Defaults on import
DEFAULT_PROGRESS_THEME = "smooth"
DEFAULT_PROGRESS_SPINNER = "it"
DEFAULT_PROGRESS_UNKNOWN = "it"

try:
    configure_global(
        theme=DEFAULT_PROGRESS_THEME,
        spinner=DEFAULT_PROGRESS_SPINNER,
        unknown=DEFAULT_PROGRESS_UNKNOWN,
        enrich_print=True,
        title_length=0,
    )
except Exception:
    pass


