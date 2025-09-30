"""Refactored menu system using command pattern and base classes.

This module provides a clean, extensible menu system that reduces duplication
and improves maintainability of the CLI interface.
"""

from __future__ import annotations

import argparse
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional, Dict, List, Any, Callable
import logging

from percell.ports.driving.user_interface_port import UserInterfacePort
from percell.application.ui_components import show_header, colorize, Colors
from percell.domain.exceptions import PercellError

logger = logging.getLogger(__name__)


@dataclass
class MenuItem:
    """Represents a menu item with display information and action."""

    key: str
    title: str
    description: str
    color: str = Colors.yellow
    action: Optional[Callable] = None
    submenu: Optional['Menu'] = None
    multiline_description: Optional[str] = None

    def display_text(self) -> List[str]:
        """Generate formatted display text for this menu item."""
        lines = []
        main_line = (
            f"{Colors.bold}{Colors.white}{self.key}.{Colors.reset} "
            f"{colorize(self.title, self.color)} "
            f"{colorize(f'- {self.description}', Colors.reset)}"
        )
        lines.append(main_line)

        if self.multiline_description:
            lines.append(f"   {colorize(self.multiline_description, Colors.reset)}")

        return lines

    def line_count(self) -> int:
        """Return the number of lines this item will take."""
        return 2 if self.multiline_description else 1


@dataclass
class MenuAction(ABC):
    """Base class for menu actions using command pattern."""

    @abstractmethod
    def execute(self, ui: UserInterfacePort, args: argparse.Namespace) -> Optional[argparse.Namespace]:
        """Execute the menu action.

        Args:
            ui: User interface for interaction
            args: Current command line arguments

        Returns:
            Updated args or None to exit
        """
        pass


class Menu:
    """Base menu class that handles common menu operations."""

    def __init__(
        self,
        title: str,
        items: List[MenuItem],
        ui: UserInterfacePort,
        parent: Optional['Menu'] = None
    ):
        self.title = title
        self.items = items
        self.ui = ui
        self.parent = parent
        self._item_map = {item.key: item for item in items}

    def show(self, args: argparse.Namespace) -> Optional[argparse.Namespace]:
        """Display the menu and handle user interaction.

        Returns:
            Updated args or None to exit
        """
        while True:
            self._display_menu()
            choice = self.ui.prompt(f"Select an option (1-{len(self.items)}): ").strip()

            result, should_exit = self._handle_choice(choice, args)
            if choice in ("q", "quit") or should_exit:
                return result

    def _display_menu(self) -> None:
        """Display the menu header and items."""
        show_header(self.ui)
        self.ui.info("")
        self.ui.info(colorize(f"{self.title.upper()}:", Colors.bold))
        self.ui.info("")

        # Display all menu items with their potentially multiline text
        item_lines_used = 0
        for item in self.items:
            display_lines = item.display_text()
            for line in display_lines:
                self.ui.info(line)
            item_lines_used += item.line_count()

        # Calculate lines used: header (7) + empty (1) + title (1) + empty (1) + items (item_lines_used) = 10 + item_lines_used
        # Target is 24 lines total including prompt, so padding needed is: 24 - 10 - item_lines_used - 1 (for prompt)
        lines_used = 10 + item_lines_used
        padding_needed = max(0, 24 - lines_used - 1)

        for _ in range(padding_needed):
            self.ui.info("")

    def _handle_choice(
        self,
        choice: str,
        args: argparse.Namespace
    ) -> tuple[Optional[argparse.Namespace], bool]:
        """Handle user choice and execute corresponding action.

        Returns:
            Tuple of (result, should_exit)
            - result: Result of action or None
            - should_exit: True if menu should exit, False to continue loop
        """
        if choice not in self._item_map:
            return None, False  # Invalid choice, continue loop

        item = self._item_map[choice]

        try:
            if item.submenu:
                result = item.submenu.show(args)
                return result, True  # Always exit after submenu
            elif item.action:
                result = item.action(self.ui, args)
                return result, True  # Always exit after successful action
            else:
                logger.warning(f"Menu item {choice} has no action or submenu")
                return None, False  # Continue loop

        except PercellError as e:
            self.ui.error(f"Error executing menu action: {e}")
            self.ui.prompt("Press Enter to continue...")
            return None, False  # Continue loop after error
        except Exception as e:
            self.ui.error(f"Unexpected error: {e}")
            logger.exception(f"Unexpected error in menu {self.title}")
            self.ui.prompt("Press Enter to continue...")
            return None, False  # Continue loop after error


