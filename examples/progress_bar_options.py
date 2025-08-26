"""
Test script that displays available options in percell.core.progress for a progress bar.

Run:
    python examples/progress_bar_options.py
"""

from __future__ import annotations

import time
import inspect
from typing import Any

from percell.core import (
    is_progress_available,
    configure_global,
    progress_bar,
)


def print_function_options(func: Any, name: str) -> None:
    signature = inspect.signature(func)
    print(f"\nOptions for {name}{signature}:")
    for param_name, param in signature.parameters.items():
        default_repr = "<required>" if param.default is inspect._empty else repr(param.default)
        annotation = getattr(param.annotation, "__name__", str(param.annotation))
        print(f"  - {param_name}: type={annotation}, default={default_repr}")


def demo_progress_bar_automatic() -> None:
    total_steps = 20
    print(f"\n[DEMO] progress_bar with automatic increments (manual=False), total={total_steps}")
    with progress_bar(total=total_steps, title="Automatic bar", manual=False) as update:
        for _ in range(total_steps):
            time.sleep(0.04)
            update(1)
    print("Completed automatic progress bar demo.")


def demo_progress_bar_manual() -> None:
    total_steps = 15
    print(f"\n[DEMO] progress_bar with manual increments (manual=True), total={total_steps}")
    with progress_bar(total=total_steps, title="Manual bar", manual=True) as update:
        for _ in range(total_steps):
            time.sleep(0.05)
            update(1)
    print("Completed manual progress bar demo.")


def demo_progress_spinner_variant() -> None:
    print("\n[DEMO] progress_bar spinner variant (total=None)")
    with progress_bar(total=None, title="Spinner via progress_bar") as update:
        for _ in range(25):
            time.sleep(0.04)
            update(0)
    print("Completed spinner variant demo.")


def main() -> None:
    if not is_progress_available():
        print("alive-progress is not installed; this will run without visible bars.")

    # Optionally set a theme/spinner to make output consistent.
    # You can try other values if your environment supports them, e.g. theme="smooth", spinner="waves".
    configure_global(theme="smooth", spinner="it", enrich_print=True)

    # Display available options (parameters) from the progress API in percell.core.progress
    from percell.core.progress import progress_bar as _progress_bar_impl
    from percell.core.progress import configure_global as _configure_global_impl

    print_function_options(_configure_global_impl, "configure_global")
    print_function_options(_progress_bar_impl, "progress_bar")

    # Demonstrate each progress_bar mode
    demo_progress_bar_automatic()
    demo_progress_bar_manual()
    demo_progress_spinner_variant()

    print("\nAll progress bar option demos completed.\n")


if __name__ == "__main__":
    main()


