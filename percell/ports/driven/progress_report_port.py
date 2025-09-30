from __future__ import annotations

from typing import Protocol, Callable, ContextManager


class ProgressReportPort(Protocol):
    """Driven port for reporting progress during long-running operations.

    This port abstracts progress reporting mechanisms (progress bars, spinners, etc.)
    to keep adapters decoupled from specific UI implementations.
    """

    def create_progress_bar(
        self,
        total: int,
        title: str,
        manual: bool = False
    ) -> ContextManager[Callable[[int], None]]:
        """Create a progress bar context manager.

        Args:
            total: Total number of items to process
            title: Title/description for the progress bar
            manual: If True, caller must manually call update function

        Returns:
            Context manager that yields an update function.
            The update function accepts an integer increment value.

        Example:
            with progress.create_progress_bar(100, "Processing") as update:
                for i in range(100):
                    # Do work
                    update(1)  # Increment by 1
        """
        ...

    def create_spinner(self, title: str) -> ContextManager[None]:
        """Create an indeterminate spinner for operations without known duration.

        Args:
            title: Title/description for the spinner

        Returns:
            Context manager that displays a spinner while active

        Example:
            with progress.create_spinner("Loading..."):
                # Do work with unknown duration
                pass
        """
        ...
