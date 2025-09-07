import os
from pathlib import Path

import pytest

from percell.domain import DataSelectionService
from percell.domain.models import DatasetSelection


@pytest.fixture()
def tmp_dataset(tmp_path: Path) -> Path:
    # Create structure: root/CondA/ files
    root = tmp_path / "dataset"
    (root / "CondA").mkdir(parents=True)
    (root / "CondB").mkdir(parents=True)

    files = [
        root / "CondA" / "R_1_Merged_ch01_t00.tif",
        root / "CondA" / "R_1_Merged_ch01_t01.tif",
        root / "CondA" / "R_2_Merged_ch00_t00.tif",
        root / "CondB" / "Exp_s2_z1_ch1_t10.tiff",
    ]
    for p in files:
        p.write_bytes(b"\x00")
    return root


def test_scan_available_data(tmp_dataset: Path):
    svc = DataSelectionService()
    files = svc.scan_available_data(tmp_dataset)
    assert len(files) == 4


def test_parse_conditions_timepoints_regions(tmp_dataset: Path):
    svc = DataSelectionService()
    files = svc.scan_available_data(tmp_dataset)
    conditions, timepoints, regions = svc.parse_conditions_timepoints_regions(files)
    assert set(conditions) == {"CondA", "CondB"}
    assert "t00" in timepoints and "t01" in timepoints and "t10" in timepoints
    assert any(r.startswith("R_1_Merged") for r in regions) or "R_1_Merged" in regions


def test_validate_and_generate_file_lists(tmp_dataset: Path):
    svc = DataSelectionService()
    selection = DatasetSelection(
        root=tmp_dataset,
        conditions=["CondA"],
        regions=["R_1_Merged"],
        timepoints=["t00"],
        channels=["ch01"],
    )
    assert svc.validate_user_selections(selection) is True
    files = svc.generate_file_lists(selection)
    # Expect exactly one file R_1_Merged_ch01_t00.tif in CondA
    assert len(files) == 1
    assert files[0].name == "R_1_Merged_ch01_t00.tif"


