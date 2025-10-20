"""Integration tests for flexible data selection stage."""

import pytest
from pathlib import Path
from percell.application.stages.data_selection_stage import DataSelectionStage
from percell.domain.services.configuration_service import ConfigurationService
import logging
import tempfile
import shutil


class TestFlexibleDataSelectionStageIntegration:
    """Integration tests for the complete flexible data selection workflow."""

    @pytest.fixture
    def temp_output_dir(self):
        """Create a temporary output directory."""
        temp_dir = tempfile.mkdtemp()
        yield Path(temp_dir)
        # Cleanup
        shutil.rmtree(temp_dir, ignore_errors=True)

    @pytest.fixture
    def config_with_flexible_mode(self, temp_output_dir):
        """Create a config with flexible mode enabled."""
        config_path = temp_output_dir / "test_config.json"
        config = ConfigurationService(config_path)
        config.load(create_if_missing=True)
        config.set('data_selection.use_flexible_selection', True)
        return config

    @pytest.fixture
    def logger(self):
        """Create a test logger."""
        logger = logging.getLogger('test_flexible_data_selection')
        logger.setLevel(logging.INFO)
        return logger

    @pytest.fixture
    def leica_fixture_dir(self):
        """Path to Leica-style test fixture."""
        return (
            Path(__file__).parent.parent
            / "fixtures"
            / "microscopy_data"
            / "leica_export"
        )

    @pytest.fixture
    def standard_fixture_dir(self):
        """Path to standard naming test fixture."""
        return (
            Path(__file__).parent.parent
            / "fixtures"
            / "microscopy_data"
            / "standard_naming"
        )

    def test_flexible_workflow_discovery_leica(
        self, config_with_flexible_mode, logger, leica_fixture_dir, temp_output_dir
    ):
        """Test file and dimension discovery with Leica export structure."""
        if not leica_fixture_dir.exists():
            pytest.skip("Test fixture not found")

        stage = DataSelectionStage(config_with_flexible_mode, logger)
        stage.input_dir = leica_fixture_dir
        stage.output_dir = temp_output_dir

        # Run discovery
        success = stage._discover_files_and_dimensions()

        assert success is True
        assert len(stage.discovered_files) == 6  # 4 from ProjectA + 2 from ProjectB
        assert len(stage.available_dimensions) > 0
        assert 'project_folder' in stage.available_dimensions
        assert set(stage.available_dimensions['project_folder']) == {'ProjectA', 'ProjectB'}
        assert set(stage.available_dimensions['channel']) == {'ch00', 'ch01'}

    def test_flexible_workflow_discovery_standard(
        self, config_with_flexible_mode, logger, standard_fixture_dir, temp_output_dir
    ):
        """Test file and dimension discovery with standard naming structure."""
        if not standard_fixture_dir.exists():
            pytest.skip("Test fixture not found")

        stage = DataSelectionStage(config_with_flexible_mode, logger)
        stage.input_dir = standard_fixture_dir
        stage.output_dir = temp_output_dir

        # Run discovery
        success = stage._discover_files_and_dimensions()

        assert success is True
        assert len(stage.discovered_files) == 6  # 4 from Condition1 + 2 from Condition2
        assert 'timepoint' in stage.available_dimensions
        assert set(stage.available_dimensions['timepoint']) == {'t0', 't1'}

    def test_flexible_workflow_programmatic_selection(
        self, config_with_flexible_mode, logger, leica_fixture_dir, temp_output_dir
    ):
        """Test flexible workflow with programmatic selections (no user input)."""
        if not leica_fixture_dir.exists():
            pytest.skip("Test fixture not found")

        stage = DataSelectionStage(config_with_flexible_mode, logger)
        stage.input_dir = leica_fixture_dir
        stage.output_dir = temp_output_dir

        # Step 1: Discover files
        success = stage._discover_files_and_dimensions()
        assert success is True

        # Step 2: Make programmatic selections
        stage.condition_dimension = 'project_folder'
        stage.selected_conditions = ['ProjectA']  # Select only ProjectA

        if stage.available_dimensions.get('channel'):
            stage.analysis_channels = ['ch00']  # Select only ch00
            stage.segmentation_channel = 'ch00'

        if stage.available_dimensions.get('timepoint'):
            stage.selected_timepoints = stage.available_dimensions['timepoint']

        stage.selected_datasets = stage.available_dimensions.get('dataset', [])

        # Step 3: Create output directories
        success = stage._create_flexible_output_directories()
        assert success is True

        # Verify output directory structure
        raw_data_dir = temp_output_dir / "raw_data"
        assert raw_data_dir.exists()
        assert (raw_data_dir / "ProjectA").exists()
        assert not (raw_data_dir / "ProjectB").exists()  # Should not create unselected

    def test_flexible_workflow_file_filtering_and_copying(
        self, config_with_flexible_mode, logger, leica_fixture_dir, temp_output_dir
    ):
        """Test file filtering and copying in flexible workflow."""
        if not leica_fixture_dir.exists():
            pytest.skip("Test fixture not found")

        stage = DataSelectionStage(config_with_flexible_mode, logger)
        stage.input_dir = leica_fixture_dir
        stage.output_dir = temp_output_dir

        # Discover files
        stage._discover_files_and_dimensions()

        # Make selections
        stage.condition_dimension = 'project_folder'
        stage.selected_conditions = ['ProjectA']
        stage.analysis_channels = ['ch00']
        stage.segmentation_channel = 'ch00'
        stage.selected_timepoints = []
        stage.selected_datasets = stage.available_dimensions.get('dataset', [])

        # Create directories
        stage._create_flexible_output_directories()

        # Copy files
        success = stage._copy_filtered_files()
        assert success is True

        # Verify files were copied
        raw_data_dir = temp_output_dir / "raw_data" / "ProjectA"
        copied_files = list(raw_data_dir.glob("*.tif"))

        # Should have 2 files: ProjectA has 4 files total (2 regions × 2 channels)
        # But we filtered to ch00 only, so should have 2 files
        assert len(copied_files) == 2

        # Verify all copied files are from ch00
        for file in copied_files:
            assert 'ch00' in file.name

    def test_flexible_workflow_config_save(
        self, config_with_flexible_mode, logger, leica_fixture_dir, temp_output_dir
    ):
        """Test that flexible selections are saved to config."""
        if not leica_fixture_dir.exists():
            pytest.skip("Test fixture not found")

        stage = DataSelectionStage(config_with_flexible_mode, logger)
        stage.input_dir = leica_fixture_dir
        stage.output_dir = temp_output_dir

        # Discover and make selections
        stage._discover_files_and_dimensions()
        stage.condition_dimension = 'project_folder'
        stage.selected_conditions = ['ProjectA', 'ProjectB']
        stage.analysis_channels = ['ch00', 'ch01']
        stage.segmentation_channel = 'ch00'
        stage.selected_timepoints = []
        stage.selected_datasets = stage.available_dimensions.get('dataset', [])

        # Save to config
        stage._save_flexible_selections_to_config()

        # Verify config was updated
        assert config_with_flexible_mode.get('data_selection.condition_dimension') == 'project_folder'
        assert config_with_flexible_mode.get('data_selection.selected_conditions') == ['ProjectA', 'ProjectB']
        assert config_with_flexible_mode.get('data_selection.analysis_channels') == ['ch00', 'ch01']
        assert config_with_flexible_mode.get('data_selection.segmentation_channel') == 'ch00'

        # Verify flexible format is also saved
        dimension_filters = config_with_flexible_mode.get('data_selection.dimension_filters')
        assert dimension_filters is not None
        assert dimension_filters['project_folder'] == ['ProjectA', 'ProjectB']
        assert dimension_filters['channel'] == ['ch00', 'ch01']

    def test_flexible_vs_legacy_mode_flag(
        self, logger, leica_fixture_dir, temp_output_dir
    ):
        """Test that feature flag correctly switches between modes."""
        if not leica_fixture_dir.exists():
            pytest.skip("Test fixture not found")

        # Test with flexible mode enabled (default)
        config_path_flexible = temp_output_dir / "test_config_flexible.json"
        config_flexible = ConfigurationService(config_path_flexible)
        config_flexible.load(create_if_missing=True)
        config_flexible.set('data_selection.use_flexible_selection', True)
        stage_flexible = DataSelectionStage(config_flexible, logger)

        # Verify flexible service is initialized
        assert hasattr(stage_flexible, '_flexible_selection')
        assert hasattr(stage_flexible, 'discovered_files')
        assert hasattr(stage_flexible, 'available_dimensions')
        assert hasattr(stage_flexible, 'condition_dimension')

        # Test with legacy mode
        config_path_legacy = temp_output_dir / "test_config_legacy.json"
        config_legacy = ConfigurationService(config_path_legacy)
        config_legacy.load(create_if_missing=True)
        config_legacy.set('data_selection.use_flexible_selection', False)
        stage_legacy = DataSelectionStage(config_legacy, logger)

        # Verify legacy service is also initialized
        assert hasattr(stage_legacy, '_selection_service')
        assert hasattr(stage_legacy, 'experiment_metadata')

    def test_flexible_workflow_handles_empty_directory(
        self, config_with_flexible_mode, logger, temp_output_dir
    ):
        """Test that flexible workflow handles empty input directory gracefully."""
        empty_dir = temp_output_dir / "empty"
        empty_dir.mkdir(parents=True, exist_ok=True)

        stage = DataSelectionStage(config_with_flexible_mode, logger)
        stage.input_dir = empty_dir
        stage.output_dir = temp_output_dir / "output"

        # Should fail gracefully
        success = stage._discover_files_and_dimensions()
        assert success is False

    def test_flexible_workflow_multiple_dimensions(
        self, config_with_flexible_mode, logger, standard_fixture_dir, temp_output_dir
    ):
        """Test flexible workflow with multiple dimensions (timepoints, channels)."""
        if not standard_fixture_dir.exists():
            pytest.skip("Test fixture not found")

        stage = DataSelectionStage(config_with_flexible_mode, logger)
        stage.input_dir = standard_fixture_dir
        stage.output_dir = temp_output_dir

        # Discover files
        stage._discover_files_and_dimensions()

        # Make selections across multiple dimensions
        stage.condition_dimension = 'project_folder'
        stage.selected_conditions = ['Condition1']
        stage.analysis_channels = ['ch0', 'ch1']
        stage.segmentation_channel = 'ch0'
        stage.selected_timepoints = ['t0']  # Filter to specific timepoint
        stage.selected_datasets = stage.available_dimensions.get('dataset', [])

        # Create directories and copy files
        stage._create_flexible_output_directories()
        success = stage._copy_filtered_files()
        assert success is True

        # Verify filtering worked correctly
        raw_data_dir = temp_output_dir / "raw_data" / "Condition1"
        copied_files = list(raw_data_dir.glob("*.tif"))

        # Should have 2 files: Condition1 has region1 with t0 and t1 timepoints
        # Filtering to t0 only, with both channels (ch0, ch1) = 2 files
        assert len(copied_files) == 2

        # Verify all copied files are from t0
        for file in copied_files:
            assert 't0' in file.name
