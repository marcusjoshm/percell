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


def show_configuration_menu(
    ui: UserInterfacePort, args: argparse.Namespace
) -> Optional[argparse.Namespace]:
    """Show configuration submenu."""
    show_header(ui)
    ui.info("")
    ui.info(colorize("CONFIGURATION MENU:", Colors.bold))
    ui.info("")
    ui.info(f"{Colors.bold}{Colors.white}1.{Colors.reset} {colorize('I/O', Colors.yellow)} {colorize('- Set input/output directories', Colors.reset)}")  # noqa: E501
    ui.info(f"{Colors.bold}{Colors.white}2.{Colors.reset} {colorize('Data Selection', Colors.yellow)} {colorize('- Select parameters (conditions, timepoints, channels, etc.)', Colors.reset)}")  # noqa: E501
    ui.info(f"   {colorize('for processing and analysis', Colors.reset)}")
    ui.info(f"{Colors.bold}{Colors.white}3.{Colors.reset} {colorize('Current Configuration', Colors.yellow)} {colorize('- View current analysis configuration', Colors.reset)}")  # noqa: E501
    ui.info(f"{Colors.bold}{Colors.white}4.{Colors.reset} {colorize('Back to Main Menu', Colors.red)}")  # noqa: E501
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
            from percell.application.directory_setup import (
                set_default_directories,
            )
            from percell.application.paths_api import get_path

            try:
                config_path = str(get_path("config_default"))
            except Exception:
                config_path = "percell/config/config.json"

            config = load_config(config_path)
            input_path, output_path = set_default_directories(
                config, config_path
            )

            # Reflect selections back into args
            args.input = input_path
            args.output = output_path
        except Exception as e:
            ui.error(f"Directory setup failed: {e}")
            # Fallback to simple prompts
            if not getattr(args, "input", None):
                args.input = ui.prompt("Enter input directory path: ").strip()
            if not getattr(args, "output", None):
                args.output = ui.prompt(
                    "Enter output directory path: "
                ).strip()
        return show_menu(ui, args)
    elif choice == "2":
        setattr(args, "data_selection", True)
        setattr(args, "return_to_main", True)
        return args
    elif choice == "3":
        # Display current configuration
        try:
            from percell.application.config_display import (
                display_current_configuration,
            )
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

            display_current_configuration(
                ui, config, current_input, current_output
            )
        except Exception as e:
            ui.error(f"Error displaying configuration: {e}")
            ui.prompt("Press Enter to continue...")

        return show_menu(ui, args)
    elif choice == "4":
        return show_menu(ui, args)
    return show_configuration_menu(ui, args)


def show_workflows_menu(
    ui: UserInterfacePort, args: argparse.Namespace
) -> Optional[argparse.Namespace]:
    """Show workflows submenu."""
    show_header(ui)
    ui.info("")
    ui.info(colorize("WORKFLOWS MENU:", Colors.bold))
    ui.info("")
    ui.info(f"{Colors.bold}{Colors.white}1.{Colors.reset} {colorize('Default Workflow', Colors.yellow)} {colorize('- Current default analysis workflow', Colors.reset)}")  # noqa: E501
    ui.info(f"{Colors.bold}{Colors.white}2.{Colors.reset} {colorize('Advanced Workflow Builder', Colors.yellow)} {colorize('- Build custom analysis workflow', Colors.reset)}")  # noqa: E501
    ui.info(f"{Colors.bold}{Colors.white}3.{Colors.reset} {colorize('Back to Main Menu', Colors.red)}")  # noqa: E501
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


def show_processing_menu(
    ui: UserInterfacePort, args: argparse.Namespace
) -> Optional[argparse.Namespace]:
    """Show processing submenu."""
    show_header(ui)
    ui.info("")
    ui.info(colorize("PROCESSING MENU:", Colors.bold))
    ui.info("")
    ui.info(f"{Colors.bold}{Colors.white}1.{Colors.reset} {colorize('Single-Cell Data Processing', Colors.yellow)}{colorize(' - Tracking, resizing, extraction, grouping', Colors.reset)}")  # noqa: E501
    ui.info(f"{Colors.bold}{Colors.white}2.{Colors.reset} {colorize('Back to Main Menu', Colors.red)}")  # noqa: E501
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