class SetAttributeAction(MenuAction):
    """Action that sets attributes on the args namespace."""

    def __init__(self, attributes: Dict[str, Any]):
        self.attributes = attributes

    def execute(self, ui: UserInterfacePort, args: argparse.Namespace) -> Optional[argparse.Namespace]:
        for key, value in self.attributes.items():
            setattr(args, key, value)
        return args


class BackToParentAction(MenuAction):
    """Action that returns to the parent menu."""

    def __init__(self, parent_menu: Menu):
        self.parent_menu = parent_menu

    def execute(self, ui: UserInterfacePort, args: argparse.Namespace) -> Optional[argparse.Namespace]:
        return self.parent_menu.show(args)


class ExitAction(MenuAction):
    """Action that exits the application."""

    def execute(self, ui: UserInterfacePort, args: argparse.Namespace) -> Optional[argparse.Namespace]:
        return None


class ConfigurationDisplayAction(MenuAction):
    """Action that displays current configuration."""

    def execute(self, ui: UserInterfacePort, args: argparse.Namespace) -> Optional[argparse.Namespace]:
        try:
            from percell.application.config_display import display_current_configuration
            from percell.application.paths_api import get_path
            from percell.domain.services.configuration_service import (
    ConfigurationService,
    create_configuration_service
)

            try:
                config_path = str(get_path("config_default"))
            except Exception:
                config_path = "percell/config/config.json"

            config = Config(config_path)

            # Pass current args input/output if available
            current_input = getattr(args, 'input', None)
            current_output = getattr(args, 'output', None)

            display_current_configuration(ui, config, current_input, current_output)

        except Exception as e:
            ui.error(f"Error displaying configuration: {e}")
            ui.prompt("Press Enter to continue...")

        return args  # Return to main menu


class DirectorySetupAction(MenuAction):
    """Action that handles directory setup."""

    def execute(self, ui: UserInterfacePort, args: argparse.Namespace) -> Optional[argparse.Namespace]:
        try:
            from percell.application.directory_setup import load_config, set_default_directories
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

        return args  # Return to main menu


class VisualizationAction(MenuAction):
    """Base class for visualization actions."""

    def _get_directories(self, ui: UserInterfacePort, args: argparse.Namespace) -> tuple[str, str]:
        """Get input and output directories from args or config."""
        from percell.domain.services.configuration_service import (
    ConfigurationService,
    create_configuration_service
)
        from percell.application.paths_api import get_path

        try:
            config_path = str(get_path("config_default"))
        except Exception:
            config_path = "percell/config/config.json"

        config = Config(config_path)

        input_dir = getattr(args, 'input', None) or config.get("directories.input", "")
        output_dir = getattr(args, 'output', None) or config.get("directories.output", "")

        if not input_dir:
            input_dir = ui.prompt("Enter input directory path: ").strip()
        if not output_dir:
            output_dir = ui.prompt("Enter output directory path: ").strip()

        return input_dir, output_dir


class CombinedVisualizationAction(VisualizationAction):
    """Action for combined visualization display."""

    def execute(self, ui: UserInterfacePort, args: argparse.Namespace) -> Optional[argparse.Namespace]:
        try:
            input_dir, output_dir = self._get_directories(ui, args)

            # Set the directories in args for the visualization function
            args.input = input_dir
            args.output = output_dir

            # Import the visualization function (to be moved to domain)
            from percell.application.cli_services import _run_combined_visualization
            _run_combined_visualization(ui, args)

        except Exception as e:
            ui.error(f"Error running visualization: {e}")
            ui.prompt("Press Enter to continue...")

        return args  # Return to main menu


