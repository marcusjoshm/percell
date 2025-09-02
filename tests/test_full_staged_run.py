from __future__ import annotations

from typing import List

from percell.infrastructure.configuration.config import create_default_config
from percell.infrastructure.logging.logger import PipelineLogger
from percell.core.stages import StageBase, StageExecutor, StageRegistry
from percell.services.factory import ServiceFactory


class _ValidStage(StageBase):
    def validate_inputs(self, **kwargs) -> bool:
        return True

    def run(self, **kwargs) -> bool:
        return True


class _FailingStage(StageBase):
    def validate_inputs(self, **kwargs) -> bool:
        return True

    def run(self, **kwargs) -> bool:
        return False


def test_full_staged_run_stops_on_failure(tmp_path):
    cfg = create_default_config(str(tmp_path / "config.json"))
    logger = PipelineLogger(str(tmp_path), log_level="DEBUG")
    registry = StageRegistry()
    registry.register("first", _ValidStage, order=1)
    registry.register("second", _FailingStage, order=2)
    registry.register("third", _ValidStage, order=3)

    executor = StageExecutor(cfg, logger, registry)
    ok = executor.execute_stages(["first", "second", "third"], input_dir=str(tmp_path), output_dir=str(tmp_path))

    assert ok is False

    # ServiceFactory shared instance quick check
    factory = ServiceFactory(cfg)
    fs1 = factory.get_file_service()
    fs2 = factory.get_file_service()
    assert fs1 is fs2


