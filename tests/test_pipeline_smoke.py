from __future__ import annotations

import argparse

from percell.core.config import create_default_config
from percell.core.logger import PipelineLogger
from percell.core.pipeline import Pipeline


def test_pipeline_initializes_with_event_bus_and_plugin_manager(tmp_path):
    cfg = create_default_config(str(tmp_path / "config.json"))
    logger = PipelineLogger(str(tmp_path), log_level="DEBUG")
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
        data_selection=False,
        segmentation=False,
        process_single_cell=False,
        threshold_grouped_cells=False,
        measure_roi_area=False,
        analysis=False,
        cleanup=False,
        complete_workflow=False,
        advanced_workflow=False,
        skip_steps=None,
        start_from=None,
        verbose=False,
        interactive=False,
    )

    pipeline = Pipeline(cfg, logger, args)
    # Ensure optional components exist (or None if intentionally absent)
    assert hasattr(pipeline, "event_bus")
    assert hasattr(pipeline, "plugin_manager")


