"""
Application use case: RunCompleteWorkflow.

Bridges input parameters to the domain orchestrator.
"""

from __future__ import annotations

from typing import Any, Dict

from percell.domain.entities.workflow import create_standard_workflow
from percell.domain.services.workflow_orchestrator import WorkflowOrchestrator


class RunCompleteWorkflow:
    def __init__(self, orchestrator: WorkflowOrchestrator) -> None:
        self.orchestrator = orchestrator

    def execute(self, workflow_id: str, parameters: Dict[str, Any] | None = None) -> Dict[str, Any]:
        workflow = create_standard_workflow(workflow_id=workflow_id, parameters=parameters or {})
        return self.orchestrator.execute_workflow(workflow)


