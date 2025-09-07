from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Dict, List

from percell.domain import WorkflowStep, WorkflowConfig


StepExecutor = Callable[[WorkflowConfig], bool]


@dataclass(slots=True)
class StepExecutionCoordinator:
    """Coordinates execution of individual workflow steps via registered executors.

    Executors are plain callables taking a WorkflowConfig and returning bool for success.
    This keeps the application layer decoupled from concrete modules.
    """

    _executors: Dict[WorkflowStep, StepExecutor] = field(default_factory=dict)

    def register_executor(self, step: WorkflowStep, executor: StepExecutor) -> None:
        self._executors[step] = executor

    def run(self, steps: List[WorkflowStep], config: WorkflowConfig) -> bool:
        for step in steps:
            executor = self._executors.get(step)
            if executor is None:
                return False
            ok = False
            try:
                ok = bool(executor(config))
            except Exception:
                ok = False
            if not ok:
                return False
        return True


