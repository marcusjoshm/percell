from __future__ import annotations

from typing import Protocol

from ...domain.models import WorkflowStep, WorkflowConfig


class WorkflowExecutionPort(Protocol):
    """Driving port for initiating workflow execution from outside the app."""

    def execute(self, steps: list[WorkflowStep], config: WorkflowConfig) -> None:
        ...


