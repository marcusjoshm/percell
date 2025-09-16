from __future__ import annotations

from dataclasses import dataclass
from typing import List

from percell.domain import WorkflowStep, WorkflowConfig
from percell.domain.services.workflow_orchestration_service import WorkflowOrchestrationService


@dataclass(slots=True)
class WorkflowCoordinator:
    """Application service coordinating execution of configured workflow steps.

    This class sits in the application layer and uses domain services to validate
    and manage workflow execution. It delegates concrete step execution to
    existing orchestrators as appropriate.
    """

    orchestrator: WorkflowOrchestrationService

    def run(self, steps: List[WorkflowStep], config: WorkflowConfig) -> bool:
        # Validate and normalize steps using the domain orchestrator
        try:
            valid = self.orchestrator.validate_workflow_steps(steps)
            if not valid:
                return False
            self.orchestrator.manage_workflow_state(start_step=steps[0] if steps else None)
        except Exception:
            return False

        # Placeholder: delegate to existing pipeline or stage runner
        # In future iterations, inject and call specific step handlers here.
        try:
            self.orchestrator.coordinate_step_execution(steps)
            return True
        except Exception:
            return False


