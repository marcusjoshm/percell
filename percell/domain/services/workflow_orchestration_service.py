"""Workflow coordination and state management rules."""

from __future__ import annotations

from ..models import WorkflowConfig, WorkflowState, WorkflowStep


class WorkflowOrchestrationService:
    """Coordinates workflow steps and manages state transitions."""

    def validate_workflow_steps(self, steps: list[WorkflowStep]) -> None:
        """Validate an ordered list of workflow steps.

        Args:
            steps: Ordered steps to validate.

        Raises:
            ValueError: If steps are invalid or contain duplicates.
        """

        raise NotImplementedError

    def manage_workflow_state(self, current_state: WorkflowState, event: str) -> WorkflowState:
        """Compute the next workflow state given an event.

        Args:
            current_state: The current workflow state.
            event: Event triggering a transition (e.g., "start", "error").

        Returns:
            The next workflow state.
        """

        raise NotImplementedError

    def coordinate_step_execution(self, steps: list[WorkflowStep], config: WorkflowConfig) -> None:
        """Coordinate execution of the given steps using provided config.

        Args:
            steps: Steps to execute.
            config: Workflow configuration and policies.
        """

        raise NotImplementedError

    def handle_custom_workflows(self, steps: list[WorkflowStep]) -> list[WorkflowStep]:
        """Normalize and validate a custom workflow definition.

        Args:
            steps: Proposed custom step order.

        Returns:
            Normalized sequence of steps.
        """

        raise NotImplementedError


