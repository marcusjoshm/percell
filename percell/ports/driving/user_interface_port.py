from __future__ import annotations

from typing import Protocol


class UserInterfacePort(Protocol):
    """Driving port for user interaction (CLI/GUI).

    Implementations handle parsing inputs and presenting outputs, without
    encoding business logic.
    """

    def prompt(self, message: str) -> str:
        ...

    def info(self, message: str) -> None:
        ...

    def error(self, message: str) -> None:
        ...


