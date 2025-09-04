from percell.domain.value_objects.processing import (
    BinningParameters,
    SegmentationParameters,
)


def test_binning_parameters_values():
    params = BinningParameters(num_bins=3, strategy='uniform')
    assert params.num_bins == 3
    assert params.strategy == 'uniform'


def test_segmentation_parameters_values():
    params = SegmentationParameters(
        model='cellpose',
        diameter=30.0,
        flow_threshold=0.5,
        cellprob_threshold=0.0,
    )
    assert params.model == 'cellpose'
    assert params.diameter == 30.0
    assert params.flow_threshold == 0.5
    assert params.cellprob_threshold == 0.0
