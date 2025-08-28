from __future__ import annotations

import argparse

from percell.core.config import create_default_config
from percell.core.logger import PipelineLogger
from percell.core.pipeline import Pipeline
from percell.core.stages import StageBase, get_stage_registry


class _FakeDataSelection(StageBase):
    def validate_inputs(self, **kwargs) -> bool:
        # Requires input/output dirs to exist; Pipeline.setup_directories creates output dirs
        return True

    def run(self, **kwargs) -> bool:
        # Simulate saving some selection to config
        self.config.set('data_selection.selected_conditions', ['condA'])
        self.config.save()
        return True


class _FakeAnalysis(StageBase):
    def validate_inputs(self, **kwargs) -> bool:
        # Check that previous stage could have set something in config
        return True

    def run(self, **kwargs) -> bool:
        # No-op success
        return True


def _register_fake_stages():
    registry = get_stage_registry()
    # Clear any previously registered stages to avoid interference
    registry.stages.clear()
    registry.stage_order.clear()
    registry.register('data_selection', _FakeDataSelection, order=1)
    registry.register('analysis', _FakeAnalysis, order=2)


def test_pipeline_end_to_end_with_fake_stages(tmp_path):
    # Arrange: register fake stages
    _register_fake_stages()

    # Config and dependencies
    cfg = create_default_config(str(tmp_path / 'config.json'))
    logger = PipelineLogger(str(tmp_path), log_level='DEBUG')

    # Build args to run exactly our two fake stages
    args = argparse.Namespace(
        input=str(tmp_path),
        output=str(tmp_path),
        datatype=None,
        conditions=None,
        timepoints=None,
        regions=None,
        segmentation_channel=None,
        analysis_channels=None,
        bins=5,
        data_selection=True,
        segmentation=False,
        process_single_cell=False,
        threshold_grouped_cells=False,
        measure_roi_area=False,
        analysis=True,
        cleanup=False,
        complete_workflow=False,
        advanced_workflow=False,
        skip_steps=None,
        start_from=None,
        verbose=False,
        interactive=False,
    )

    # Act: run pipeline
    pipeline = Pipeline(cfg, logger, args)
    ok = pipeline.run()

    # Assert
    assert ok is True


