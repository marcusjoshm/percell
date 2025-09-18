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
    ui.info(f"{Colors.bold}{Colors.white}1.{Colors.reset} {colorize('I/O', Colors.yellow)} {colorize('- Set input/output directories', Colors.reset)}")
    ui.info(f"{Colors.bold}{Colors.white}2.{Colors.reset} {colorize('Data Selection', Colors.yellow)} {colorize('- Select data for analysis', Colors.reset)}")
    ui.info(f"{Colors.bold}{Colors.white}3.{Colors.reset} {colorize('Current Configuration', Colors.yellow)} {colorize('- View current analysis configuration', Colors.reset)}")
    ui.info(f"{Colors.bold}{Colors.white}4.{Colors.reset} {colorize('Back to Main Menu', Colors.red)}")
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
        return show_menu(ui, args)
    elif choice == "2":
        setattr(args, "data_selection", True)
        setattr(args, "return_to_main", True)
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

        return show_menu(ui, args)
    elif choice == "4":
        return show_menu(ui, args)
    return show_configuration_menu(ui, args)


def show_workflows_menu(ui: UserInterfacePort, args: argparse.Namespace) -> Optional[argparse.Namespace]:
    """Show workflows submenu."""
    show_header(ui)
    ui.info("")
    ui.info(colorize("WORKFLOWS MENU:", Colors.bold))
    ui.info("")
    ui.info(f"{Colors.bold}{Colors.white}1.{Colors.reset} {colorize('Default Workflow', Colors.yellow)} {colorize('- Current default analysis workflow', Colors.reset)}")
    ui.info(f"{Colors.bold}{Colors.white}2.{Colors.reset} {colorize('Advanced Workflow Builder', Colors.yellow)} {colorize('- Build custom analysis workflow', Colors.reset)}")
    ui.info(f"{Colors.bold}{Colors.white}3.{Colors.reset} {colorize('Back to Main Menu', Colors.red)}")
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
    ui.info(f"{Colors.bold}{Colors.white}1.{Colors.reset} {colorize('Single-Cell Data Processing', Colors.yellow)}{colorize(' - Tracking, resizing, extraction, grouping', Colors.reset)}")
    ui.info(f"{Colors.bold}{Colors.white}2.{Colors.reset} {colorize('Back to Main Menu', Colors.red)}")
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
    ui.info(f"{Colors.bold}{Colors.white}1.{Colors.reset} {colorize('Cellpose', Colors.yellow)}{colorize(' - Single-cell segmentation using Cellpose SAM GUI', Colors.reset)}")
    ui.info(f"{Colors.bold}{Colors.white}2.{Colors.reset} {colorize('Back to Main Menu', Colors.red)}")
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
    ui.info(f"{Colors.bold}{Colors.white}1.{Colors.reset} {colorize('Back to Main Menu', Colors.red)}")
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
    ui.info(f"{Colors.bold}{Colors.white}1.{Colors.reset} {colorize('Back to Main Menu', Colors.red)}")
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
    ui.info(f"{Colors.bold}{Colors.white}1.{Colors.reset} {colorize('Threshold Grouped Cells', Colors.yellow)}{colorize(' - interactive Otsu autothresholding using imageJ', Colors.reset)}")
    ui.info(f"{Colors.bold}{Colors.white}2.{Colors.reset} {colorize('Measure Cell Area', Colors.yellow)}{colorize(' - Measure area of cells in ROIs using imageJ', Colors.reset)}")
    ui.info(f"{Colors.bold}{Colors.white}3.{Colors.reset} {colorize('Particle Analysis', Colors.yellow)}{colorize(' - Analyze particles in segmented images using imageJ', Colors.reset)}")
    ui.info(f"{Colors.bold}{Colors.white}4.{Colors.reset} {colorize('Back to Main Menu', Colors.red)}")
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
    ui.info(f"{Colors.bold}{Colors.white}1.{Colors.reset} {colorize('Advanced Image Processing', Colors.yellow)}{colorize(' - Microscopy image preprocessing workflow', Colors.reset)}")
    ui.info(f"{Colors.bold}{Colors.white}2.{Colors.reset} {colorize('Back to Main Menu', Colors.red)}")
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
        # Import and run the advanced image processing plugin
        try:
            from percell.plugins.advanced_image_processing import show_advanced_image_processing_plugin
            result = show_advanced_image_processing_plugin(ui, args)
            # If plugin returns args, go to main menu; otherwise stay in plugins menu
            if result is not None:
                return show_menu(ui, args)
        except ImportError as e:
            ui.error(f"Failed to load advanced image processing plugin: {e}")
            ui.prompt("Press Enter to continue...")
        return show_plugins_menu(ui, args)
    elif choice == "2":
        return show_menu(ui, args)
    return show_plugins_menu(ui, args)


