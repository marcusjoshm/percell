import pytest

from percell.domain import FileNamingService, FileMetadata


@pytest.fixture()
def svc() -> FileNamingService:
    return FileNamingService()


class TestFileNamingServiceParsing:
    @pytest.mark.parametrize(
        "filename, expected",
        [
            (
                "R_1_Merged_ch01_t00.tif",
                {
                    "region": "R_1_Merged",
                    "channel": "ch01",
                    "timepoint": "t00",
                    "extension": ".tif",
                },
            ),
            (
                "ExperimentX_s2_z3_ch1_t10.tiff",
                {
                    "region": "ExperimentX",
                    "channel": "ch1",
                    "timepoint": "t10",
                    "extension": ".tiff",
                    "z_index": 3,
                },
            ),
        ],
    )
    def test_parse_microscopy_filename_valid(self, svc: FileNamingService, filename: str, expected: dict):
        meta = svc.parse_microscopy_filename(filename)
        assert isinstance(meta, FileMetadata)
        assert meta.original_name == filename
        for key, value in expected.items():
            assert getattr(meta, key) == value

    def test_parse_microscopy_filename_invalid_extension(self, svc: FileNamingService):
        with pytest.raises(NotImplementedError):
            # Implementation should raise a domain error or return a controlled result;
            # for now, ensure the method is exercised during TDD.
            svc.parse_microscopy_filename("image.png")


class TestFileNamingServiceROIExtraction:
    @pytest.mark.parametrize(
        "roi_name, expected",
        [
            (
                "ROIs_R_1_Merged_ch01_t00_rois.zip",
                {"region": "R_1_Merged", "channel": "ch01", "timepoint": "t00"},
            ),
            (
                "ROIs_Sample_A_ch00_t12.zip",
                {"region": "Sample_A", "channel": "ch00", "timepoint": "t12"},
            ),
        ],
    )
    def test_extract_metadata_from_roi_name(self, svc: FileNamingService, roi_name: str, expected: dict):
        tokens = svc.extract_metadata_from_name(roi_name)
        for key, value in expected.items():
            assert tokens.get(key) == value


class TestFileNamingServiceValidationAndGeneration:
    @pytest.mark.parametrize(
        "filename, valid",
        [
            ("R_1_Merged_ch01_t00.tif", True),
            ("RegionOnly.tif", False),
            ("Region_ch01.tif", False),
            ("Region_t00.tif", False),
        ],
    )
    def test_validate_naming_convention(self, svc: FileNamingService, filename: str, valid: bool):
        assert svc.validate_naming_convention(filename) is valid

    @pytest.mark.parametrize(
        "meta, expected",
        [
            (
                FileMetadata(
                    original_name="R_1_Merged_ch01_t00.tif",
                    region="R_1_Merged",
                    channel="ch01",
                    timepoint="t00",
                    extension=".tif",
                ),
                "R_1_Merged_ch01_t00.tif",
            ),
            (
                FileMetadata(
                    original_name="ExperimentX_s2_z3_ch1_t10.tiff",
                    region="ExperimentX",
                    channel="ch1",
                    timepoint="t10",
                    extension=".tiff",
                    z_index=3,
                ),
                "ExperimentX_ch1_t10.tiff",
            ),
        ],
    )
    def test_generate_output_filename(self, svc: FileNamingService, meta: FileMetadata, expected: str):
        assert svc.generate_output_filename(meta) == expected


