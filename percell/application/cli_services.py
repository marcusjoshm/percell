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


def show_configuration_menu(ui: UserInterfacePort, args: argparse.Namespace) -> Optional[argparse.Namespace]:
    """Show configuration submenu."""
    show_header(ui)
    ui.info("")
    ui.info(colorize("CONFIGURATION MENU:", Colors.bold))
    ui.info("")
    ui.info(colorize("1. Set Input/Output Directories", Colors.yellow))
    ui.info(colorize("2. Data Selection (conditions, regions, timepoints, channels)", Colors.yellow))
    ui.info(colorize("3. Check Current Configuration", Colors.blue))
    ui.info(colorize("4. Back to Main Menu", Colors.red))
    ui.info("")
    ui.info("")
    ui.info("")
    ui.info("")
    ui.info("")
    ui.info("")
    ui.info("")
    ui.info("")
    ui.info("")

    choice = ui.prompt("Select an option (1-4): ").strip().lower()
    if choice == "1":
        # Use interactive directory setup with recent paths and defaults
        try:
            # Resolve config path similar to validate_args
            from percell.application.directory_setup import load_config
            from percell.application.directory_setup import set_default_directories
            from percell.application.paths_api import get_path

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
        return show_configuration_menu(ui, args)
    elif choice == "2":
        setattr(args, "data_selection", True)
        setattr(args, "return_to_config", True)
        return args
    elif choice == "3":
        # Display current configuration
        try:
            from percell.application.config_display import display_current_configuration
            from percell.application.paths_api import get_path

            try:
                config_path = str(get_path("config_default"))
            except Exception:
                config_path = "percell/config/config.json"

            from percell.application.config_api import Config
            config = Config(config_path)

            # Pass current args input/output if available
            current_input = getattr(args, 'input', None)
            current_output = getattr(args, 'output', None)

            display_current_configuration(ui, config, current_input, current_output)
        except Exception as e:
            ui.error(f"Error displaying configuration: {e}")
            ui.prompt("Press Enter to continue...")

        return show_configuration_menu(ui, args)
    elif choice == "4":
        return show_menu(ui, args)
    return show_configuration_menu(ui, args)


def show_workflows_menu(ui: UserInterfacePort, args: argparse.Namespace) -> Optional[argparse.Namespace]:
    """Show workflows submenu."""
    show_header(ui)
    ui.info("")
    ui.info(colorize("WORKFLOWS MENU:", Colors.bold))
    ui.info("")
    ui.info(colorize("1. Run Complete Workflow", Colors.yellow))
    ui.info(colorize("2. Advanced Workflow Builder (custom sequence of steps)", Colors.yellow))
    ui.info(colorize("3. Back to Main Menu", Colors.red))
    ui.info("")
    ui.info("")
    ui.info("")
    ui.info("")
    ui.info("")
    ui.info("")
    ui.info("")
    ui.info("")
    ui.info("")
    ui.info("")

    choice = ui.prompt("Select an option (1-3): ").strip().lower()
    if choice == "1":
        args.data_selection = True
        args.segmentation = True
        args.process_single_cell = True
        args.threshold_grouped_cells = True
        args.measure_roi_area = True
        args.analysis = True
        args.complete_workflow = True
        return args
    elif choice == "2":
        setattr(args, "advanced_workflow", True)
        return args
    elif choice == "3":
        return show_menu(ui, args)
    return show_workflows_menu(ui, args)


def show_processing_menu(ui: UserInterfacePort, args: argparse.Namespace) -> Optional[argparse.Namespace]:
    """Show processing submenu."""
    show_header(ui)
    ui.info("")
    ui.info(colorize("PROCESSING MENU:", Colors.bold))
    ui.info("")
    ui.info(colorize("1. Process Single-cell Data (tracking, resizing, extraction, grouping)", Colors.yellow))
    ui.info(colorize("2. Back to Main Menu", Colors.red))
    ui.info("")
    ui.info("")
    ui.info("")
    ui.info("")
    ui.info("")
    ui.info("")
    ui.info("")
    ui.info("")
    ui.info("")
    ui.info("")
    ui.info("")

    choice = ui.prompt("Select an option (1-2): ").strip().lower()
    if choice == "1":
        setattr(args, "process_single_cell", True)
        return args
    elif choice == "2":
        return show_menu(ui, args)
    return show_processing_menu(ui, args)


