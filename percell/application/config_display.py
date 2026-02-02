"""Configuration display service for showing current settings."""

from __future__ import annotations

from typing import Optional
from percell.domain.services.configuration_service import (
    ConfigurationService,
    create_configuration_service
)
from percell.ports.driving.user_interface_port import UserInterfacePort
from percell.application.ui_components import colorize, Colors


def _format_value(value, empty_text: str = "Not set") -> str:
    """Format a value with appropriate color based on whether it's set."""
    if value:
        return colorize(value, Colors.green)
    return colorize(empty_text, Colors.red)


def _format_list(items: list, empty_text: str = "None selected") -> str:
    """Format a list with appropriate color based on whether it has items."""
    if items:
        return colorize(", ".join(map(str, items)), Colors.green)
    return colorize(empty_text, Colors.red)


def _display_directory(
    ui: UserInterfacePort,
    label: str,
    args_value: Optional[str],
    config_value: str,
) -> None:
    """Display a directory setting with current/saved/not-set states."""
    if args_value:
        ui.info(f"  Current {label}:  {colorize(args_value, Colors.green)}")
    elif config_value:
        ui.info(f"  Saved {label}:    {colorize(config_value, Colors.yellow)}")
    else:
        ui.info(f"  {label}:          {colorize('Not set', Colors.red)}")


def _display_directories(
    ui: UserInterfacePort,
    config: ConfigurationService,
    args_input: Optional[str],
    args_output: Optional[str],
) -> None:
    """Display the directories section."""
    ui.info(colorize("DIRECTORIES:", Colors.bold))

    _display_directory(
        ui, "Input", args_input, config.get("directories.input", "")
    )
    _display_directory(
        ui, "Output", args_output, config.get("directories.output", "")
    )

    recent_inputs = config.get("directories.recent_inputs", [])
    recent_outputs = config.get("directories.recent_outputs", [])

    if recent_inputs:
        ui.info(f"  Recent Inputs:  {len(recent_inputs)} saved")
    if recent_outputs:
        ui.info(f"  Recent Outputs: {len(recent_outputs)} saved")


def _display_data_selection(ui: UserInterfacePort, config: ConfigurationService) -> None:
    """Display the data selection section."""
    ui.info(colorize("DATA SELECTION:", Colors.bold))

    datatype = config.get("data_selection.selected_datatype")
    ui.info(f"  Data Type: {_format_value(datatype, 'Not selected')}")

    conditions = config.get("data_selection.selected_conditions", [])
    ui.info(f"  Conditions: {_format_list(conditions)}")

    regions = config.get("data_selection.selected_regions", [])
    ui.info(f"  Regions: {_format_list(regions)}")

    timepoints = config.get("data_selection.selected_timepoints", [])
    ui.info(f"  Timepoints: {_format_list(timepoints)}")

    seg_channel = config.get("data_selection.segmentation_channel")
    ui.info(f"  Segmentation Channel: {_format_value(seg_channel, 'Not selected')}")

    analysis_channels = config.get("data_selection.analysis_channels", [])
    ui.info(f"  Analysis Channels: {_format_list(analysis_channels)}")


def display_current_configuration(
    ui: UserInterfacePort,
    config: ConfigurationService,
    args_input: Optional[str] = None,
    args_output: Optional[str] = None,
) -> None:
    """Display current configuration including directories and data selections."""
    ui.info("")
    ui.info(colorize("CURRENT CONFIGURATION:", Colors.bold))
    ui.info("=" * 50)
    ui.info("")

    _display_directories(ui, config, args_input, args_output)
    ui.info("")

    _display_data_selection(ui, config)

    ui.info("")
    ui.info("=" * 50)
    ui.info("")
    ui.info("Press Enter to return to main menu...")
    ui.prompt("")