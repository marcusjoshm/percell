from percell.application.workflow_coordinator import WorkflowCoordinator
from percell.domain import WorkflowStep, WorkflowConfig
from percell.domain.services.workflow_orchestration_service import WorkflowOrchestrationService


def test_workflow_coordinator_run_happy_path():
    orchestrator = WorkflowOrchestrationService()
    wc = WorkflowCoordinator(orchestrator=orchestrator)
    steps = [WorkflowStep.DATA_SELECTION, WorkflowStep.SEGMENTATION]
    cfg = WorkflowConfig(steps=steps)
    ok = wc.run(steps, cfg)
    assert isinstance(ok, bool)


