"""Configuration display service for showing current settings."""

from __future__ import annotations

from typing import Optional
from percell.domain.services.configuration_service import (
    ConfigurationService,
    create_configuration_service
)
from percell.ports.driving.user_interface_port import UserInterfacePort
from percell.application.ui_components import colorize, Colors


def display_current_configuration(ui: UserInterfacePort, config: Config, args_input: Optional[str] = None, args_output: Optional[str] = None) -> None:
    """Display current configuration including directories and data selections."""

    ui.info("")
    ui.info(colorize("CURRENT CONFIGURATION:", Colors.bold))
    ui.info("=" * 50)
    ui.info("")

    # Display directories
    ui.info(colorize("DIRECTORIES:", Colors.bold))

    # Current session directories (from args if available)
    if args_input:
        ui.info(f"  Current Input:  {colorize(args_input, Colors.green)}")
    else:
        config_input = config.get("directories.input", "")
        if config_input:
            ui.info(f"  Saved Input:    {colorize(config_input, Colors.yellow)}")
        else:
            ui.info(f"  Input:          {colorize('Not set', Colors.red)}")

    if args_output:
        ui.info(f"  Current Output: {colorize(args_output, Colors.green)}")
    else:
        config_output = config.get("directories.output", "")
        if config_output:
            ui.info(f"  Saved Output:   {colorize(config_output, Colors.yellow)}")
        else:
            ui.info(f"  Output:         {colorize('Not set', Colors.red)}")

    # Recent directories
    recent_inputs = config.get("directories.recent_inputs", [])
    recent_outputs = config.get("directories.recent_outputs", [])

    if recent_inputs:
        ui.info(f"  Recent Inputs:  {len(recent_inputs)} saved")
    if recent_outputs:
        ui.info(f"  Recent Outputs: {len(recent_outputs)} saved")

    ui.info("")

    # Display data selection settings
    ui.info(colorize("DATA SELECTION:", Colors.bold))

    selected_datatype = config.get("data_selection.selected_datatype")
    if selected_datatype:
        ui.info(f"  Data Type: {colorize(selected_datatype, Colors.green)}")
    else:
        ui.info(f"  Data Type: {colorize('Not selected', Colors.red)}")

    selected_conditions = config.get("data_selection.selected_conditions", [])
    if selected_conditions:
        ui.info(f"  Conditions: {colorize(', '.join(selected_conditions), Colors.green)}")
    else:
        ui.info(f"  Conditions: {colorize('None selected', Colors.red)}")

    selected_regions = config.get("data_selection.selected_regions", [])
    if selected_regions:
        ui.info(f"  Regions: {colorize(', '.join(selected_regions), Colors.green)}")
    else:
        ui.info(f"  Regions: {colorize('None selected', Colors.red)}")

    selected_timepoints = config.get("data_selection.selected_timepoints", [])
    if selected_timepoints:
        ui.info(f"  Timepoints: {colorize(', '.join(map(str, selected_timepoints)), Colors.green)}")
    else:
        ui.info(f"  Timepoints: {colorize('None selected', Colors.red)}")

    # Channel information
    segmentation_channel = config.get("data_selection.segmentation_channel")
    analysis_channels = config.get("data_selection.analysis_channels", [])

    if segmentation_channel:
        ui.info(f"  Segmentation Channel: {colorize(segmentation_channel, Colors.green)}")
    else:
        ui.info(f"  Segmentation Channel: {colorize('Not selected', Colors.red)}")

    if analysis_channels:
        ui.info(f"  Analysis Channels: {colorize(', '.join(analysis_channels), Colors.green)}")
    else:
        ui.info(f"  Analysis Channels: {colorize('None selected', Colors.red)}")

    ui.info("")
    ui.info("=" * 50)
    ui.info("")
    ui.info("Press Enter to return to main menu...")
    ui.prompt("")