def show_segmentation_menu(
    ui: UserInterfacePort, 
    args: argparse.Namespace
) -> Optional[argparse.Namespace]:
    """Show segmentation submenu."""
    show_header(ui)
    ui.info("")
    ui.info(colorize("SEGMENTATION MENU:", Colors.bold))
    ui.info("")
    ui.info(f"{Colors.bold}{Colors.white}1.{Colors.reset} {colorize('Cellpose', Colors.yellow)}{colorize(' - Single-cell segmentation using Cellpose SAM GUI', Colors.reset)}")  # noqa: E501
    ui.info(f"{Colors.bold}{Colors.white}2.{Colors.reset} {colorize('Back to Main Menu', Colors.red)}")  # noqa: E501
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


def show_tracking_menu(
    ui: UserInterfacePort, 
    args: argparse.Namespace
) -> Optional[argparse.Namespace]:
    """Show tracking submenu."""
    show_header(ui)
    ui.info("")
    ui.info(colorize("TRACKING MENU:", Colors.bold))
    ui.info("")
    ui.info(colorize("(No tracking options available yet)", Colors.reset))
    ui.info("")
    ui.info(f"{Colors.bold}{Colors.white}1.{Colors.reset} {colorize('Back to Main Menu', Colors.red)}")  # noqa: E501
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


def show_visualization_menu(
    ui: UserInterfacePort, 
    args: argparse.Namespace
) -> Optional[argparse.Namespace]:
    """Show visualization submenu."""
    show_header(ui)
    ui.info("")
    ui.info(colorize("VISUALIZATION MENU:", Colors.bold))
    ui.info("")
    ui.info(f"{Colors.bold}{Colors.white}1.{Colors.reset} {colorize('Interactive Visualization', Colors.yellow)} {colorize('- Display raw images, masks, and overlays with LUT', Colors.reset)}")  # noqa: E501
    ui.info(f"   {colorize('controls', Colors.reset)}")
    ui.info(f"{Colors.bold}{Colors.white}2.{Colors.reset} {colorize('Napari Viewer', Colors.yellow)} {colorize('- Launch Napari for advanced image visualization and analysis', Colors.reset)}")  # noqa: E501
    ui.info(f"{Colors.bold}{Colors.white}3.{Colors.reset} {colorize('Back to Main Menu', Colors.red)}")  # noqa: E501
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
        try:
            _run_combined_visualization(ui, args)
        except Exception as e:
            ui.error(f"Error running visualization: {e}")
            ui.prompt("Press Enter to continue...")
        # Return to main menu after visualization
        return show_menu(ui, args)
    elif choice == "2":
        try:
            _run_napari_viewer(ui, args)
        except Exception as e:
            ui.error(f"Error running Napari viewer: {e}")
            ui.prompt("Press Enter to continue...")
        # Return to main menu after napari
        return show_menu(ui, args)
    elif choice == "3":
        return show_menu(ui, args)
    return show_visualization_menu(ui, args)


def show_analysis_menu(
    ui: UserInterfacePort, args: argparse.Namespace
) -> Optional[argparse.Namespace]:
    """Show analysis submenu."""
    show_header(ui)
    ui.info("")
    ui.info(colorize("ANALYSIS MENU:", Colors.bold))
    ui.info("")
    ui.info(f"{Colors.bold}{Colors.white}1.{Colors.reset} {colorize('Threshold Grouped Cells', Colors.yellow)}{colorize(' - interactive Otsu autothresholding using imageJ', Colors.reset)}")  # noqa: E501
    ui.info(f"{Colors.bold}{Colors.white}2.{Colors.reset} {colorize('Measure Cell Area', Colors.yellow)}{colorize(' - Measure area of cells in ROIs using imageJ', Colors.reset)}")  # noqa: E501
    ui.info(f"{Colors.bold}{Colors.white}3.{Colors.reset} {colorize('Particle Analysis', Colors.yellow)}{colorize(' - Analyze particles in segmented images using imageJ', Colors.reset)}")  # noqa: E501
    ui.info(f"{Colors.bold}{Colors.white}4.{Colors.reset} {colorize('Back to Main Menu', Colors.red)}")  # noqa: E501
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