class NapariViewerAction(VisualizationAction):
    """Action for Napari viewer launch."""

    def execute(self, ui: UserInterfacePort, args: argparse.Namespace) -> Optional[argparse.Namespace]:
        try:
            input_dir, output_dir = self._get_directories(ui, args)

            # Set the directories in args for the napari function
            args.input = input_dir
            args.output = output_dir

            # Import the napari function (to be moved to domain)
            from percell.application.cli_services import _run_napari_viewer
            _run_napari_viewer(ui, args)

        except Exception as e:
            ui.error(f"Error running Napari viewer: {e}")
            ui.prompt("Press Enter to continue...")

        return args  # Return to main menu


class MainMenu(Menu):
    """Special main menu class with welcome message."""

    def _display_menu(self) -> None:
        """Display the main menu with welcome message."""
        show_header(self.ui)
        self.ui.info("")
        self.ui.info(colorize("              🔬 Welcome single-cell microscopy analysis user! 🔬               ", Colors.bold))
        self.ui.info("")
        self.ui.info(colorize(f"{self.title.upper()}:", Colors.bold))

        # Display all menu items with their potentially multiline text
        item_lines_used = 0
        for item in self.items:
            display_lines = item.display_text()
            for line in display_lines:
                self.ui.info(line)
            item_lines_used += item.line_count()

        # Calculate lines used: header (7) + empty (1) + welcome (1) + empty (1) + title (1) + items (item_lines_used) = 11 + item_lines_used
        # Target is 24 lines total including prompt, so padding needed is: 24 - 11 - item_lines_used - 1 (for prompt)
        lines_used = 11 + item_lines_used
        padding_needed = max(0, 24 - lines_used - 1)

        for _ in range(padding_needed):
            self.ui.info("")


