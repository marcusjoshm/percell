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
        if not steps:
            raise ValueError("Workflow must contain at least one step")

        # All entries must be WorkflowStep and unique
        if any(not isinstance(s, WorkflowStep) for s in steps):
            raise ValueError("All workflow steps must be of type WorkflowStep")
        if len(set(steps)) != len(steps):
            raise ValueError("Workflow steps must not contain duplicates")

        # Enforce monotonic order according to the canonical sequence
        canonical = [
            WorkflowStep.DATA_SELECTION,
            WorkflowStep.SEGMENTATION,
            WorkflowStep.PROCESSING,
            WorkflowStep.THRESHOLDING,
            WorkflowStep.ANALYSIS,
        ]
        order_index = {step: i for i, step in enumerate(canonical)}
        indices = [order_index[s] for s in steps]
        if indices != sorted(indices):
            raise ValueError("Workflow steps must follow the canonical order without reordering")

    def manage_workflow_state(self, current_state: WorkflowState, event: str) -> WorkflowState:
        """Compute the next workflow state given an event.

        Args:
            current_state: The current workflow state.
            event: Event triggering a transition (e.g., "start", "error").

        Returns:
            The next workflow state.
        """
        event = (event or "").lower().strip()
        if event == "error":
            return WorkflowState.FAILED
        if current_state == WorkflowState.PENDING and event == "start":
            return WorkflowState.RUNNING
        if current_state == WorkflowState.RUNNING and event in {"complete", "finish", "done"}:
            return WorkflowState.COMPLETED
        # Default: no transition
        return current_state

    def coordinate_step_execution(self, steps: list[WorkflowStep], config: WorkflowConfig) -> None:
        """Coordinate execution of the given steps using provided config.

        Args:
            steps: Steps to execute.
            config: Workflow configuration and policies.
        """
        # For domain layer, we validate and compute an execution plan only.
        # Execution is handled by the application layer/adapters.
        self.validate_workflow_steps(steps)
        # Potential enhancements: dependency expansion, policy checks, etc.
        return None

    def handle_custom_workflows(self, steps: list[WorkflowStep]) -> list[WorkflowStep]:
        """Normalize and validate a custom workflow definition.

        Args:
            steps: Proposed custom step order.

        Returns:
            Normalized sequence of steps.
        """
        if not steps:
            return []
        # Remove duplicates while preserving order
        seen: set[WorkflowStep] = set()
        deduped: list[WorkflowStep] = []
        for s in steps:
            if isinstance(s, WorkflowStep) and s not in seen:
                deduped.append(s)
                seen.add(s)

        # Keep only steps in canonical list, then sort by canonical order
        canonical = [
            WorkflowStep.DATA_SELECTION,
            WorkflowStep.SEGMENTATION,
            WorkflowStep.PROCESSING,
            WorkflowStep.THRESHOLDING,
            WorkflowStep.ANALYSIS,
        ]
        order_index = {step: i for i, step in enumerate(canonical)}
        filtered = [s for s in deduped if s in order_index]
        # Return in canonical order while preserving subset
        filtered.sort(key=lambda s: order_index[s])
        return filtered


