import pytest

from percell.domain import WorkflowOrchestrationService
from percell.domain.models import WorkflowStep, WorkflowState, WorkflowConfig


@pytest.fixture()
def svc() -> WorkflowOrchestrationService:
    return WorkflowOrchestrationService()


def test_validate_workflow_steps_contract(svc: WorkflowOrchestrationService):
    steps = [WorkflowStep.DATA_SELECTION, WorkflowStep.SEGMENTATION]
    with pytest.raises(NotImplementedError):
        svc.validate_workflow_steps(steps)


def test_manage_workflow_state_contract(svc: WorkflowOrchestrationService):
    with pytest.raises(NotImplementedError):
        svc.manage_workflow_state(WorkflowState.PENDING, "start")


def test_coordinate_step_execution_contract(svc: WorkflowOrchestrationService):
    cfg = WorkflowConfig(steps=[WorkflowStep.DATA_SELECTION])
    with pytest.raises(NotImplementedError):
        svc.coordinate_step_execution([WorkflowStep.DATA_SELECTION], cfg)


def test_handle_custom_workflows_contract(svc: WorkflowOrchestrationService):
    with pytest.raises(NotImplementedError):
        svc.handle_custom_workflows([WorkflowStep.ANALYSIS])


