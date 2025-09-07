from __future__ import annotations

from percell.ports.driving.user_interface_port import UserInterfacePort


class Colors:
    red = '\033[31m'
    orange = '\033[38;5;208m'
    yellow = '\033[33m'
    green = '\033[32m'
    blue = '\033[34m'
    indigo = '\033[38;5;54m'
    violet = '\033[35m'
    magenta = '\033[95m'
    reset = '\033[0m'
    bold = '\033[1m'


def colorize(text: str, color: str) -> str:
    return f"{Colors.bold}{color}{text}{Colors.reset}"


def show_header(ui: UserInterfacePort) -> None:
    header = [
        "         ███████╗ ████████╗███████╗ ███████╗████████╗██╗      ██╗               ",
        "         ██╔═══██╗██╔═════╝██╔═══██╗██╔════╝██╔═════╝██║      ██║               ",
        "         ███████╔╝███████╗ ███████╔╝██║     ███████╗ ██║      ██║               ",
        "         ██╔════╝ ██╔════╝ ██╔═══██╗██║     ██╔════╝ ██║      ██║               ",
        "         ██║      ████████╗██║   ██║███████╗████████╗████████╗████████╗         ",
        "         ╚═╝      ╚═══════╝╚═╝   ╚═╝╚══════╝╚═══════╝╚═══════╝╚═══════╝         ",
    ]

    ui.info("")  # Empty line at start
    for i, line in enumerate(header):
        colored_line = ""
        for j, char in enumerate(line):
            # Color based on column position (match original behavior)
            if 1 <= j <= 35:  # PER section
                colored_line += colorize(char, Colors.green)
            elif 36 <= j <= 80:  # CELL section
                colored_line += colorize(char, Colors.magenta)
            else:
                colored_line += char
        ui.info(colored_line)


