"""Unit tests for FlexibleDataSelectionService."""

import pytest
from pathlib import Path
from percell.domain.services.flexible_data_selection_service import (
    FlexibleDataSelectionService,
)
from percell.domain.models import DatasetSelection


class TestFlexibleDataSelectionService:
    """Test flexible data selection service."""

    @pytest.fixture
    def service(self):
        return FlexibleDataSelectionService()

    @pytest.fixture
    def leica_fixture_dir(self):
        """Path to Leica-style test fixture."""
        return (
            Path(__file__).parent.parent.parent
            / "fixtures"
            / "microscopy_data"
            / "leica_export"
        )

    @pytest.fixture
    def standard_fixture_dir(self):
        """Path to standard naming test fixture."""
        return (
            Path(__file__).parent.parent.parent
            / "fixtures"
            / "microscopy_data"
            / "standard_naming"
        )

    @pytest.fixture
    def nested_fixture_dir(self):
        """Path to nested structure test fixture."""
        return (
            Path(__file__).parent.parent.parent
            / "fixtures"
            / "microscopy_data"
            / "nested_structure"
        )

    def test_discover_all_files_leica_structure(
        self, service, leica_fixture_dir
    ):
        """Test file discovery with Leica export structure."""
        if not leica_fixture_dir.exists():
            pytest.skip("Test fixture not found")

        files_meta = service.discover_all_files(leica_fixture_dir)

        # Should find all .tif files
        assert len(files_meta) == 6  # 4 from ProjectA + 2 from ProjectB

        # Check that metadata is populated
        for file_path, meta in files_meta:
            assert meta.original_name is not None
            assert meta.project_folder is not None
            assert meta.full_path == file_path
            assert meta.relative_path is not None

    def test_discover_all_files_standard_structure(
        self, service, standard_fixture_dir
    ):
        """Test file discovery with standard naming structure."""
        if not standard_fixture_dir.exists():
            pytest.skip("Test fixture not found")

        files_meta = service.discover_all_files(standard_fixture_dir)

        # Should find all .tif files
        assert len(files_meta) == 6  # 4 from Condition1 + 2 from Condition2

    def test_discover_all_files_nested_structure(
        self, service, nested_fixture_dir
    ):
        """Test file discovery with nested structure."""
        if not nested_fixture_dir.exists():
            pytest.skip("Test fixture not found")

        files_meta = service.discover_all_files(nested_fixture_dir)

        # Should find all nested .tif files
        assert len(files_meta) == 6  # 2+2+2 from nested replicates

    def test_get_available_dimensions_leica(
        self, service, leica_fixture_dir
    ):
        """Test dimension extraction from Leica files."""
        if not leica_fixture_dir.exists():
            pytest.skip("Test fixture not found")

        files_meta = service.discover_all_files(leica_fixture_dir)
        dimensions = service.get_available_dimensions(files_meta)

        # Should have multiple dimensions
        assert "project_folder" in dimensions
        assert "channel" in dimensions
        assert "region" in dimensions

        # Check specific values
        assert set(dimensions["project_folder"]) == {"ProjectA", "ProjectB"}
        assert set(dimensions["channel"]) == {"ch00", "ch01"}

        # Check that dimensions are sorted
        if dimensions["channel"]:
            assert dimensions["channel"] == sorted(dimensions["channel"])

    def test_get_available_dimensions_standard(
        self, service, standard_fixture_dir
    ):
        """Test dimension extraction from standard naming files."""
        if not standard_fixture_dir.exists():
            pytest.skip("Test fixture not found")

        files_meta = service.discover_all_files(standard_fixture_dir)
        dimensions = service.get_available_dimensions(files_meta)

        # Check for timepoints in standard naming
        assert "timepoint" in dimensions
        assert set(dimensions["timepoint"]) == {"t0", "t1"}

        # Check for channels
        assert "channel" in dimensions
        assert set(dimensions["channel"]) == {"ch0", "ch1"}

    def test_group_files_by_project_folder(
        self, service, leica_fixture_dir
    ):
        """Test grouping files by project folder."""
        if not leica_fixture_dir.exists():
            pytest.skip("Test fixture not found")

        files_meta = service.discover_all_files(leica_fixture_dir)
        groups = service.group_files(files_meta, ["project_folder"])

        # Should have groups for each project folder
        assert len(groups) == 2  # ProjectA and ProjectB

        # Each group should have files
        for group_key, files in groups.items():
            assert len(files) > 0
            assert isinstance(group_key, tuple)

    def test_group_files_by_multiple_dimensions(
        self, service, leica_fixture_dir
    ):
        """Test grouping by multiple dimensions."""
        if not leica_fixture_dir.exists():
            pytest.skip("Test fixture not found")

        files_meta = service.discover_all_files(leica_fixture_dir)
        groups = service.group_files(
            files_meta, ["project_folder", "channel"]
        )

        # Should have groups for each combination
        assert len(groups) > 2  # At least ProjectA x channels

        # Verify group keys are tuples of correct length
        for group_key in groups.keys():
            assert len(group_key) == 2  # project_folder, channel

    def test_filter_files_by_channel(self, service, leica_fixture_dir):
        """Test filtering files by channel."""
        if not leica_fixture_dir.exists():
            pytest.skip("Test fixture not found")

        files_meta = service.discover_all_files(leica_fixture_dir)
        dimensions = service.get_available_dimensions(files_meta)

        if not dimensions.get("channel"):
            pytest.skip("No channels found in test data")

        # Filter to first channel only
        first_channel = dimensions["channel"][0]
        filtered = service.filter_files(
            files_meta, {"channel": [first_channel]}
        )

        # Should have fewer files than total
        assert len(filtered) < len(files_meta)
        assert len(filtered) > 0

        # Verify all filtered files are from the selected channel
        for file_path in filtered:
            meta = next(m for f, m in files_meta if f == file_path)
            assert meta.channel == first_channel

    def test_filter_files_by_project_folder(
        self, service, leica_fixture_dir
    ):
        """Test filtering files by project folder."""
        if not leica_fixture_dir.exists():
            pytest.skip("Test fixture not found")

        files_meta = service.discover_all_files(leica_fixture_dir)

        # Filter to ProjectA only
        filtered = service.filter_files(
            files_meta, {"project_folder": ["ProjectA"]}
        )

        assert len(filtered) == 4  # ProjectA has 4 files

    def test_filter_files_multiple_dimensions(
        self, service, leica_fixture_dir
    ):
        """Test filtering by multiple dimensions."""
        if not leica_fixture_dir.exists():
            pytest.skip("Test fixture not found")

        files_meta = service.discover_all_files(leica_fixture_dir)
        dimensions = service.get_available_dimensions(files_meta)

        filters = {}
        if dimensions.get("channel"):
            filters["channel"] = [dimensions["channel"][0]]
        if dimensions.get("project_folder"):
            filters["project_folder"] = [dimensions["project_folder"][0]]

        filtered = service.filter_files(files_meta, filters)

        # Should be more restrictive than single filter
        assert len(filtered) > 0

        # Verify all files match filters
        for file_path in filtered:
            meta = next(m for f, m in files_meta if f == file_path)
            for dim, values in filters.items():
                assert str(getattr(meta, dim)) in values

    def test_filter_files_no_filters_returns_all(
        self, service, leica_fixture_dir
    ):
        """Test that empty filter returns all files."""
        if not leica_fixture_dir.exists():
            pytest.skip("Test fixture not found")

        files_meta = service.discover_all_files(leica_fixture_dir)
        filtered = service.filter_files(files_meta, {})

        assert len(filtered) == len(files_meta)

    def test_validate_selection_valid(
        self, service, leica_fixture_dir
    ):
        """Test validation of valid selection."""
        if not leica_fixture_dir.exists():
            pytest.skip("Test fixture not found")

        files_meta = service.discover_all_files(leica_fixture_dir)

        # Create valid selection
        selection = DatasetSelection(
            root=leica_fixture_dir,
            dimension_filters={
                "project_folder": ["ProjectA"],
                "channel": ["ch00"],
            },
        )

        assert service.validate_selection(files_meta, selection) is True

    def test_validate_selection_invalid_dimension_value(
        self, service, leica_fixture_dir
    ):
        """Test validation rejects invalid dimension values."""
        if not leica_fixture_dir.exists():
            pytest.skip("Test fixture not found")

        files_meta = service.discover_all_files(leica_fixture_dir)

        # Create invalid selection
        selection = DatasetSelection(
            root=leica_fixture_dir,
            dimension_filters={
                "project_folder": ["NonExistentProject"],
            },
        )

        assert service.validate_selection(files_meta, selection) is False

    def test_validate_selection_empty_files(self, service):
        """Test validation fails with no files."""
        selection = DatasetSelection(
            root=Path("/tmp"),
            dimension_filters={"channel": ["ch00"]},
        )

        assert service.validate_selection([], selection) is False

    def test_get_dimension_summary(self, service, leica_fixture_dir):
        """Test dimension summary generation."""
        if not leica_fixture_dir.exists():
            pytest.skip("Test fixture not found")

        files_meta = service.discover_all_files(leica_fixture_dir)
        summary = service.get_dimension_summary(files_meta)

        # Should be a non-empty string
        assert isinstance(summary, str)
        assert len(summary) > 0
        assert "Discovered" in summary
        assert "files" in summary

        # Should mention dimensions
        assert "project_folder" in summary
        assert "channel" in summary

    def test_extract_project_folder_first_level(
        self, service, leica_fixture_dir
    ):
        """Test project folder extraction from first directory level."""
        if not leica_fixture_dir.exists():
            pytest.skip("Test fixture not found")

        files_meta = service.discover_all_files(leica_fixture_dir)

        # All files should have project_folder from first level
        for file_path, meta in files_meta:
            assert meta.project_folder in ["ProjectA", "ProjectB"]

    def test_extract_project_folder_nested(
        self, service, nested_fixture_dir
    ):
        """Test project folder extraction from nested structure."""
        if not nested_fixture_dir.exists():
            pytest.skip("Test fixture not found")

        files_meta = service.discover_all_files(nested_fixture_dir)

        # All files should have project_folder from first level only
        for file_path, meta in files_meta:
            assert meta.project_folder in ["Project1", "Project2"]
            # Should NOT include Replicate1/Replicate2
            assert "Replicate" not in meta.project_folder
