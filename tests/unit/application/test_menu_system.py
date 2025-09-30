"""Unit tests for the new menu system."""
import argparse
from unittest.mock import Mock, patch
import pytest

from percell.application.menu.menu_system import (
    MenuItem,
    Menu,
    SetAttributeAction,
    ExitAction,
    MenuFactory,
    create_menu_system
)
from percell.ports.driving.user_interface_port import UserInterfacePort


class MockUI(UserInterfacePort):
    """Mock UI for testing."""

    def __init__(self):
        self.info_calls = []
        self.prompt_responses = []
        self.prompt_call_count = 0
        self.error_calls = []

    def info(self, message: str) -> None:
        self.info_calls.append(message)

    def error(self, message: str) -> None:
        self.error_calls.append(message)

    def prompt(self, message: str) -> str:
        if self.prompt_call_count < len(self.prompt_responses):
            response = self.prompt_responses[self.prompt_call_count]
            self.prompt_call_count += 1
            return response
        return ""

    def setup_responses(self, responses):
        """Set up predetermined responses for prompts."""
        self.prompt_responses = responses
        self.prompt_call_count = 0


class TestMenuItem:
    """Test the MenuItem class."""

    def test_creates_menu_item_with_defaults(self):
        from percell.application.ui_components import Colors
        item = MenuItem("1", "Test", "Description")
        assert item.key == "1"
        assert item.title == "Test"
        assert item.description == "Description"
        assert item.color == Colors.yellow

    def test_creates_menu_item_with_custom_color(self):
        from percell.application.ui_components import Colors
        item = MenuItem("1", "Test", "Description", Colors.red)
        assert item.color == Colors.red

    def test_display_text_formatting(self):
        item = MenuItem("1", "Test", "Description")
        text = item.display_text()
        assert "1." in text
        assert "Test" in text
        assert "Description" in text


class TestSetAttributeAction:
    """Test the SetAttributeAction class."""

    def test_sets_single_attribute(self):
        action = SetAttributeAction({"test_attr": True})
        ui = MockUI()
        args = argparse.Namespace()

        result = action.execute(ui, args)

        assert result == args
        assert args.test_attr is True

    def test_sets_multiple_attributes(self):
        action = SetAttributeAction({
            "attr1": True,
            "attr2": "value",
            "attr3": 42
        })
        ui = MockUI()
        args = argparse.Namespace()

        result = action.execute(ui, args)

        assert result == args
        assert args.attr1 is True
        assert args.attr2 == "value"
        assert args.attr3 == 42


class TestExitAction:
    """Test the ExitAction class."""

    def test_returns_none(self):
        action = ExitAction()
        ui = MockUI()
        args = argparse.Namespace()

        result = action.execute(ui, args)
        assert result is None


class TestMenu:
    """Test the Menu class."""

    def test_creates_menu_with_items(self):
        ui = MockUI()
        items = [
            MenuItem("1", "Option 1", "First option"),
            MenuItem("2", "Option 2", "Second option"),
        ]
        menu = Menu("Test Menu", items, ui)

        assert menu.title == "Test Menu"
        assert len(menu.items) == 2
        assert menu.ui == ui

    def test_handles_valid_choice(self):
        ui = MockUI()
        ui.setup_responses(["1"])

        action_called = False

        def test_action(ui, args):
            nonlocal action_called
            action_called = True
            return args

        items = [
            MenuItem("1", "Option 1", "First option", action=test_action),
        ]
        menu = Menu("Test Menu", items, ui)
        args = argparse.Namespace()

        result = menu.show(args)

        assert action_called
        assert result == args

    def test_handles_invalid_choice_loops(self):
        ui = MockUI()
        ui.setup_responses(["invalid", "1"])

        executed = False

        def test_action(ui, args):
            nonlocal executed
            executed = True
            return args

        items = [
            MenuItem("1", "Exit", "Exit option", action=test_action),
        ]
        menu = Menu("Test Menu", items, ui)
        args = argparse.Namespace()

        result = menu.show(args)

        assert executed
        assert result == args

    @patch('percell.application.menu.menu_system.show_header')
    def test_displays_menu_header(self, mock_header):
        ui = MockUI()
        ui.setup_responses(["1"])

        items = [
            MenuItem("1", "Exit", "Exit", action=lambda ui, args: args),
        ]
        menu = Menu("Test Menu", items, ui)
        args = argparse.Namespace()

        menu.show(args)

        mock_header.assert_called_with(ui)
        assert any("TEST MENU:" in call for call in ui.info_calls)

    def test_handles_action_exceptions(self):
        ui = MockUI()
        ui.setup_responses(["1", "", "2"])  # Added empty string for "Press Enter to continue"

        def failing_action(ui, args):
            raise Exception("Test error")

        def exit_action(ui, args):
            return args

        items = [
            MenuItem("1", "Fail", "Failing option", action=failing_action),
            MenuItem("2", "Exit", "Exit option", action=exit_action),
        ]
        menu = Menu("Test Menu", items, ui)
        args = argparse.Namespace()

        result = menu.show(args)

        assert result == args
        assert len(ui.error_calls) > 0
        assert "Unexpected error" in ui.error_calls[0]


