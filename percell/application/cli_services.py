from __future__ import annotations

import argparse
from typing import Optional

from percell.ports.driving.user_interface_port import UserInterfacePort
from percell.application.ui_components import show_header, colorize, Colors


def _any_stage_selected(args: argparse.Namespace) -> bool:
    return any(
        getattr(args, name, False)
        for name in (
            "data_selection",
            "segmentation",
            "process_single_cell",
            "threshold_grouped_cells",
            "measure_roi_area",
            "analysis",
            "cleanup",
            "complete_workflow",
            "advanced_workflow",
        )
    )


def show_menu(ui: UserInterfacePort, args: argparse.Namespace) -> Optional[argparse.Namespace]:
    if _any_stage_selected(args):
        return args

    show_header(ui)
    ui.info("")
    ui.info(colorize("  🔬 Welcome single-cell microscopy analysis user! 🔬", Colors.bold))
    ui.info("")
    ui.info(colorize("MENU:", Colors.bold))
    ui.info(colorize("1. Set Input/Output Directories", Colors.yellow))
    ui.info(colorize("2. Run Complete Workflow", Colors.magenta))
    ui.info(colorize("3. Data Selection", Colors.green))
    ui.info(colorize("4. Single-cell Segmentation (Cellpose)", Colors.green))
    ui.info(colorize("5. Process Single-cell Data", Colors.green))
    ui.info(colorize("6. Threshold Grouped Cells", Colors.green))
    ui.info(colorize("7. Measure ROI Area", Colors.green))
    ui.info(colorize("8. Analysis", Colors.green))
    ui.info(colorize("9. Cleanup", Colors.yellow))
    ui.info(colorize("10. Advanced Workflow", Colors.magenta))
    ui.info(colorize("11. Exit", Colors.red))
    ui.info("")

    choice = ui.prompt("Select an option (1-11): ").strip().lower()
    if choice == "1":
        # Use interactive directory setup with recent paths and defaults
        try:
            # Resolve config path similar to validate_args
            from percell.modules.directory_setup import load_config
            from percell.modules.set_directories import set_default_directories
            from percell.core.paths import get_path

            try:
                config_path = str(get_path("config_default"))
            except Exception:
                config_path = "percell/config/config.json"

            config = load_config(config_path)
            input_path, output_path = set_default_directories(config, config_path)

            # Reflect selections back into args
            args.input = input_path
            args.output = output_path
        except Exception as e:
            ui.error(f"Directory setup failed: {e}")
            # Fallback to simple prompts
            if not getattr(args, "input", None):
                args.input = ui.prompt("Enter input directory path: ").strip()
            if not getattr(args, "output", None):
                args.output = ui.prompt("Enter output directory path: ").strip()
        return args
    if choice == "2":
        args.data_selection = True
        args.segmentation = True
        args.process_single_cell = True
        args.threshold_grouped_cells = True
        args.measure_roi_area = True
        args.analysis = True
        args.complete_workflow = True
        return args
    mapping = {
        "3": "data_selection",
        "4": "segmentation",
        "5": "process_single_cell",
        "6": "threshold_grouped_cells",
        "7": "measure_roi_area",
        "8": "analysis",
        "9": "cleanup",
        "10": "advanced_workflow",
    }
    if choice in mapping:
        setattr(args, mapping[choice], True)
        return args
    if choice in ("11", "q", "quit"):
        return None
    return args


def validate_args(args: argparse.Namespace, ui: Optional[UserInterfacePort] = None) -> None:
    """Validate args and fill defaults from config if available.

    Raises:
        ValueError if required paths are missing in non-interactive mode.
    """
    # Load defaults from config if needed
    default_input = ""
    default_output = ""
    try:
        from percell.modules.directory_setup import load_config
        from percell.core.paths import get_path

        if getattr(args, "config", None):
            config_path = args.config
        else:
            try:
                config_path = str(get_path("config_default"))
            except Exception:
                config_path = "percell/config/config.json"
        config = load_config(config_path)
        default_input = config.get("directories", {}).get("input", "")
        default_output = config.get("directories", {}).get("output", "")
    except Exception:
        pass

    if not getattr(args, "input", None) and not getattr(args, "interactive", False):
        if default_input:
            args.input = default_input
            if ui:
                ui.info(f"Using default input directory: {default_input}")
        else:
            raise ValueError("Input directory is required unless using --interactive")

    if not getattr(args, "output", None) and not getattr(args, "interactive", False):
        if default_output:
            args.output = default_output
            if ui:
                ui.info(f"Using default output directory: {default_output}")
        else:
            raise ValueError("Output directory is required unless using --interactive")