def show_segmentation_menu(ui: UserInterfacePort, args: argparse.Namespace) -> Optional[argparse.Namespace]:
    """Show segmentation submenu."""
    show_header(ui)
    ui.info("")
    ui.info(colorize("SEGMENTATION MENU:", Colors.bold))
    ui.info("")
    ui.info(colorize("1. Cellpose Single-cell Segmentation", Colors.yellow))
    ui.info(colorize("2. Back to Main Menu", Colors.red))
    ui.info("")
    ui.info("")
    ui.info("")
    ui.info("")
    ui.info("")
    ui.info("")
    ui.info("")
    ui.info("")
    ui.info("")
    ui.info("")
    ui.info("")

    choice = ui.prompt("Select an option (1-2): ").strip().lower()
    if choice == "1":
        setattr(args, "segmentation", True)
        return args
    elif choice == "2":
        return show_menu(ui, args)
    return show_segmentation_menu(ui, args)


def show_tracking_menu(ui: UserInterfacePort, args: argparse.Namespace) -> Optional[argparse.Namespace]:
    """Show tracking submenu."""
    show_header(ui)
    ui.info("")
    ui.info(colorize("TRACKING MENU:", Colors.bold))
    ui.info("")
    ui.info(colorize("(No tracking options available yet)", Colors.reset))
    ui.info("")
    ui.info(colorize("1. Back to Main Menu", Colors.red))
    ui.info("")
    ui.info("")
    ui.info("")
    ui.info("")
    ui.info("")
    ui.info("")
    ui.info("")
    ui.info("")
    ui.info("")
    ui.info("")

    choice = ui.prompt("Select an option (1): ").strip().lower()
    if choice == "1":
        return show_menu(ui, args)
    return show_tracking_menu(ui, args)


def show_visualization_menu(ui: UserInterfacePort, args: argparse.Namespace) -> Optional[argparse.Namespace]:
    """Show visualization submenu."""
    show_header(ui)
    ui.info("")
    ui.info(colorize("VISUALIZATION MENU:", Colors.bold))
    ui.info("")
    ui.info(colorize("(No visualization options available yet)", Colors.reset))
    ui.info("")
    ui.info(colorize("1. Back to Main Menu", Colors.red))
    ui.info("")
    ui.info("")
    ui.info("")
    ui.info("")
    ui.info("")
    ui.info("")
    ui.info("")
    ui.info("")
    ui.info("")
    ui.info("")

    choice = ui.prompt("Select an option (1): ").strip().lower()
    if choice == "1":
        return show_menu(ui, args)
    return show_visualization_menu(ui, args)


def show_analysis_menu(ui: UserInterfacePort, args: argparse.Namespace) -> Optional[argparse.Namespace]:
    """Show analysis submenu."""
    show_header(ui)
    ui.info("")
    ui.info(colorize("ANALYSIS MENU:", Colors.bold))
    ui.info("")
    ui.info(colorize("1. Threshold Grouped Cells (interactive ImageJ thresholding)", Colors.yellow))
    ui.info(colorize("2. Measure Cell Area (measure areas from single-cell ROIs)", Colors.yellow))
    ui.info(colorize("3. Analysis (combine masks, create cell masks, export results)", Colors.yellow))
    ui.info(colorize("4. Back to Main Menu", Colors.red))
    ui.info("")
    ui.info("")
    ui.info("")
    ui.info("")
    ui.info("")
    ui.info("")
    ui.info("")
    ui.info("")
    ui.info("")

    choice = ui.prompt("Select an option (1-4): ").strip().lower()
    if choice == "1":
        setattr(args, "threshold_grouped_cells", True)
        return args
    elif choice == "2":
        setattr(args, "measure_roi_area", True)
        return args
    elif choice == "3":
        setattr(args, "analysis", True)
        return args
    elif choice == "4":
        return show_menu(ui, args)
    return show_analysis_menu(ui, args)


