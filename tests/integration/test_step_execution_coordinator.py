from percell.application.step_execution_coordinator import StepExecutionCoordinator
from percell.domain import WorkflowStep, WorkflowConfig


def test_step_execution_coordinator_runs_registered_steps():
    sec = StepExecutionCoordinator()
    ran = {"count": 0}

    def ok_exec(cfg: WorkflowConfig) -> bool:
        ran["count"] += 1
        return True

    sec.register_executor(WorkflowStep.DATA_SELECTION, ok_exec)
    sec.register_executor(WorkflowStep.SEGMENTATION, ok_exec)
    cfg = WorkflowConfig(steps=[WorkflowStep.DATA_SELECTION, WorkflowStep.SEGMENTATION])
    assert sec.run(cfg.steps, cfg) is True
    assert ran["count"] == 2

def test_step_execution_coordinator_fails_on_missing_executor():
    sec = StepExecutionCoordinator()
    cfg = WorkflowConfig(steps=[WorkflowStep.ANALYSIS])
    assert sec.run(cfg.steps, cfg) is False


