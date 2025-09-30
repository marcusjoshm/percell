"""Unit tests for refactored CLI services module."""
import argparse
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import pytest

from percell.application.cli_services import (
    _any_stage_selected,
    show_menu,
    validate_args
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


class TestAnyStageSelected:
    """Test the _any_stage_selected helper function."""

    def test_no_stages_selected(self):
        args = argparse.Namespace()
        assert _any_stage_selected(args) is False

    def test_single_stage_selected(self):
        args = argparse.Namespace(segmentation=True)
        assert _any_stage_selected(args) is True

    def test_multiple_stages_selected(self):
        args = argparse.Namespace(data_selection=True, analysis=True)
        assert _any_stage_selected(args) is True

    def test_only_false_stages(self):
        args = argparse.Namespace(
            data_selection=False,
            segmentation=False,
            process_single_cell=False
        )
        assert _any_stage_selected(args) is False

    def test_complete_workflow_selected(self):
        args = argparse.Namespace(complete_workflow=True)
        assert _any_stage_selected(args) is True


class TestShowMenu:
    """Test the show_menu function."""

    def test_returns_args_when_stage_selected(self):
        """When a stage is already selected, menu should be skipped."""
        ui = MockUI()
        args = argparse.Namespace(segmentation=True)

        result = show_menu(ui, args)

        assert result == args
        # No menu interaction should have occurred
        assert len(ui.info_calls) == 0
        assert len(ui.prompt_responses) == 0

    @patch('percell.application.cli_services.create_menu_system')
    def test_creates_and_shows_menu_system(self, mock_create_menu):
        """Test that show_menu creates and displays the menu system."""
        ui = MockUI()
        args = argparse.Namespace()
        expected_result = argparse.Namespace(test=True)

        # Mock the menu system
        mock_menu = Mock()
        mock_menu.show.return_value = expected_result
        mock_create_menu.return_value = mock_menu

        result = show_menu(ui, args)

        # Verify menu system was created and shown
        mock_create_menu.assert_called_once_with(ui)
        mock_menu.show.assert_called_once_with(args)
        assert result == expected_result

    @patch('percell.application.cli_services.create_menu_system')
    def test_handles_menu_system_errors(self, mock_create_menu):
        """Test that show_menu handles menu system errors gracefully."""
        ui = MockUI()
        args = argparse.Namespace()

        # Mock menu system to raise an exception
        mock_create_menu.side_effect = Exception("Menu system error")

        result = show_menu(ui, args)

        assert result is None
        assert len(ui.error_calls) > 0
        assert "Menu system error" in ui.error_calls[0]


class TestValidateArgs:
    """Test the validate_args function."""

    @patch('percell.application.paths_api.get_path')
    @patch('percell.domain.services.configuration_service.create_configuration_service')
    def test_loads_defaults_from_config(self, mock_create_config, mock_get_path):
        """Test that validate_args loads default directories from config."""
        ui = MockUI()
        args = argparse.Namespace()

        # Mock path and config service
        mock_get_path.return_value = "test/config.json"
        mock_config = Mock()
        mock_config.get.side_effect = lambda key, default: {
            "directories.input": "/test/input",
            "directories.output": "/test/output"
        }.get(key, default)
        mock_create_config.return_value = mock_config

        validate_args(args, ui)

        assert args.input == "/test/input"
        assert args.output == "/test/output"
        assert any("Using default input directory" in call for call in ui.info_calls)
        assert any("Using default output directory" in call for call in ui.info_calls)

    def test_raises_error_for_missing_input_non_interactive(self):
        """Test that missing input raises error in non-interactive mode."""
        ui = MockUI()
        args = argparse.Namespace(output="/test/output")

        with pytest.raises(ValueError, match="Input directory is required"):
            validate_args(args, ui)

    def test_raises_error_for_missing_output_non_interactive(self):
        """Test that missing output raises error in non-interactive mode."""
        ui = MockUI()
        args = argparse.Namespace(input="/test/input")

        with pytest.raises(ValueError, match="Output directory is required"):
            validate_args(args, ui)

    def test_allows_missing_paths_in_interactive_mode(self):
        """Test that missing paths are allowed in interactive mode."""
        ui = MockUI()
        args = argparse.Namespace(interactive=True)

        # Should not raise an exception
        validate_args(args, ui)

    def test_preserves_existing_args(self):
        """Test that existing input/output args are preserved."""
        ui = MockUI()
        args = argparse.Namespace(input="/existing/input", output="/existing/output")

        validate_args(args, ui)

        assert args.input == "/existing/input"
        assert args.output == "/existing/output"


class TestBackwardCompatibilityAliases:
    """Test that backward compatibility aliases work correctly."""

    @patch('percell.application.cli_services.show_menu')
    def test_configuration_menu_alias(self, mock_show_menu):
        """Test that show_configuration_menu calls show_menu."""
        from percell.application.cli_services import show_configuration_menu

        ui = MockUI()
        args = argparse.Namespace()
        expected_result = argparse.Namespace(test=True)
        mock_show_menu.return_value = expected_result

        result = show_configuration_menu(ui, args)

        mock_show_menu.assert_called_once_with(ui, args)
        assert result == expected_result

    @patch('percell.application.cli_services.show_menu')
    def test_workflows_menu_alias(self, mock_show_menu):
        """Test that show_workflows_menu calls show_menu."""
        from percell.application.cli_services import show_workflows_menu

        ui = MockUI()
        args = argparse.Namespace()
        expected_result = argparse.Namespace(test=True)
        mock_show_menu.return_value = expected_result

        result = show_workflows_menu(ui, args)

        mock_show_menu.assert_called_once_with(ui, args)
        assert result == expected_result


class TestVisualizationFunctions:
    """Test the visualization functions."""

    @patch('percell.application.cli_services.VisualizationService')
    @patch('percell.application.cli_services.build_container')
    @patch('percell.application.cli_services.Path')
    def test_run_combined_visualization_success(self, mock_path_cls, mock_build_container, mock_viz_service_cls):
        """Test successful combined visualization execution."""
        from percell.application.cli_services import _run_combined_visualization

        ui = MockUI()
        args = argparse.Namespace(input="/test/input", output="/test/output")

        # Mock path objects
        mock_input_path = Mock()
        mock_input_path.exists.return_value = True
        mock_output_path = Mock()
        mock_masks_path = Mock()
        mock_masks_path.exists.return_value = True

        mock_path_cls.side_effect = [mock_input_path, mock_output_path, mock_masks_path, mock_masks_path]

        # Mock container and services
        mock_container = Mock()
        mock_image_processor = Mock()
        mock_container.image_processing_port.return_value = mock_image_processor
        mock_build_container.return_value = mock_container

        mock_viz_service = Mock()
        mock_viz_service_cls.return_value = mock_viz_service

        # Should not raise an exception
        _run_combined_visualization(ui, args)

        # Verify visualization service was called
        mock_viz_service.create_visualization_data.assert_called_once()

    def test_run_combined_visualization_missing_args(self):
        """Test combined visualization with missing arguments."""
        from percell.application.cli_services import _run_combined_visualization

        ui = MockUI()
        args = argparse.Namespace()  # Missing input/output

        _run_combined_visualization(ui, args)

        # Should have logged an error
        assert len(ui.error_calls) > 0
        assert "Failed to run combined visualization" in ui.error_calls[0]

    @patch('percell.application.cli_services.napari')
    @patch('percell.application.cli_services.DataSelectionService')
    @patch('percell.application.cli_services.build_container')
    @patch('percell.application.cli_services.Path')
    def test_run_napari_viewer_success(self, mock_path_cls, mock_build_container,
                                     mock_data_service_cls, mock_napari):
        """Test successful Napari viewer execution."""
        from percell.application.cli_services import _run_napari_viewer

        ui = MockUI()
        args = argparse.Namespace(input="/test/input", output="/test/output")

        # Mock path objects
        mock_input_path = Mock()
        mock_input_path.exists.return_value = True
        mock_output_path = Mock()
        mock_path_cls.side_effect = [mock_input_path, mock_output_path, mock_output_path]

        # Mock container and services
        mock_container = Mock()
        mock_image_processor = Mock()
        mock_container.image_processing_port.return_value = mock_image_processor
        mock_build_container.return_value = mock_container

        mock_data_service = Mock()
        mock_data_service.generate_file_lists.return_value = [Path("/test/file1.tif")]
        mock_data_service_cls.return_value = mock_data_service

        mock_viewer = Mock()
        mock_napari.Viewer.return_value = mock_viewer

        # Mock image reading
        mock_image_processor.read_image.return_value = [[1, 2], [3, 4]]

        # Should not raise an exception
        _run_napari_viewer(ui, args)

        # Verify napari was used
        mock_napari.Viewer.assert_called_once()
        mock_napari.run.assert_called_once()