def show_plugins_menu(ui: UserInterfacePort, args: argparse.Namespace) -> Optional[argparse.Namespace]:
    """Show plugins submenu."""
    show_header(ui)
    ui.info("")
    ui.info(colorize("PLUGINS MENU:", Colors.bold))
    ui.info("")
    ui.info(colorize("(No plugins available yet)", Colors.reset))
    ui.info("")
    ui.info(colorize("1. Back to Main Menu", Colors.red))
    ui.info("")
    ui.info("")
    ui.info("")
    ui.info("")
    ui.info("")
    ui.info("")
    ui.info("")
    ui.info("")
    ui.info("")
    ui.info("")

    choice = ui.prompt("Select an option (1): ").strip().lower()
    if choice == "1":
        return show_menu(ui, args)
    return show_plugins_menu(ui, args)


def show_utilities_menu(ui: UserInterfacePort, args: argparse.Namespace) -> Optional[argparse.Namespace]:
    """Show utilities submenu."""
    show_header(ui)
    ui.info("")
    ui.info(colorize("UTILITIES MENU:", Colors.bold))
    ui.info("")
    ui.info(colorize("1. Cleanup (empty cells and masks directories, preserves grouped/combined data)", Colors.reset))
    ui.info(colorize("2. Back to Main Menu", Colors.red))
    ui.info("")
    ui.info("")
    ui.info("")
    ui.info("")
    ui.info("")
    ui.info("")
    ui.info("")
    ui.info("")
    ui.info("")
    ui.info("")
    ui.info("")

    choice = ui.prompt("Select an option (1-2): ").strip().lower()
    if choice == "1":
        setattr(args, "cleanup", True)
        return args
    elif choice == "2":
        return show_menu(ui, args)
    return show_utilities_menu(ui, args)


def show_menu(ui: UserInterfacePort, args: argparse.Namespace) -> Optional[argparse.Namespace]:
    if _any_stage_selected(args):
        return args

    show_header(ui)
    ui.info("")
    ui.info(colorize("  🔬 Welcome single-cell microscopy analysis user! 🔬", Colors.bold))
    ui.info("")
    ui.info(colorize("MAIN MENU:", Colors.bold))
    ui.info("")
    ui.info(colorize("1. Configuration", Colors.reset))
    ui.info(colorize("2. Workflows", Colors.yellow))
    ui.info(colorize("3. Processing", Colors.yellow))
    ui.info(colorize("4. Segmentation", Colors.yellow))
    ui.info(colorize("5. Tracking", Colors.yellow))
    ui.info(colorize("6. Visualization", Colors.yellow))
    ui.info(colorize("7. Analysis", Colors.yellow))
    ui.info(colorize("8. Plugins", Colors.yellow))
    ui.info(colorize("9. Utilities", Colors.reset))
    ui.info(colorize("10. Exit", Colors.red))
    ui.info("")

    choice = ui.prompt("Select an option (1-10): ").strip().lower()
    if choice == "1":
        return show_configuration_menu(ui, args)
    elif choice == "2":
        return show_workflows_menu(ui, args)
    elif choice == "3":
        return show_processing_menu(ui, args)
    elif choice == "4":
        return show_segmentation_menu(ui, args)
    elif choice == "5":
        return show_tracking_menu(ui, args)
    elif choice == "6":
        return show_visualization_menu(ui, args)
    elif choice == "7":
        return show_analysis_menu(ui, args)
    elif choice == "8":
        return show_plugins_menu(ui, args)
    elif choice == "9":
        return show_utilities_menu(ui, args)
    elif choice in ("10", "q", "quit"):
        return None
    return show_menu(ui, args)


def validate_args(args: argparse.Namespace, ui: Optional[UserInterfacePort] = None) -> None:
    """Validate args and fill defaults from config if available.

    Raises:
        ValueError if required paths are missing in non-interactive mode.
    """
    # Load defaults from config if needed
    default_input = ""
    default_output = ""
    try:
        from percell.application.directory_setup import load_config
        from percell.application.paths_api import get_path

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