def show_utilities_menu(ui: UserInterfacePort, args: argparse.Namespace) -> Optional[argparse.Namespace]:
    """Show utilities submenu."""
    show_header(ui)
    ui.info("")
    ui.info(colorize("UTILITIES MENU:", Colors.bold))
    ui.info("")
    ui.info(f"{Colors.bold}{Colors.white}1.{Colors.reset} {colorize('Cleanup', Colors.yellow)}{colorize(' - Delete individual cells and masks to save space', Colors.reset)}")
    ui.info(f"{Colors.bold}{Colors.white}2.{Colors.reset} {colorize('Back to Main Menu', Colors.red)}")
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
    ui.info(colorize("              🔬 Welcome single-cell microscopy analysis user! 🔬               ", Colors.bold))
    ui.info("")
    ui.info(colorize("MAIN MENU:", Colors.bold))
    ui.info(f"{Colors.bold}{Colors.white}1.{Colors.reset}  {colorize('Configuration', Colors.yellow)} {colorize('- Set input/output directories and data selection', Colors.reset)}")
    ui.info(f"{Colors.bold}{Colors.white}2.{Colors.reset}  {colorize('Workflows', Colors.yellow)} {colorize('- Run complete or custom analysis workflows', Colors.reset)}")
    ui.info(f"{Colors.bold}{Colors.white}3.{Colors.reset}  {colorize('Segmentation', Colors.yellow)} {colorize('- Cellpose SAM', Colors.reset)}")
    ui.info(f"{Colors.bold}{Colors.white}4.{Colors.reset}  {colorize('Processing', Colors.yellow)} {colorize('- Data processing for downstream analysis', Colors.reset)}")
    ui.info(f"{Colors.bold}{Colors.white}5.{Colors.reset}  {colorize('Tracking', Colors.yellow)} {colorize('- Track cells across time points', Colors.reset)}")
    ui.info(f"{Colors.bold}{Colors.white}6.{Colors.reset}  {colorize('Visualization', Colors.yellow)} {colorize('- Create visualizations and plots', Colors.reset)}")
    ui.info(f"{Colors.bold}{Colors.white}7.{Colors.reset}  {colorize('Analysis', Colors.yellow)} {colorize('- Semi-automated thresholding, cell area, and particle analysis', Colors.reset)}")
    ui.info(f"{Colors.bold}{Colors.white}8.{Colors.reset}  {colorize('Plugins', Colors.yellow)} {colorize('- Extend functionality with plugins', Colors.reset)}")
    ui.info(f"{Colors.bold}{Colors.white}9.{Colors.reset}  {colorize('Utilities', Colors.yellow)} {colorize('- Cleanup and maintenance tools', Colors.reset)}")
    ui.info(f"{Colors.bold}{Colors.white}10.{Colors.reset} {colorize('Exit', Colors.red)} {colorize('- Quit the application', Colors.reset)}")
    ui.info("")
    ui.info("")

    choice = ui.prompt("Select an option (1-10): ").strip().lower()
    if choice == "1":
        return show_configuration_menu(ui, args)
    elif choice == "2":
        return show_workflows_menu(ui, args)
    elif choice == "3":
        return show_segmentation_menu(ui, args)
    elif choice == "4":
        return show_processing_menu(ui, args)
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


