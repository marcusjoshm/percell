from pathlib import Path

import numpy as np
import pytest

from percell.domain import IntensityAnalysisService, ROI, CellMetrics, ThresholdParameters, AnalysisResult


@pytest.fixture()
def svc() -> IntensityAnalysisService:
    return IntensityAnalysisService()


def test_measure_cell_intensity_basic(svc: IntensityAnalysisService, tmp_path: Path):
    # Create a simple 5x5 image with a bright 3x3 center
    img = np.zeros((5, 5), dtype=np.uint8)
    img[1:4, 1:4] = 10
    p = tmp_path / "img.tif"
    try:
        import tifffile
        tifffile.imwrite(p, img)
    except Exception:
        pytest.skip("tifffile not available in test environment")

    rois = [ROI(id=1), ROI(id=2)]
    metrics = svc.measure_cell_intensity(p, rois)
    assert isinstance(metrics, list) and len(metrics) == 2
    for m in metrics:
        assert isinstance(m, CellMetrics)
        assert m.area > 0
        assert m.mean_intensity > 0


def test_group_cells_by_brightness_contract(svc: IntensityAnalysisService):
    metrics = [
        CellMetrics(cell_id=1, area=10, mean_intensity=5.0),
        CellMetrics(cell_id=2, area=10, mean_intensity=15.0),
    ]
    groups = svc.group_cells_by_brightness(metrics)
    labels = [g[0] for g in groups]
    members = {g[0]: set(g[1]) for g in groups}
    assert "dim" in labels and "bright" in labels
    assert 1 in members.get("dim", set())
    assert 2 in members.get("bright", set())


def test_calculate_threshold_parameters_delegated(svc: IntensityAnalysisService):
    metrics = [
        CellMetrics(cell_id=1, area=10, mean_intensity=5.0),
        CellMetrics(cell_id=2, area=10, mean_intensity=15.0),
    ]
    with pytest.raises(NotImplementedError):
        svc.calculate_threshold_parameters(metrics)


def test_analyze_binary_masks_contract(svc: IntensityAnalysisService, tmp_path: Path):
    p = tmp_path / "mask.tif"
    try:
        import tifffile
        tifffile.imwrite(p, np.zeros((3, 3), dtype=np.uint8))
    except Exception:
        pytest.skip("tifffile not available in test environment")
    result = svc.analyze_binary_masks([p])
    assert isinstance(result, AnalysisResult)
    assert len(result.metrics) == 1


