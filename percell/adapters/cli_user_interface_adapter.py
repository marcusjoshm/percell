from __future__ import annotations

from percell.ports.driving.user_interface_port import UserInterfacePort


class CLIUserInterfaceAdapter(UserInterfacePort):
    def prompt(self, message: str) -> str:
        try:
            return input(message)
        except EOFError:
            return ""

    def info(self, message: str) -> None:
        print(message)

    def error(self, message: str) -> None:
        print(message)