def show_plugins_menu(
    ui: UserInterfacePort, 
    args: argparse.Namespace
) -> Optional[argparse.Namespace]:
    """Show plugins submenu."""
    show_header(ui)
    ui.info("")
    ui.info(colorize("PLUGINS MENU:", Colors.bold))
    ui.info("")
    ui.info(f"{Colors.bold}{Colors.white}1.{Colors.reset} {colorize('Auto Image Preprocessing', Colors.yellow)}{colorize(' - auto preprocessing for downstream analysis', Colors.reset)}")  # noqa: E501
    ui.info(f"{Colors.bold}{Colors.white}2.{Colors.reset} {colorize('Back to Main Menu', Colors.red)}")  # noqa: E501
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
        # Import and run the auto image preprocessing plugin
        try:
            from percell.plugins.auto_image_preprocessing import (
                show_auto_image_preprocessing_plugin,
            )
            result = show_auto_image_preprocessing_plugin(ui, args)
            # If plugin returns args, go to main menu; 
            # otherwise stay in plugins menu
            if result is not None:
                return show_menu(ui, args)
        except ImportError as e:
            ui.error(f"Failed to load auto image preprocessing plugin: {e}")
            ui.prompt("Press Enter to continue...")
        return show_plugins_menu(ui, args)
    elif choice == "2":
        return show_menu(ui, args)
    return show_plugins_menu(ui, args)


def show_utilities_menu(
    ui: UserInterfacePort, 
    args: argparse.Namespace
) -> Optional[argparse.Namespace]:
    """Show utilities submenu."""
    show_header(ui)
    ui.info("")
    ui.info(colorize("UTILITIES MENU:", Colors.bold))
    ui.info("")
    ui.info(f"{Colors.bold}{Colors.white}1.{Colors.reset} {colorize('Cleanup', Colors.yellow)}{colorize(' - Delete individual cells and masks to save space', Colors.reset)}")  # noqa: E501
    ui.info(f"{Colors.bold}{Colors.white}2.{Colors.reset} {colorize('Back to Main Menu', Colors.red)}")  # noqa: E501
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


def show_menu(
    ui: UserInterfacePort, 
    args: argparse.Namespace
) -> Optional[argparse.Namespace]:
    if _any_stage_selected(args):
        return args

    show_header(ui)
    ui.info("")
    ui.info(colorize("              🔬 Welcome single-cell microscopy analysis user! 🔬               ", Colors.bold))  # noqa: E501
    ui.info("")
    ui.info(colorize("MAIN MENU:", Colors.bold))
    ui.info(f"{Colors.bold}{Colors.white}1.{Colors.reset}  {colorize('Configuration', Colors.yellow)} {colorize('- Set input/output directories and analysis parameters', Colors.reset)}")  # noqa: E501
    ui.info(f"{Colors.bold}{Colors.white}2.{Colors.reset}  {colorize('Workflows', Colors.yellow)} {colorize('- Pre-built and custom analysis workflows', Colors.reset)}")  # noqa: E501
    ui.info(f"{Colors.bold}{Colors.white}3.{Colors.reset}  {colorize('Segmentation', Colors.yellow)} {colorize('- Single-cell segmentation tools', Colors.reset)}")  # noqa: E501
    ui.info(f"{Colors.bold}{Colors.white}4.{Colors.reset}  {colorize('Processing', Colors.yellow)} {colorize('- Data processing for downstream analysis', Colors.reset)}")  # noqa: E501
    ui.info(f"{Colors.bold}{Colors.white}5.{Colors.reset}  {colorize('Tracking', Colors.yellow)} {colorize('- Single-cell tracking tools', Colors.reset)}")  # noqa: E501
    ui.info(f"{Colors.bold}{Colors.white}6.{Colors.reset}  {colorize('Visualization', Colors.yellow)} {colorize('- Image and mask visualization tools', Colors.reset)}")  # noqa: E501
    ui.info(f"{Colors.bold}{Colors.white}7.{Colors.reset}  {colorize('Analysis', Colors.yellow)} {colorize('- Semi-automated thresholding and image analysis tools', Colors.reset)}")  # noqa: E501
    ui.info(f"{Colors.bold}{Colors.white}8.{Colors.reset}  {colorize('Plugins', Colors.yellow)} {colorize('- Extend functionality with plugins', Colors.reset)}")  # noqa: E501
    ui.info(f"{Colors.bold}{Colors.white}9.{Colors.reset}  {colorize('Utilities', Colors.yellow)} {colorize('- Cleanup and maintenance tools', Colors.reset)}")  # noqa: E501
    ui.info(f"{Colors.bold}{Colors.white}10.{Colors.reset} {colorize('Exit', Colors.red)} {colorize('- Quit the application', Colors.reset)}")  # noqa: E501
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


