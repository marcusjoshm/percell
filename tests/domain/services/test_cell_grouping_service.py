import numpy as np
import pytest
from percell.domain.services.cell_grouping_service import CellGroupingService, GroupingParameters


def test_compute_auc_simple_profile():
    service = CellGroupingService()
    profile = np.array([1, 2, 3, 2, 1], dtype=float)
    auc = service.compute_auc(profile)
    assert auc == pytest.approx(9.0)


def test_uniform_bins_even_split():
    service = CellGroupingService()
    intensities = [1, 2, 3, 4, 5, 6]
    params = GroupingParameters(num_bins=2, strategy='uniform')
    groups = service.group_by_intensity(intensities, params)
    # Should split roughly 3 and 3
    assert groups == [0, 0, 0, 1, 1, 1]


def test_uniform_bins_constant_values_all_zero_group():
    service = CellGroupingService()
    intensities = [5, 5, 5]
    params = GroupingParameters(num_bins=3, strategy='uniform')
    groups = service.group_by_intensity(intensities, params)
    assert groups == [0, 0, 0]


def test_aggregate_by_group_sums_images():
    service = CellGroupingService()
    # two 2x2 images per group
    img_a1 = np.ones((2, 2))
    img_a2 = np.ones((2, 2)) * 2
    img_b1 = np.ones((2, 2)) * 3
    images = [img_a1, img_a2, img_b1]
    assignments = [0, 0, 1]
    aggregated = service.aggregate_by_group(images, assignments)
    assert 0 in aggregated and 1 in aggregated
    np.testing.assert_allclose(aggregated[0], np.array([[3, 3], [3, 3]]))
    np.testing.assert_allclose(aggregated[1], np.array([[3, 3], [3, 3]]))


def test_kmeans_and_gmm_optional_dependencies():
    service = CellGroupingService()
    intensities = [1, 2, 10, 11]
    with pytest.raises(RuntimeError):
        service.group_by_intensity(intensities, GroupingParameters(num_bins=2, strategy='kmeans'))
    with pytest.raises(RuntimeError):
        service.group_by_intensity(intensities, GroupingParameters(num_bins=2, strategy='gmm'))
