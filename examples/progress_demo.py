"""
Example script demonstrating percell.core.progress utilities.

Run:
    python examples/progress_demo.py
"""

from __future__ import annotations

import time
import random

from percell.core import (
    is_progress_available,
    configure_global,
    spinner,
    progress_bar,
    iter_with_progress,
)


def demo_spinner() -> None:
    print("\n[DEMO] Spinner: indexing files for ~2s")
    with spinner("Indexing files"):
        time.sleep(2.0)
    print("Completed spinner demo.")


def demo_manual_bar() -> None:
    total_steps = 25
    print(f"\n[DEMO] Manual progress_bar: {total_steps} steps")
    with progress_bar(total=total_steps, title="Processing items") as update:
        for _ in range(total_steps):
            time.sleep(0.05 + random.random() * 0.03)
            update(1)
    print("Completed manual bar demo.")


def demo_iter_wrapper() -> None:
    items = list(range(30))
    print(f"\n[DEMO] iter_with_progress over {len(items)} items")
    for _ in iter_with_progress(items, title="Loading dataset"):
        time.sleep(0.03 + random.random() * 0.02)
    print("Completed iterable progress demo.")


def main() -> None:
    if not is_progress_available():
        print("alive-progress is not installed; demos will run without visible bars.")

    # Optional: set a consistent theme/spinner across demos
    configure_global(theme="classic", spinner="dots", enrich_print=True)

    demo_spinner()
    demo_manual_bar()
    demo_iter_wrapper()

    print("\nAll progress demos completed.\n")


if __name__ == "__main__":
    main()



