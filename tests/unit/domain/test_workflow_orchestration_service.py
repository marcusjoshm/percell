import pytest

from percell.domain import WorkflowOrchestrationService
from percell.domain.models import WorkflowStep, WorkflowState, WorkflowConfig


@pytest.fixture()
def svc() -> WorkflowOrchestrationService:
    return WorkflowOrchestrationService()


def test_validate_workflow_steps_valid(svc: WorkflowOrchestrationService):
    steps = [WorkflowStep.DATA_SELECTION, WorkflowStep.SEGMENTATION]
    svc.validate_workflow_steps(steps)  # should not raise


def test_validate_workflow_steps_invalid_order(svc: WorkflowOrchestrationService):
    with pytest.raises(ValueError):
        svc.validate_workflow_steps([WorkflowStep.SEGMENTATION, WorkflowStep.DATA_SELECTION])


def test_manage_workflow_state_transitions(svc: WorkflowOrchestrationService):
    assert svc.manage_workflow_state(WorkflowState.PENDING, "start") == WorkflowState.RUNNING
    assert svc.manage_workflow_state(WorkflowState.RUNNING, "complete") == WorkflowState.COMPLETED
    assert svc.manage_workflow_state(WorkflowState.RUNNING, "error") == WorkflowState.FAILED


def test_coordinate_step_execution_validates(svc: WorkflowOrchestrationService):
    cfg = WorkflowConfig(steps=[WorkflowStep.DATA_SELECTION])
    # Should validate and return None
    assert svc.coordinate_step_execution([WorkflowStep.DATA_SELECTION], cfg) is None


def test_handle_custom_workflows_normalizes(svc: WorkflowOrchestrationService):
    result = svc.handle_custom_workflows([
        WorkflowStep.ANALYSIS,
        WorkflowStep.DATA_SELECTION,
        WorkflowStep.SEGMENTATION,
        WorkflowStep.DATA_SELECTION,
    ])
    # Duplicates removed and order normalized to canonical subset
    assert result == [WorkflowStep.DATA_SELECTION, WorkflowStep.SEGMENTATION, WorkflowStep.ANALYSIS]


