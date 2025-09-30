#!/usr/bin/env python3
"""Quick test of exit functionality."""

import argparse
from percell.application.menu.menu_system import create_menu_system
from percell.ports.driving.user_interface_port import UserInterfacePort


class QuietUI(UserInterfacePort):
    def __init__(self, responses):
        self.responses = responses
        self.index = 0

    def info(self, message: str) -> None:
        pass  # Suppress output

    def error(self, message: str) -> None:
        print(f"ERROR: {message}")

    def prompt(self, message: str) -> str:
        if self.index < len(self.responses):
            response = self.responses[self.index]
            self.index += 1
            print(f"Selecting option: {response}")
            return response
        return "q"


ui = QuietUI(["10"])  # Select Exit
menu_system = create_menu_system(ui)
args = argparse.Namespace()

result = menu_system.show(args)
print(f"Exit test result: {result}")
print("✅ Exit works!" if result is None else "❌ Exit failed!")