def validate_args(
    args: argparse.Namespace, 
    ui: Optional[UserInterfacePort] = None
) -> None:
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

    if not getattr(args, "input", None) and not getattr(
        args, "interactive", False
    ):
        if default_input:
            args.input = default_input
            if ui:
                ui.info(f"Using default input directory: {default_input}")
        else:
            raise ValueError(
                "Input directory is required unless using --interactive"
            )

    if not getattr(args, "output", None) and not getattr(
        args, "interactive", False
    ):
        if default_output:
            args.output = default_output
            if ui:
                ui.info(f"Using default output directory: {default_output}")
        else:
            raise ValueError(
                "Output directory is required unless using --interactive"
            )


def _run_combined_visualization(
    ui: UserInterfacePort, args: argparse.Namespace
) -> None:
    """Run the combined visualization feature."""
    from percell.application.visualization_service import VisualizationService
    from percell.application.config_api import Config
    from percell.application.paths_api import get_path
    from percell.domain.models import DatasetSelection
    from pathlib import Path

    # Get current configuration
    try:
        config_path = str(get_path("config_default"))
    except Exception:
        config_path = "percell/config/config.json"

    config = Config(config_path)

    # Get directories
    input_dir = (
        getattr(args, 'input', None) or config.get("directories.input", "")
    )
    output_dir = (
        getattr(args, 'output', None) or config.get("directories.output", "")
    )

    if not input_dir:
        input_dir = ui.prompt("Enter input directory path: ").strip()
    if not output_dir:
        output_dir = ui.prompt("Enter output directory path: ").strip()

    # Look for raw data in output/raw_data first, 
    # then fall back to input directory
    output_raw_data_dir = Path(output_dir) / "raw_data"
    input_raw_data_dir = Path(input_dir)

    if output_raw_data_dir.exists():
        raw_data_dir = output_raw_data_dir
        ui.info(f"Using processed raw data: {raw_data_dir}")
    elif input_raw_data_dir.exists():
        raw_data_dir = input_raw_data_dir
        ui.info(f"Using original input data: {raw_data_dir}")
    else:
        ui.error(
            (
                f"No raw data found in {output_raw_data_dir} or "
                f"{input_raw_data_dir}"
            )
        )
        return

    # Look for masks in combined_masks first, then fall back to masks
    combined_masks_dir = Path(output_dir) / "combined_masks"
    masks_dir = Path(output_dir) / "masks"

    if combined_masks_dir.exists():
        masks_dir = combined_masks_dir
        ui.info(f"Using combined masks: {masks_dir}")
    elif masks_dir.exists():
        ui.info(f"Using individual masks: {masks_dir}")
    else:
        ui.info(f"No masks found in {combined_masks_dir} or {masks_dir}")
        ui.info("Will show raw images only")

    # Get data selection configuration from config but be 
    # flexible with conditions
    config_conditions = config.get("data_selection.selected_conditions", [])
    config_timepoints = config.get("data_selection.selected_timepoints", [])
    config_regions = config.get("data_selection.selected_regions", [])
    config_channels = config.get("data_selection.analysis_channels", [])

    # For visualization, let's be more flexible and 
    # discover what's actually available
    from percell.domain.services.data_selection_service import (
        DataSelectionService,
    )
    data_service = DataSelectionService()
    all_files = data_service.scan_available_data(raw_data_dir)
    available_conditions, available_timepoints, available_regions = (
        data_service.parse_conditions_timepoints_regions(all_files)
    )

    ui.info(f"Available conditions: {available_conditions}")
    ui.info(f"Available timepoints: {available_timepoints}")
    ui.info(f"Available regions: {available_regions}")

    # Use config selections if they match available data,
    # otherwise use all available
    use_conditions = (
        config_conditions
        if any(c in available_conditions for c in config_conditions)
        else available_conditions
    )
    use_timepoints = (
        config_timepoints
        if any(t in available_timepoints for t in config_timepoints)
        else available_timepoints
    )
    use_regions = (
        config_regions
        if any(r in available_regions for r in config_regions)
        else available_regions
    )

    selection = DatasetSelection(
        root=raw_data_dir,
        conditions=use_conditions,
        timepoints=use_timepoints,
        regions=use_regions,
        channels=config_channels
    )

    ui.info(
        f"Creating interactive visualization for "
        f"{len(selection.conditions or ['all'])} conditions..."
    )
    ui.info(
        "Use the sliders to adjust intensity range "
        "(similar to ImageJ brightness/contrast)"
    )
    ui.info("Green overlay at 70% transparency")

    # Create visualization
    viz_service = VisualizationService(ui)
    success = viz_service.display_combined_visualization(
        raw_data_dir, masks_dir, selection, overlay_alpha=0.7
    )

    if success:
        ui.info("Visualization created successfully!")
    else:
        ui.error("Failed to create visualization")

    ui.prompt("Press Enter to continue...")


