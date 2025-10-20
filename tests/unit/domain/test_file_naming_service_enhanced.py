"""Test enhanced filename parsing for various conventions."""

import pytest
from percell.domain.services.file_naming_service import FileNamingService


class TestEnhancedFileNaming:
    """Test parsing of various filename conventions."""

    @pytest.fixture
    def service(self):
        return FileNamingService()

    def test_parse_leica_style_filename(self, service):
        """Test parsing Leica export style filenames."""
        meta = service.parse_microscopy_filename(
            "18h dTAG13_Merged_z00_ch00.tif"
        )

        assert meta.dataset == "18h dTAG13_Merged"
        assert meta.channel == "ch00"
        assert meta.z_index == 0
        assert meta.extension == ".tif"

    def test_parse_leica_multiple_channels(self, service):
        """Test parsing different channels."""
        meta1 = service.parse_microscopy_filename(
            "18h dTAG13_Merged_z00_ch00.tif"
        )
        meta2 = service.parse_microscopy_filename(
            "18h dTAG13_Merged_z00_ch01.tif"
        )

        assert meta1.dataset == meta2.dataset
        assert meta1.channel == "ch00"
        assert meta2.channel == "ch01"

    def test_parse_region_with_spaces(self, service):
        """Test parsing regions with spaces in names."""
        meta = service.parse_microscopy_filename(
            "No dTAG13_Merged_z00_ch00.tif"
        )

        assert meta.dataset == "No dTAG13_Merged"
        assert meta.channel == "ch00"

    def test_parse_3h_treatment_filename(self, service):
        """Test parsing 3h treatment filename from fixtures."""
        meta = service.parse_microscopy_filename(
            "3h treatment_Merged_z00_ch00.tif"
        )

        assert meta.dataset == "3h treatment_Merged"
        assert meta.channel == "ch00"
        assert meta.z_index == 0

    def test_parse_standard_naming(self, service):
        """Test parsing standard underscore-based naming."""
        meta = service.parse_microscopy_filename("region1_t0_ch1_z5.tif")

        assert meta.dataset == "region1"
        assert meta.timepoint == "t0"
        assert meta.channel == "ch1"
        assert meta.z_index == 5

    def test_parse_minimal_filename(self, service):
        """Test parsing filename with minimal metadata."""
        meta = service.parse_microscopy_filename("experiment_ch00.tif")

        assert meta.dataset == "experiment"
        assert meta.channel == "ch00"
        assert meta.timepoint is None
        assert meta.z_index is None

    def test_parse_with_timepoint(self, service):
        """Test parsing filename with timepoint."""
        meta = service.parse_microscopy_filename("data_t5_ch2.tif")

        assert meta.dataset == "data"
        assert meta.timepoint == "t5"
        assert meta.channel == "ch2"

    def test_parse_case_insensitive(self, service):
        """Test that parsing is case insensitive."""
        meta1 = service.parse_microscopy_filename("data_CH00_T0.tif")
        meta2 = service.parse_microscopy_filename("data_ch00_t0.tif")

        assert meta1.channel == meta2.channel
        assert meta1.timepoint == meta2.timepoint

    def test_parse_without_underscore_prefix(self, service):
        """Test parsing markers without underscore prefix."""
        meta = service.parse_microscopy_filename("experiment z00 ch01.tif")

        assert "experiment" in meta.dataset
        assert meta.channel == "ch01"
        assert meta.z_index == 0

    def test_parse_nested_fixture_filename(self, service):
        """Test parsing nested structure fixture filename."""
        meta = service.parse_microscopy_filename("data_t0_ch0.tif")

        assert meta.dataset == "data"
        assert meta.timepoint == "t0"
        assert meta.channel == "ch0"

    def test_parse_multidigit_indices(self, service):
        """Test parsing filenames with multi-digit indices."""
        meta = service.parse_microscopy_filename("sample_t10_ch15_z99.tif")

        assert meta.dataset == "sample"
        assert meta.timepoint == "t10"
        assert meta.channel == "ch15"
        assert meta.z_index == 99

    def test_parse_tiff_extension(self, service):
        """Test parsing .tiff extension."""
        meta = service.parse_microscopy_filename(
            "experiment_ch00.tiff"
        )

        assert meta.dataset == "experiment"
        assert meta.channel == "ch00"
        assert meta.extension == ".tiff"

    def test_parse_invalid_extension_raises_error(self, service):
        """Test that invalid extensions raise ValueError."""
        with pytest.raises(ValueError, match="Unsupported extension"):
            service.parse_microscopy_filename("experiment.png")

    def test_parse_preserves_original_name(self, service):
        """Test that original filename is preserved."""
        filename = "18h dTAG13_Merged_z00_ch00.tif"
        meta = service.parse_microscopy_filename(filename)

        assert meta.original_name == filename

    def test_parse_complex_region_name(self, service):
        """Test parsing with complex region names."""
        meta = service.parse_microscopy_filename(
            "A549 UFD1L KO_Merged_z00_ch00.tif"
        )

        assert "A549 UFD1L KO" in meta.dataset or "A549 UFD1L KO_Merged" == meta.dataset
        assert meta.channel == "ch00"
        assert meta.z_index == 0
