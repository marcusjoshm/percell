"""Refactored CLI services using the new menu system.

This module provides a cleaner, more maintainable CLI interface using
the command pattern and proper separation of concerns.
"""

from __future__ import annotations

import argparse
from typing import Optional
import logging

from percell.ports.driving.user_interface_port import UserInterfacePort
from percell.application.menu.menu_system import create_menu_system

logger = logging.getLogger(__name__)


def _any_stage_selected(args: argparse.Namespace) -> bool:
    """Check if any pipeline stage has been selected.

    Args:
        args: Command line arguments

    Returns:
        True if any stage is selected, False otherwise
    """
    stage_names = (
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
    return any(getattr(args, name, False) for name in stage_names)


def show_menu(ui: UserInterfacePort, args: argparse.Namespace) -> Optional[argparse.Namespace]:
    """Show the main menu interface.

    Args:
        ui: User interface for interaction
        args: Command line arguments

    Returns:
        Updated args or None to exit
    """
    # If any stage is already selected, skip menu
    if _any_stage_selected(args):
        return args

    # Create and show the menu system
    try:
        menu_system = create_menu_system(ui)
        return menu_system.show(args)
    except Exception as e:
        logger.error(f"Error in menu system: {e}")
        ui.error(f"Menu system error: {e}")
        return None


def _load_config_defaults(args: argparse.Namespace) -> tuple[str, str]:
    """Load default input/output directories from configuration.

    Returns:
        Tuple of (default_input, default_output) paths, empty strings if unavailable.
    """
    try:
        from percell.domain.services.configuration_service import create_configuration_service
        from percell.application.paths_api import get_path

        # Determine configuration path
        if hasattr(args, "config") and args.config:
            config_path = args.config
        else:
            try:
                config_path = str(get_path("config_default"))
            except Exception:
                config_path = "percell/config/config.json"

        config = create_configuration_service(config_path, create_if_missing=True)
        default_input = config.get("directories.input", "")
        default_output = config.get("directories.output", "")
        logger.debug(
            f"Loaded configuration defaults: input='{default_input}', output='{default_output}'"
        )
        return default_input, default_output

    except Exception as e:
        logger.warning(f"Could not load configuration defaults: {e}")
        return "", ""


def _apply_directory_default(
    args: argparse.Namespace,
    attr_name: str,
    default_value: str,
    ui: Optional[UserInterfacePort],
) -> None:
    """Apply a default directory value if not set and not in interactive mode.

    Raises:
        ValueError: If no value is set and no default is available.
    """
    has_value = getattr(args, attr_name, None)
    is_interactive = getattr(args, "interactive", False)

    if has_value or is_interactive:
        return

    if default_value:
        setattr(args, attr_name, default_value)
        if ui:
            ui.info(f"Using default {attr_name} directory: {default_value}")
    else:
        raise ValueError(f"{attr_name.capitalize()} directory is required unless using --interactive")


def validate_args(args: argparse.Namespace, ui: Optional[UserInterfacePort] = None) -> None:
    """Validate command line arguments and fill defaults from configuration.

    Args:
        args: Command line arguments to validate
        ui: Optional user interface for feedback

    Raises:
        ValueError: If required paths are missing in non-interactive mode
        ConfigurationError: If configuration cannot be loaded
    """
    default_input, default_output = _load_config_defaults(args)
    _apply_directory_default(args, "input", default_input, ui)
    _apply_directory_default(args, "output", default_output, ui)


def _run_combined_visualization(ui: UserInterfacePort, args: argparse.Namespace) -> None:
    """Run the combined visualization feature.

    This function provides interactive visualization of raw images, masks, and overlays
    with LUT controls for better image analysis.
    """
    try:
        from percell.domain.services.visualization_service import VisualizationService
        from percell.domain.models import DatasetSelection
        from pathlib import Path

        # Get directories from args
        if not hasattr(args, 'input') or not hasattr(args, 'output'):
            raise ValueError("Input and output directories must be specified")

        input_dir = Path(args.input)
        output_dir = Path(args.output)

        if not input_dir.exists():
            raise ValueError(f"Input directory does not exist: {input_dir}")

        # Create visualization service with image processor
        from percell.adapters.pil_image_processing_adapter import PILImageProcessingAdapter
        image_processor = PILImageProcessingAdapter()
        viz_service = VisualizationService(image_processor)

        # Create data selection service to discover available data
        from percell.domain.services.data_selection_service import DataSelectionService
        data_service = DataSelectionService()

        # First scan all available data
        all_files = data_service.scan_available_data(input_dir)

        if not all_files:
            ui.error(f"No .tif/.tiff files found in {input_dir}")
            return

        # Get configuration using the same approach as Napari
        from percell.domain.services.configuration_service import create_configuration_service
        from percell.application.paths_api import get_path

        try:
            config_path = str(get_path("config_default"))
        except Exception:
            config_path = "percell/config/config.json"

        config = create_configuration_service(config_path)

        # Get configured data selection using dot notation like Napari
        config_conditions = config.get("data_selection.selected_conditions", [])
        config_timepoints = config.get("data_selection.selected_timepoints", [])
        config_regions = config.get("data_selection.selected_regions", [])
        config_channels = config.get("data_selection.analysis_channels", [])

        ui.info(f"Using configured selection:")
        ui.info(f"  Conditions: {config_conditions}")
        ui.info(f"  Timepoints: {config_timepoints}")
        ui.info(f"  Regions: {config_regions}")
        ui.info(f"  Channels: {config_channels}")

        # Debug by showing what files are actually available (like Napari does)
        ui.info(f"Found {len(all_files)} total .tif/.tiff files")

        if all_files:
            ui.info("Sample files found:")
            for i, f in enumerate(all_files[:3]):  # Show first 3 files
                ui.info(f"  {f}")
                ui.info(f"    Parent dir: {f.parent.name}")
                ui.info(f"    Filename: {f.name}")

        # Parse what conditions/timepoints/regions are actually available
        available_conditions, available_timepoints, available_regions = data_service.parse_conditions_timepoints_regions(all_files)
        ui.info(f"Available conditions: {available_conditions}")
        ui.info(f"Available timepoints: {available_timepoints}")
        ui.info(f"Available regions: {available_regions}")

        # Use smart fallback logic like Napari: use configured values if they match available data
        use_conditions = config_conditions if any(c in available_conditions for c in config_conditions) else available_conditions
        use_timepoints = config_timepoints if any(t in available_timepoints for t in config_timepoints) else available_timepoints
        use_regions = config_regions if any(r in available_regions for r in config_regions) else available_regions

        ui.info(f"Adjusted selection to match available data:")
        ui.info(f"  Conditions: {use_conditions}")
        ui.info(f"  Timepoints: {use_timepoints}")
        ui.info(f"  Regions: {use_regions}")
        ui.info(f"  Channels: {config_channels}")

        selected_conditions = use_conditions
        selected_timepoints = use_timepoints
        selected_regions = use_regions
        selected_channels = config_channels

        # Create a selection using configured filters
        selection = DatasetSelection(
            root=input_dir,
            conditions=selected_conditions,
            timepoints=selected_timepoints,
            regions=selected_regions,
            channels=selected_channels if selected_channels else []
        )

        # Find masks directory using same approach as Napari (check multiple locations)
        ui.info(f"Looking for masks in output directory: {output_dir}")

        masks_dir = None
        mask_locations = [
            output_dir / "combined_masks",  # Combined masks first (like Napari)
            output_dir / "masks",
            output_dir / "segmentation",
            output_dir / "cellpose_output"
        ]

        for potential_masks in mask_locations:
            if potential_masks.exists():
                ui.info(f"Found masks directory: {potential_masks}")
                masks_dir = potential_masks
                break
            else:
                ui.info(f"Checked: {potential_masks} (does not exist)")

        if not masks_dir:
            ui.info("No masks directory found. Showing raw images only.")
            masks_dir = Path("/nonexistent")  # Ensure it doesn't exist
        else:
            # Show some mask files for debugging
            mask_files = list(masks_dir.rglob("*.tif*"))
            ui.info(f"Found {len(mask_files)} potential mask files in {masks_dir}")
            if mask_files:
                ui.info("Sample mask files:")
                for mask_file in mask_files[:3]:
                    ui.info(f"  {mask_file.name}")

        ui.info("Starting interactive visualization...")
        ui.info("Use the sliders to adjust image intensity. Close windows to navigate between images.")

        # Run visualization with default overlay alpha
        viz_service.create_visualization_data(input_dir, masks_dir, selection)

    except Exception as e:
        logger.error(f"Visualization error: {e}")
        ui.error(f"Failed to run combined visualization: {e}")


def _run_napari_viewer(ui: UserInterfacePort, args: argparse.Namespace) -> None:
    """Run the Napari viewer feature.

    This function launches Napari for advanced image visualization and analysis.
    """
    try:
        import napari
        from percell.domain.services.data_selection_service import DataSelectionService
        from percell.domain.models import DatasetSelection
        from pathlib import Path
        import numpy as np
        from PIL import Image

        # Get directories from args
        if not hasattr(args, 'input') or not hasattr(args, 'output'):
            raise ValueError("Input and output directories must be specified")

        input_dir = Path(args.input)
        output_dir = Path(args.output)

        if not input_dir.exists():
            raise ValueError(f"Input directory does not exist: {input_dir}")

        # Get configuration to use actual configured selection
        from percell.domain.services.configuration_service import create_configuration_service
        from percell.application.paths_api import get_path

        try:
            config_path = str(get_path("config_default"))
        except Exception:
            config_path = "percell/config/config.json"

        config = create_configuration_service(config_path)

        # Get configured data selection
        config_conditions = config.get("data_selection.selected_conditions", [])
        config_timepoints = config.get("data_selection.selected_timepoints", [])
        config_regions = config.get("data_selection.selected_regions", [])
        config_channels = config.get("data_selection.analysis_channels", [])

        ui.info(f"Using configured selection:")
        ui.info(f"  Conditions: {config_conditions}")
        ui.info(f"  Timepoints: {config_timepoints}")
        ui.info(f"  Regions: {config_regions}")
        ui.info(f"  Channels: {config_channels}")

        # Create data selection service
        data_service = DataSelectionService()

        # First, let's debug by seeing what files are actually available
        all_files = data_service.scan_available_data(input_dir)
        ui.info(f"Found {len(all_files)} total .tif/.tiff files")

        if all_files:
            ui.info("Sample files found:")
            for i, f in enumerate(all_files[:3]):  # Show first 3 files
                ui.info(f"  {f}")
                ui.info(f"    Parent dir: {f.parent.name}")
                ui.info(f"    Filename: {f.name}")

        # Parse what conditions/timepoints/regions are actually available
        available_conditions, available_timepoints, available_regions = data_service.parse_conditions_timepoints_regions(all_files)
        ui.info(f"Available conditions: {available_conditions}")
        ui.info(f"Available timepoints: {available_timepoints}")
        ui.info(f"Available regions: {available_regions}")

        # Create selection using available data (adjust configured selection to match reality)
        # The issue is that conditions in config are A549_As_treated but files show timepoint_1
        # Use available conditions instead of configured ones for now
        use_conditions = available_conditions  # Use what's actually available
        use_timepoints = config_timepoints if any(t in available_timepoints for t in config_timepoints) else available_timepoints
        use_regions = config_regions if any(r in available_regions for r in config_regions) else available_regions

        ui.info(f"Adjusted selection to match available data:")
        ui.info(f"  Conditions: {use_conditions}")
        ui.info(f"  Timepoints: {use_timepoints}")
        ui.info(f"  Regions: {use_regions}")
        ui.info(f"  Channels: {config_channels}")

        selection = DatasetSelection(
            root=input_dir,
            conditions=use_conditions,
            timepoints=use_timepoints,
            regions=use_regions,
            channels=config_channels if config_channels else None
        )

        # Get file lists using the configured selection
        raw_files = data_service.generate_file_lists(selection)

        if not raw_files:
            ui.error("No raw data files found matching configured selection criteria")
            ui.info("This might be a mismatch between configured selection and available data")
            return

        ui.info(f"Found {len(raw_files)} images. Loading into Napari...")

        # Create napari viewer
        viewer = napari.Viewer()

        # Load images into napari
        for i, raw_file in enumerate(raw_files[:10]):  # Limit to first 10 for performance
            try:
                # Use PIL to read image
                image = np.array(Image.open(raw_file))
                viewer.add_image(image, name=f"Raw_{raw_file.name}", colormap='viridis')

                # Try to load corresponding mask if available
                masks_dir = output_dir / "masks"
                combined_masks_dir = output_dir / "combined_masks"

                # Check both masks and combined_masks directories
                mask_file = None

                if combined_masks_dir.exists():
                    # Look for combined mask files first
                    mask_candidates = list(combined_masks_dir.rglob(f"*{raw_file.stem}*"))
                    # Filter to get actual files, not directories
                    mask_files = [m for m in mask_candidates if m.is_file() and m.suffix.lower() in ['.tif', '.tiff']]
                    if mask_files:
                        mask_file = mask_files[0]
                        ui.info(f"Found combined mask: {mask_file}")

                if not mask_file and masks_dir.exists():
                    # Look in individual masks directory
                    mask_candidates = list(masks_dir.rglob(f"*{raw_file.stem}*"))
                    # Filter to get actual files, not directories
                    mask_files = [m for m in mask_candidates if m.is_file() and m.suffix.lower() in ['.tif', '.tiff']]
                    if mask_files:
                        mask_file = mask_files[0]
                        ui.info(f"Found individual mask: {mask_file}")

                if mask_file:
                    try:
                        mask_image = np.array(Image.open(mask_file))
                        viewer.add_labels(mask_image.astype(np.int32),
                                        name=f"Mask_{raw_file.name}")
                    except Exception as e:
                        ui.info(f"Could not load mask {mask_file}: {e}")

            except Exception as e:
                logger.warning(f"Could not load {raw_file}: {e}")
                continue

        # Reset view to fit all loaded layers to screen
        viewer.reset_view()

        ui.info("Napari viewer launched. Close the viewer window when done.")
        napari.run()

    except ImportError:
        ui.error("Napari is not installed. Please install it with: pip install napari[all]")
    except Exception as e:
        logger.error(f"Napari viewer error: {e}")
        ui.error(f"Failed to run Napari viewer: {e}")