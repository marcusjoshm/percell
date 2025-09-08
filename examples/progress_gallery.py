"""
Demo script that displays all theme and spinner options from alive-progress.

Run:
    python examples/progress_gallery.py
"""

from __future__ import annotations

import time
from typing import List

from percell.application.progress_api import (
    is_progress_available,
    configure_global,
    progress_bar,
)


def list_themes() -> List[str]:
    try:
        from alive_progress.styles import THEMES
        return sorted(THEMES.keys())
    except Exception:
        return []


def list_spinners() -> List[str]:
    try:
        from alive_progress.styles import SPINNERS
        return sorted(SPINNERS.keys())
    except Exception:
        return []


def demo_theme(theme_name: str) -> None:
    # Use the theme for both known-total bars and unknown-total bars
    configure_global(theme=theme_name, spinner="waves", unknown=theme_name)
    total = 30
    with progress_bar(total=total, title=f"Theme: {theme_name}") as update:
        for _ in range(total):
            time.sleep(0.02)
            update()


def demo_spinner(spinner_name: str) -> None:
    # Keep the bar theme consistent, swap spinner per demo
    configure_global(theme="smooth", spinner=spinner_name, unknown="smooth")
    # Spinner demonstration using total=None
    with progress_bar(total=None, title=f"Spinner: {spinner_name}") as update:
        # Animate for a short, fixed duration
        end = time.time() + 0.8
        while time.time() < end:
            time.sleep(0.05)
            update(0)


def main() -> None:
    if not is_progress_available():
        print("alive-progress is not installed; this demo will not render bars.")
        return

    themes = list_themes()
    spinners = list_spinners()

    print("\n=== Themes ===")
    print(", ".join(themes) if themes else "<none detected>")
    for name in themes:
        demo_theme(name)

    print("\n=== Spinners ===")
    print(", ".join(spinners) if spinners else "<none detected>")
    for name in spinners:
        demo_spinner(name)

    print("\nAll theme and spinner demos completed.\n")


if __name__ == "__main__":
    main()


