from __future__ import annotations

from typing import List

from percell.infrastructure.configuration.config import create_default_config
from percell.infrastructure.logging.logger import PipelineLogger
from percell.infrastructure.stages.stages import StageBase, StageExecutor, StageRegistry
from percell.services.event_bus import PipelineEventBus, StageStarted, StageCompleted


class _DummyStage(StageBase):
    def validate_inputs(self, **kwargs) -> bool:
        return True

    def run(self, **kwargs) -> bool:
        return True


def test_event_bus_receives_stage_events(tmp_path):
    # Setup config, logger, registry
    cfg = create_default_config(str(tmp_path / "config.json"))
    logger = PipelineLogger(str(tmp_path), log_level="DEBUG")
    registry = StageRegistry()
    registry.register("dummy", _DummyStage, order=1)

    # Setup event bus and subscribers
    bus = PipelineEventBus()
    started: List[str] = []
    completed: List[str] = []

    def on_started(e: StageStarted):
        started.append(e.stage_name)

    def on_completed(e: StageCompleted):
        completed.append(e.stage_name)

    bus.subscribe(StageStarted, on_started)
    bus.subscribe(StageCompleted, on_completed)

    # Execute
    executor = StageExecutor(cfg, logger, registry, event_bus=bus)
    ok = executor.execute_stages(["dummy"], input_dir=str(tmp_path), output_dir=str(tmp_path))

    assert ok is True
    assert started == ["dummy"]
    assert completed == ["dummy"]