class MenuFactory:
    """Factory for creating standard menu structures."""

    @staticmethod
    def create_main_menu(ui: UserInterfacePort) -> Menu:
        """Create the main application menu."""

        # Create configuration submenu
        config_menu = MenuFactory.create_configuration_menu(ui)

        # Create workflows submenu
        workflows_menu = MenuFactory.create_workflows_menu(ui)

        # Create visualization submenu
        visualization_menu = MenuFactory.create_visualization_menu(ui)

        # Create analysis submenu
        analysis_menu = MenuFactory.create_analysis_menu(ui)

        # Create plugins submenu
        plugins_menu = MenuFactory.create_plugins_menu(ui)

        # Create segmentation submenu
        segmentation_menu = MenuFactory.create_segmentation_menu(ui)

        # Create processing submenu
        processing_menu = MenuFactory.create_processing_menu(ui)

        # Create tracking submenu
        tracking_menu = MenuFactory.create_tracking_menu(ui)

        # Create utilities submenu
        utilities_menu = MenuFactory.create_utilities_menu(ui)

        main_items = [
            MenuItem("1", "Configuration", "Set input/output directories and analysis parameters",
                    action=lambda ui, args: config_menu.show(args)),
            MenuItem("2", "Workflows", "Pre-built and custom analysis workflows",
                    action=lambda ui, args: workflows_menu.show(args)),
            MenuItem("3", "Segmentation", "Single-cell segmentation tools",
                    action=lambda ui, args: segmentation_menu.show(args)),
            MenuItem("4", "Processing", "Data processing for downstream analysis",
                    action=lambda ui, args: processing_menu.show(args)),
            MenuItem("5", "Tracking", "Single-cell tracking tools",
                    action=lambda ui, args: tracking_menu.show(args)),
            MenuItem("6", "Visualization", "Image and mask visualization tools",
                    action=lambda ui, args: visualization_menu.show(args)),
            MenuItem("7", "Analysis", "Semi-automated thresholding and image analysis tools",
                    action=lambda ui, args: analysis_menu.show(args)),
            MenuItem("8", "Plugins", "Extend functionality with plugins",
                    action=lambda ui, args: plugins_menu.show(args)),
            MenuItem("9", "Utilities", "Cleanup and maintenance tools",
                    action=lambda ui, args: utilities_menu.show(args)),
            MenuItem("10", "Exit", "Quit the application", Colors.red,
                    action=lambda ui, args: ExitAction().execute(ui, args)),
        ]

        main_menu = MainMenu("Main Menu", main_items, ui)

        # Set parent references for submenus
        config_menu.parent = main_menu
        workflows_menu.parent = main_menu
        segmentation_menu.parent = main_menu
        processing_menu.parent = main_menu
        tracking_menu.parent = main_menu
        visualization_menu.parent = main_menu
        analysis_menu.parent = main_menu
        plugins_menu.parent = main_menu
        utilities_menu.parent = main_menu

        return main_menu

    @staticmethod
    def create_configuration_menu(ui: UserInterfacePort) -> Menu:
        """Create the configuration submenu."""
        items = [
            MenuItem("1", "I/O", "Set input/output directories",
                    action=lambda ui, args: DirectorySetupAction().execute(ui, args)),
            MenuItem("2", "Data Selection", "Select parameters (conditions, timepoints, channels, etc.)",
                    multiline_description="for processing and analysis",
                    action=lambda ui, args: SetAttributeAction({"data_selection": True, "return_to_main": True}).execute(ui, args)),
            MenuItem("3", "Current Configuration", "View current analysis configuration",
                    action=lambda ui, args: ConfigurationDisplayAction().execute(ui, args)),
            MenuItem("4", "Back to Main Menu", "", Colors.red,
                    action=lambda ui, args: args),
        ]
        return Menu("Configuration Menu", items, ui)

    @staticmethod
    def create_workflows_menu(ui: UserInterfacePort) -> Menu:
        """Create the workflows submenu."""
        items = [
            MenuItem("1", "Default Workflow", "Current default analysis workflow",
                    action=lambda ui, args: SetAttributeAction({
                        "data_selection": True,
                        "segmentation": True,
                        "process_single_cell": True,
                        "threshold_grouped_cells": True,
                        "measure_roi_area": True,
                        "analysis": True,
                        "complete_workflow": True
                    }).execute(ui, args)),
            MenuItem("2", "Advanced Workflow Builder", "Build custom analysis workflow",
                    action=lambda ui, args: SetAttributeAction({"advanced_workflow": True}).execute(ui, args)),
            MenuItem("3", "Back to Main Menu", "Return to main menu", Colors.red,
                    action=lambda ui, args: args),
        ]
        return Menu("Workflows Menu", items, ui)

    @staticmethod
    def create_segmentation_menu(ui: UserInterfacePort) -> Menu:
        """Create the segmentation submenu."""
        items = [
            MenuItem("1", "Cellpose", "Single-cell segmentation using Cellpose SAM GUI",
                    action=lambda ui, args: SetAttributeAction({"segmentation": True}).execute(ui, args)),
            MenuItem("2", "Back to Main Menu", "", Colors.red,
                    action=lambda ui, args: args),
        ]
        return Menu("Segmentation Menu", items, ui)

    @staticmethod
    def create_processing_menu(ui: UserInterfacePort) -> Menu:
        """Create the processing submenu."""
        items = [
            MenuItem("1", "Single-Cell Data Processing", "Tracking, resizing, extraction, grouping",
                    action=lambda ui, args: SetAttributeAction({"process_single_cell": True}).execute(ui, args)),
            MenuItem("2", "Back to Main Menu", "", Colors.red,
                    action=lambda ui, args: args),
        ]
        return Menu("Processing Menu", items, ui)

    @staticmethod
    def create_tracking_menu(ui: UserInterfacePort) -> Menu:
        """Create the tracking submenu."""
        items = [
            MenuItem("1", "Back to Main Menu", "", Colors.red,
                    action=lambda ui, args: args),
        ]
        return Menu("Tracking Menu", items, ui)

    @staticmethod
    def create_visualization_menu(ui: UserInterfacePort) -> Menu:
        """Create the visualization submenu."""
        items = [
            MenuItem("1", "Interactive Visualization", "Display raw images, masks, and overlays with LUT",
                    multiline_description="controls",
                    action=lambda ui, args: CombinedVisualizationAction().execute(ui, args)),
            MenuItem("2", "Napari Viewer", "Launch Napari for advanced image visualization and analysis",
                    action=lambda ui, args: NapariViewerAction().execute(ui, args)),
            MenuItem("3", "Back to Main Menu", "", Colors.red,
                    action=lambda ui, args: args),
        ]
        return Menu("Visualization Menu", items, ui)

    @staticmethod
    def create_analysis_menu(ui: UserInterfacePort) -> Menu:
        """Create the analysis submenu."""
        items = [
            MenuItem("1", "Threshold Grouped Cells", "Interactive Otsu autothresholding using ImageJ",
                    action=lambda ui, args: SetAttributeAction({"threshold_grouped_cells": True}).execute(ui, args)),
            MenuItem("2", "Measure Cell Area", "Measure area of cells in ROIs using ImageJ",
                    action=lambda ui, args: SetAttributeAction({"measure_roi_area": True}).execute(ui, args)),
            MenuItem("3", "Particle Analysis", "Analyze particles in segmented images using ImageJ",
                    action=lambda ui, args: SetAttributeAction({"analysis": True}).execute(ui, args)),
            MenuItem("4", "Back to Main Menu", "Return to main menu", Colors.red,
                    action=lambda ui, args: args),
        ]
        return Menu("Analysis Menu", items, ui)

    @staticmethod
    def create_plugins_menu(ui: UserInterfacePort) -> Menu:
        """Create the plugins submenu."""
        items = [
            MenuItem("1", "Auto Image Preprocessing", "Auto preprocessing for downstream analysis",
                    action=MenuFactory._create_plugin_action("auto_image_preprocessing")),
            MenuItem("2", "Back to Main Menu", "Return to main menu", Colors.red,
                    action=lambda ui, args: args),
        ]
        return Menu("Plugins Menu", items, ui)

    @staticmethod
    def create_utilities_menu(ui: UserInterfacePort) -> Menu:
        """Create the utilities submenu."""
        items = [
            MenuItem("1", "Cleanup", "Delete individual cells and masks to save space",
                    action=lambda ui, args: SetAttributeAction({"cleanup": True}).execute(ui, args)),
            MenuItem("2", "Back to Main Menu", "Return to main menu", Colors.red,
                    action=lambda ui, args: args),
        ]
        return Menu("Utilities Menu", items, ui)

    @staticmethod
    def _create_plugin_action(plugin_name: str) -> Callable:
        """Create an action for loading and running a plugin."""
        def plugin_action(ui: UserInterfacePort, args: argparse.Namespace) -> Optional[argparse.Namespace]:
            try:
                if plugin_name == "auto_image_preprocessing":
                    from percell.plugins.auto_image_preprocessing import show_auto_image_preprocessing_plugin
                    result = show_auto_image_preprocessing_plugin(ui, args)
                    return result
                else:
                    ui.error(f"Unknown plugin: {plugin_name}")
                    return None
            except ImportError as e:
                ui.error(f"Failed to load plugin {plugin_name}: {e}")
                ui.prompt("Press Enter to continue...")
                return None
            except Exception as e:
                ui.error(f"Error running plugin {plugin_name}: {e}")
                ui.prompt("Press Enter to continue...")
                return None
        return plugin_action


def create_menu_system(ui: UserInterfacePort) -> Menu:
    """Create the complete menu system."""
    return MenuFactory.create_main_menu(ui)