import pytest
from pathlib import Path
from percell.domain.value_objects.experiment import (
    DataType,
    Channel,
    Timepoint,
    Region,
    Condition,
    ExperimentSelection,
)


def test_experiment_selection_immutable():
    selection = ExperimentSelection(
        data_type=DataType.SINGLE_TIMEPOINT,
        input_dir=Path('/tmp/input'),
        output_dir=Path('/tmp/output'),
        conditions=[Condition(name='ctrl')],
        channels=[Channel(name='DAPI', is_segmentation=True)],
        timepoints=[Timepoint(id='t0', order=0)],
        regions=[Region(id='r1', name='Region 1')],
    )

    with pytest.raises(Exception):
        selection.output_dir = Path('/tmp/new')


def test_channel_defaults():
    ch = Channel(name='GFP')
    assert ch.is_segmentation is False
    assert ch.is_analysis is False


def test_timepoint_and_region_values():
    tp = Timepoint(id='t1', order=1)
    rg = Region(id='r2', name='Region 2')
    assert tp.order == 1
    assert rg.name == 'Region 2'