def _run_napari_viewer(
    ui: UserInterfacePort, 
    args: argparse.Namespace
) -> None:
    """Run the Napari viewer feature."""
    from percell.adapters.napari_subprocess_adapter import (
        NapariSubprocessAdapter,
    )
    from percell.application.config_api import Config
    from percell.application.paths_api import get_path
    from pathlib import Path

    # Get current configuration
    try:
        config_path = str(get_path("config_default"))
    except Exception:
        config_path = "percell/config/config.json"

    config = Config(config_path)

    # Get directories
    input_dir = (
        getattr(args, 'input', None) or config.get("directories.input", "")
    )
    output_dir = (
        getattr(args, 'output', None) or config.get("directories.output", "")
    )

    if not input_dir:
        input_dir = ui.prompt("Enter input directory path: ").strip()
    if not output_dir:
        output_dir = ui.prompt("Enter output directory path: ").strip()

    # Look for raw data in output/raw_data first,
    # then fall back to input directory
    output_raw_data_dir = Path(output_dir) / "raw_data"
    input_raw_data_dir = Path(input_dir)

    if output_raw_data_dir.exists():
        raw_data_dir = output_raw_data_dir
        ui.info(f"Using processed raw data: {raw_data_dir}")
    elif input_raw_data_dir.exists():
        raw_data_dir = input_raw_data_dir
        ui.info(f"Using original input data: {raw_data_dir}")
    else:
        ui.error(
            (
                f"No raw data found in {output_raw_data_dir} or "
                f"{input_raw_data_dir}"
            )
        )
        return

    # Look for masks in combined_masks first, then fall back to masks
    combined_masks_dir = Path(output_dir) / "combined_masks"
    masks_dir = Path(output_dir) / "masks"

    masks_found = None
    if combined_masks_dir.exists():
        masks_found = combined_masks_dir
        ui.info(f"Found combined masks: {masks_found}")
    elif masks_dir.exists():
        masks_found = masks_dir
        ui.info(f"Found individual masks: {masks_found}")
    else:
        ui.info("No masks found - will launch Napari with images only")

    # Use data selection service to get files based on configuration
    from percell.domain.models import DatasetSelection
    from percell.domain.services.data_selection_service import DataSelectionService

    data_service = DataSelectionService()

    # Get data selection configuration from config
    config_conditions = config.get("data_selection.selected_conditions", [])
    config_timepoints = config.get("data_selection.selected_timepoints", [])
    config_regions = config.get("data_selection.selected_regions", [])
    config_channels = config.get("data_selection.analysis_channels", [])

    # Create data selection using the same approach as visualization
    selection = DatasetSelection(
        root=raw_data_dir,
        conditions=config_conditions,
        timepoints=config_timepoints,
        regions=config_regions,
        channels=config_channels
    )

    # For visualization, be flexible and discover what's actually available
    all_files = data_service.scan_available_data(raw_data_dir)
    available_conditions, available_timepoints, available_regions = (
        data_service.parse_conditions_timepoints_regions(all_files)
    )

    ui.info(f"Available conditions: {available_conditions}")
    ui.info(f"Available timepoints: {available_timepoints}")
    ui.info(f"Available regions: {available_regions}")

    # Use config selections if they match available data, otherwise use all available
    use_conditions = (
        config_conditions
        if config_conditions and any(c in available_conditions for c in config_conditions)
        else available_conditions
    )
    use_timepoints = (
        config_timepoints
        if config_timepoints and any(t in available_timepoints for t in config_timepoints)
        else available_timepoints
    )
    use_regions = (
        config_regions
        if config_regions and any(r in available_regions for r in config_regions)
        else available_regions
    )

    # Create flexible selection
    flexible_selection = DatasetSelection(
        root=raw_data_dir,
        conditions=use_conditions,
        timepoints=use_timepoints,
        regions=use_regions,
        channels=config_channels
    )

    # Get files using flexible selection
    image_files = data_service.generate_file_lists(flexible_selection)

    if image_files:
        ui.info(f"Found {len(image_files)} files matching selection criteria:")
        ui.info(f"  Using conditions: {use_conditions or 'all'}")
        ui.info(f"  Using timepoints: {use_timepoints or 'all'}")
        ui.info(f"  Using regions: {use_regions or 'all'}")
        ui.info(f"  Using channels: {config_channels or 'all'}")
    else:
        ui.info("No files found - this shouldn't happen with flexible selection")

    # Find corresponding mask files using correspondence mapping (like visualization service)
    mask_files = []
    if masks_found and image_files:
        from percell.application.visualization_service import VisualizationService
        viz_service = VisualizationService(ui)
        mask_mapping = viz_service._find_corresponding_masks(image_files, masks_found)

        # Extract the mask files from the mapping
        for idx, mask_file in mask_mapping.items():
            if mask_file and mask_file.exists():
                mask_files.append(mask_file)

    if image_files:
        ui.info(f"Loading {len(image_files)} raw data files as separate layers")
        for img in image_files:
            ui.info(f"  Image: {img}")

    if mask_files:
        ui.info(f"Loading {len(mask_files)} mask files as separate layers")
        for mask in mask_files:
            ui.info(f"  Mask: {mask}")
    elif masks_found:
        ui.info("No mask files found matching selection criteria")

    # Use the virtual environment python
    try:
        import sys
        python_path = Path(sys.executable)
        ui.info(f"Using Python interpreter: {python_path}")
    except Exception:
        python_path = Path("python")

    # Create napari adapter and launch
    napari_adapter = NapariSubprocessAdapter(python_path)

    ui.info("Launching Napari viewer...")
    ui.info("Selected files will be loaded as separate layers based on your data selection configuration.")
    ui.info("Napari will open in a new window. Close the window when finished.")

    # Launch napari with selected files based on data selection configuration
    napari_adapter.launch_viewer(
        images=image_files if image_files else None,
        masks=mask_files if mask_files else None,
        working_dir=raw_data_dir
    )