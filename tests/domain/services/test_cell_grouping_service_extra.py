import numpy as np
import pytest

from percell.domain.services.cell_grouping_service import CellGroupingService, GroupingParameters


def test_compute_auc_rejects_non_1d():
    service = CellGroupingService()
    with pytest.raises(ValueError):
        service.compute_auc(np.ones((2, 2)))


def test_uniform_bins_empty_and_constant():
    service = CellGroupingService()
    assert service.group_by_intensity([], GroupingParameters(3, 'uniform')) == []
    assert service.group_by_intensity([5, 5, 5], GroupingParameters(3, 'uniform')) == [0, 0, 0]


def test_uniform_bins_edges():
    service = CellGroupingService()
    vals = [0.0, 0.5, 1.0]
    groups = service.group_by_intensity(vals, GroupingParameters(2, 'uniform'))
    assert len(groups) == 3


def test_aggregate_by_group_mismatched_lengths():
    service = CellGroupingService()
    with pytest.raises(ValueError):
        service.aggregate_by_group([np.ones((2, 2))], [0, 1])


