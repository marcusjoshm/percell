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

# Default fallback path when config_default cannot be resolved
_DEFAULT_CONFIG_PATH = "percell/config/config.json"


def _any_stage_selected(args: argparse.Namespace) -> bool:
    """Check if any pipeline stage has been selected.

    Args:
        args: Command line arguments

    Returns:
        True if any stage is selected, False otherwise
    """
    stage_names = (
        "data_selection",
        "cellpose_segmentation",
        "process_cellpose_single_cell",
        "auc_group_cells",
        "semi_auto_threshold_grouped_cells",
        "full_auto_threshold_grouped_cells",
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
                config_path = _DEFAULT_CONFIG_PATH

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


def _get_config_path() -> str:
    """Get the configuration file path, with fallback to default."""
    from percell.application.paths_api import get_path
    try:
        return str(get_path("config_default"))
    except Exception:
        return _DEFAULT_CONFIG_PATH


def _load_data_selection_config(config) -> dict:
    """Load data selection configuration values."""
    return {
        "conditions": config.get("data_selection.selected_conditions", []),
        "timepoints": config.get("data_selection.selected_timepoints", []),
        "regions": config.get("data_selection.selected_regions", []),
        "channels": config.get("data_selection.analysis_channels", []),
    }


def _adjust_selection_to_available(
    configured: list, available: list
) -> list:
    """Use configured values if any match available data, otherwise use all available."""
    if any(item in available for item in configured):
        return configured
    return available


def _find_masks_directory(output_dir, ui: UserInterfacePort):
    """Find the masks directory from known locations."""
    from pathlib import Path

    ui.info(f"Looking for masks in output directory: {output_dir}")

    mask_locations = [
        output_dir / "combined_masks",
        output_dir / "masks",
        output_dir / "segmentation",
        output_dir / "cellpose_output",
    ]

    for potential_masks in mask_locations:
        if potential_masks.exists():
            ui.info(f"Found masks directory: {potential_masks}")
            return potential_masks
        ui.info(f"Checked: {potential_masks} (does not exist)")

    ui.info("No masks directory found. Showing raw images only.")
    return Path("/nonexistent")


def _log_sample_files(ui: UserInterfacePort, files: list, label: str) -> None:
    """Log sample files for debugging."""
    if not files:
        return
    ui.info(f"Sample {label}:")
    for f in files[:3]:
        ui.info(f"  {f.name if hasattr(f, 'name') else f}")
        if hasattr(f, 'parent'):
            ui.info(f"    Parent dir: {f.parent.name}")


def _run_combined_visualization(ui: UserInterfacePort, args: argparse.Namespace) -> None:
    """Run the combined visualization feature.

    This function provides interactive visualization of raw images, masks, and overlays
    with LUT controls for better image analysis.
    """
    try:
        from percell.domain.services.visualization_service import VisualizationService
        from percell.domain.models import DatasetSelection
        from percell.domain.services.configuration_service import create_configuration_service
        from percell.domain.services.data_selection_service import DataSelectionService
        from percell.adapters.pil_image_processing_adapter import PILImageProcessingAdapter
        from pathlib import Path

        if not hasattr(args, 'input') or not hasattr(args, 'output'):
            raise ValueError("Input and output directories must be specified")

        input_dir = Path(args.input)
        output_dir = Path(args.output)

        if not input_dir.exists():
            raise ValueError(f"Input directory does not exist: {input_dir}")

        # Create services
        viz_service = VisualizationService(PILImageProcessingAdapter())
        data_service = DataSelectionService()

        # Scan available data
        all_files = data_service.scan_available_data(input_dir)
        if not all_files:
            ui.error(f"No .tif/.tiff files found in {input_dir}")
            return

        # Load configuration
        config = create_configuration_service(_get_config_path())
        cfg = _load_data_selection_config(config)

        ui.info("Using configured selection:")
        ui.info(f"  Conditions: {cfg['conditions']}")
        ui.info(f"  Timepoints: {cfg['timepoints']}")
        ui.info(f"  Regions: {cfg['regions']}")
        ui.info(f"  Channels: {cfg['channels']}")

        ui.info(f"Found {len(all_files)} total .tif/.tiff files")
        _log_sample_files(ui, all_files, "files found")

        # Parse available data
        avail_cond, avail_time, avail_reg = data_service.parse_conditions_timepoints_regions(all_files)
        ui.info(f"Available conditions: {avail_cond}")
        ui.info(f"Available timepoints: {avail_time}")
        ui.info(f"Available regions: {avail_reg}")

        # Adjust selection to match available data
        use_conditions = _adjust_selection_to_available(cfg['conditions'], avail_cond)
        use_timepoints = _adjust_selection_to_available(cfg['timepoints'], avail_time)
        use_regions = _adjust_selection_to_available(cfg['regions'], avail_reg)

        ui.info("Adjusted selection to match available data:")
        ui.info(f"  Conditions: {use_conditions}")
        ui.info(f"  Timepoints: {use_timepoints}")
        ui.info(f"  Regions: {use_regions}")
        ui.info(f"  Channels: {cfg['channels']}")

        selection = DatasetSelection(
            root=input_dir,
            conditions=use_conditions,
            timepoints=use_timepoints,
            regions=use_regions,
            channels=cfg['channels'] if cfg['channels'] else [],
        )

        masks_dir = _find_masks_directory(output_dir, ui)
        if masks_dir.exists():
            mask_files = list(masks_dir.rglob("*.tif*"))
            ui.info(f"Found {len(mask_files)} potential mask files in {masks_dir}")
            _log_sample_files(ui, mask_files, "mask files")

        ui.info("Starting interactive visualization...")
        ui.info("Use the sliders to adjust image intensity. Close windows to navigate between images.")
        viz_service.create_visualization_data(input_dir, masks_dir, selection)

    except Exception as e:
        logger.error(f"Visualization error: {e}")
        ui.error(f"Failed to run combined visualization: {e}")


def _find_mask_for_raw_file(raw_file, output_dir, ui: UserInterfacePort):
    """Find a matching mask file for a raw image file."""
    from pathlib import Path

    mask_dirs = [
        (output_dir / "combined_masks", "combined"),
        (output_dir / "masks", "individual"),
    ]

    for mask_dir, mask_type in mask_dirs:
        if not mask_dir.exists():
            continue
        candidates = list(mask_dir.rglob(f"*{raw_file.stem}*"))
        tiff_files = [
            m for m in candidates
            if m.is_file() and m.suffix.lower() in ['.tif', '.tiff']
        ]
        if tiff_files:
            ui.info(f"Found {mask_type} mask: {tiff_files[0]}")
            return tiff_files[0]

    return None


def _load_image_and_mask_to_napari(
    viewer, raw_file, output_dir, ui: UserInterfacePort
) -> bool:
    """Load a raw image and its mask (if found) into Napari viewer."""
    import numpy as np
    from PIL import Image

    try:
        image = np.array(Image.open(raw_file))
        viewer.add_image(image, name=f"Raw_{raw_file.name}", colormap='viridis')

        mask_file = _find_mask_for_raw_file(raw_file, output_dir, ui)
        if mask_file:
            try:
                mask_image = np.array(Image.open(mask_file))
                viewer.add_labels(
                    mask_image.astype(np.int32), name=f"Mask_{raw_file.name}"
                )
            except Exception as e:
                ui.info(f"Could not load mask {mask_file}: {e}")
        return True

    except Exception as e:
        logger.warning(f"Could not load {raw_file}: {e}")
        return False


def _run_napari_viewer(ui: UserInterfacePort, args: argparse.Namespace) -> None:
    """Run the Napari viewer feature.

    This function launches Napari for advanced image visualization and analysis.
    """
    try:
        import napari
        from percell.domain.services.data_selection_service import DataSelectionService
        from percell.domain.models import DatasetSelection
        from percell.domain.services.configuration_service import create_configuration_service
        from pathlib import Path

        if not hasattr(args, 'input') or not hasattr(args, 'output'):
            raise ValueError("Input and output directories must be specified")

        input_dir = Path(args.input)
        output_dir = Path(args.output)

        if not input_dir.exists():
            raise ValueError(f"Input directory does not exist: {input_dir}")

        # Load configuration
        config = create_configuration_service(_get_config_path())
        cfg = _load_data_selection_config(config)

        ui.info("Using configured selection:")
        ui.info(f"  Conditions: {cfg['conditions']}")
        ui.info(f"  Timepoints: {cfg['timepoints']}")
        ui.info(f"  Regions: {cfg['regions']}")
        ui.info(f"  Channels: {cfg['channels']}")

        # Scan available data
        data_service = DataSelectionService()
        all_files = data_service.scan_available_data(input_dir)
        ui.info(f"Found {len(all_files)} total .tif/.tiff files")
        _log_sample_files(ui, all_files, "files found")

        # Parse available data
        avail_cond, avail_time, avail_reg = data_service.parse_conditions_timepoints_regions(all_files)
        ui.info(f"Available conditions: {avail_cond}")
        ui.info(f"Available timepoints: {avail_time}")
        ui.info(f"Available regions: {avail_reg}")

        # Adjust selection - for Napari, always use available conditions
        use_conditions = avail_cond
        use_timepoints = _adjust_selection_to_available(cfg['timepoints'], avail_time)
        use_regions = _adjust_selection_to_available(cfg['regions'], avail_reg)

        ui.info("Adjusted selection to match available data:")
        ui.info(f"  Conditions: {use_conditions}")
        ui.info(f"  Timepoints: {use_timepoints}")
        ui.info(f"  Regions: {use_regions}")
        ui.info(f"  Channels: {cfg['channels']}")

        selection = DatasetSelection(
            root=input_dir,
            conditions=use_conditions,
            timepoints=use_timepoints,
            regions=use_regions,
            channels=cfg['channels'] if cfg['channels'] else None,
        )

        raw_files = data_service.generate_file_lists(selection)
        if not raw_files:
            ui.error("No raw data files found matching configured selection criteria")
            ui.info("This might be a mismatch between configured selection and available data")
            return

        ui.info(f"Found {len(raw_files)} images. Loading into Napari...")

        viewer = napari.Viewer()
        for raw_file in raw_files[:10]:
            _load_image_and_mask_to_napari(viewer, raw_file, output_dir, ui)

        viewer.reset_view()
        ui.info("Napari viewer launched. Close the viewer window when done.")
        napari.run()

    except ImportError:
        ui.error("Napari is not installed. Please install it with: pip install napari[all]")
    except Exception as e:
        logger.error(f"Napari viewer error: {e}")
        ui.error(f"Failed to run Napari viewer: {e}")