class TestMenuFactory:
    """Test the MenuFactory class."""

    @patch('percell.application.menu.menu_system.show_header')
    def test_creates_main_menu(self, mock_header):
        ui = MockUI()
        main_menu = MenuFactory.create_main_menu(ui)

        assert main_menu.title == "Main Menu"
        assert len(main_menu.items) == 10  # 9 options + exit

        # Check that main menu items exist
        menu_keys = [item.key for item in main_menu.items]
        expected_keys = ["1", "2", "3", "4", "5", "6", "7", "8", "9", "10"]
        assert menu_keys == expected_keys

    def test_creates_configuration_menu(self):
        ui = MockUI()
        config_menu = MenuFactory.create_configuration_menu(ui)

        assert config_menu.title == "Configuration Menu"
        assert len(config_menu.items) == 4

        menu_titles = [item.title for item in config_menu.items]
        assert "I/O" in menu_titles
        assert "Data Selection" in menu_titles
        assert "Current Configuration" in menu_titles
        assert "Back to Main Menu" in menu_titles

    def test_creates_workflows_menu(self):
        ui = MockUI()
        workflows_menu = MenuFactory.create_workflows_menu(ui)

        assert workflows_menu.title == "Workflows Menu"
        assert len(workflows_menu.items) == 3

        menu_titles = [item.title for item in workflows_menu.items]
        assert "Default Workflow" in menu_titles
        assert "Advanced Workflow Builder" in menu_titles
        assert "Back to Main Menu" in menu_titles


class TestMenuIntegration:
    """Integration tests for the menu system."""

    @patch('percell.application.menu.menu_system.show_header')
    def test_menu_system_creation(self, mock_header):
        ui = MockUI()
        menu_system = create_menu_system(ui)

        assert isinstance(menu_system, Menu)
        assert menu_system.title == "Main Menu"

    @patch('percell.application.menu.menu_system.show_header')
    def test_exit_option_works(self, mock_header):
        ui = MockUI()
        ui.setup_responses(["q"])  # Use quit shortcut instead of navigating to exit menu

        menu_system = create_menu_system(ui)
        args = argparse.Namespace()

        result = menu_system.show(args)
        assert result is None

    @patch('percell.application.menu.menu_system.show_header')
    def test_segmentation_option_sets_attribute(self, mock_header):
        ui = MockUI()
        ui.setup_responses(["3", "q"])  # Segmentation option -> quit

        menu_system = create_menu_system(ui)
        args = argparse.Namespace()

        result = menu_system.show(args)

        assert result == args
        assert hasattr(result, 'segmentation')
        assert result.segmentation is True

    @patch('percell.application.menu.menu_system.show_header')
    def test_default_workflow_sets_multiple_attributes(self, mock_header):
        ui = MockUI()
        ui.setup_responses(["2", "1", "q"])  # Workflows menu -> Default workflow -> quit

        menu_system = create_menu_system(ui)
        args = argparse.Namespace()

        result = menu_system.show(args)

        assert result == args
        assert result.data_selection is True
        assert result.segmentation is True
        assert result.process_single_cell is True
        assert result.threshold_grouped_cells is True
        assert result.measure_roi_area is True
        assert result.analysis is True
        assert result.complete_workflow is True


class TestMenuActions:
    """Test specific menu actions."""

    @patch('percell.application.config_display.display_current_configuration')
    @patch('percell.application.paths_api.get_path')
    @patch('percell.application.config_api.Config')
    def test_configuration_display_action(self, mock_config, mock_get_path, mock_display):
        from percell.application.menu.menu_system import ConfigurationDisplayAction

        ui = MockUI()
        args = argparse.Namespace(input="/test/input", output="/test/output")

        mock_get_path.return_value = "test/config.json"
        mock_config_instance = Mock()
        mock_config.return_value = mock_config_instance

        action = ConfigurationDisplayAction()
        result = action.execute(ui, args)

        mock_display.assert_called_once()
        assert result is None  # Should stay in current menu

    @patch('percell.application.directory_setup.set_default_directories')
    @patch('percell.application.directory_setup.load_config')
    @patch('percell.application.paths_api.get_path')
    def test_directory_setup_action(self, mock_get_path, mock_load_config, mock_setup):
        from percell.application.menu.menu_system import DirectorySetupAction

        ui = MockUI()
        args = argparse.Namespace()

        mock_get_path.return_value = "test/config.json"
        mock_config = {"test": "config"}
        mock_load_config.return_value = mock_config
        mock_setup.return_value = ("/input/path", "/output/path")

        action = DirectorySetupAction()
        result = action.execute(ui, args)

        mock_setup.assert_called_once_with(mock_config, "test/config.json")
        assert args.input == "/input/path"
        assert args.output == "/output/path"
        assert result is None  # Should stay in current menu