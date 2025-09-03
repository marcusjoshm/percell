"""
Workflow entity for Percell domain.

Represents a workflow definition and execution state.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any, Callable
from enum import Enum
from datetime import datetime


class WorkflowStatus(Enum):
    """Workflow execution status."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class StepStatus(Enum):
    """Individual step status."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class WorkflowStep:
    """
    Represents a single step in a workflow.
    """
    
    step_id: str
    name: str
    description: Optional[str] = None
    
    # Execution
    status: StepStatus = StepStatus.PENDING
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    duration: Optional[float] = None
    
    # Parameters
    parameters: Dict[str, Any] = field(default_factory=dict)
    
    # Dependencies
    depends_on: List[str] = field(default_factory=list)
    
    # Results
    results: Dict[str, Any] = field(default_factory=dict)
    error_message: Optional[str] = None
    
    def start(self) -> None:
        """Mark step as started."""
        self.status = StepStatus.RUNNING
        self.start_time = datetime.now()
    
    def complete(self, results: Dict[str, Any] = None) -> None:
        """Mark step as completed."""
        self.status = StepStatus.COMPLETED
        self.end_time = datetime.now()
        if self.start_time:
            self.duration = (self.end_time - self.start_time).total_seconds()
        if results:
            self.results.update(results)
    
    def fail(self, error_message: str) -> None:
        """Mark step as failed."""
        self.status = StepStatus.FAILED
        self.end_time = datetime.now()
        if self.start_time:
            self.duration = (self.end_time - self.start_time).total_seconds()
        self.error_message = error_message
    
    def skip(self, reason: str = None) -> None:
        """Mark step as skipped."""
        self.status = StepStatus.SKIPPED
        self.end_time = datetime.now()
        if reason:
            self.error_message = f"Skipped: {reason}"
    
    def is_ready(self, completed_steps: set) -> bool:
        """Check if step is ready to execute based on dependencies."""
        return all(dep in completed_steps for dep in self.depends_on)


@dataclass
class Workflow:
    """
    Represents a complete workflow definition and execution state.
    """
    
    # Identification
    workflow_id: str
    name: str
    description: Optional[str] = None
    version: str = "1.0"
    
    # Steps
    steps: List[WorkflowStep] = field(default_factory=list)
    
    # Execution state
    status: WorkflowStatus = WorkflowStatus.PENDING
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    duration: Optional[float] = None
    
    # Configuration
    parameters: Dict[str, Any] = field(default_factory=dict)
    
    # Results
    results: Dict[str, Any] = field(default_factory=dict)
    
    # Metadata
    created_by: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    
    def add_step(self, step: WorkflowStep) -> None:
        """Add a step to the workflow."""
        self.steps.append(step)
    
    def get_step(self, step_id: str) -> Optional[WorkflowStep]:
        """Get a step by ID."""
        for step in self.steps:
            if step.step_id == step_id:
                return step
        return None
    
    def get_steps_by_status(self, status: StepStatus) -> List[WorkflowStep]:
        """Get all steps with a specific status."""
        return [step for step in self.steps if step.status == status]
    
    def get_ready_steps(self) -> List[WorkflowStep]:
        """Get steps that are ready to execute."""
        completed_steps = {step.step_id for step in self.steps if step.status == StepStatus.COMPLETED}
        return [step for step in self.steps 
                if step.status == StepStatus.PENDING and step.is_ready(completed_steps)]
    
    def start(self) -> None:
        """Start workflow execution."""
        self.status = WorkflowStatus.RUNNING
        self.start_time = datetime.now()
    
    def complete(self) -> None:
        """Mark workflow as completed."""
        self.status = WorkflowStatus.COMPLETED
        self.end_time = datetime.now()
        if self.start_time:
            self.duration = (self.end_time - self.start_time).total_seconds()
    
    def fail(self) -> None:
        """Mark workflow as failed."""
        self.status = WorkflowStatus.FAILED
        self.end_time = datetime.now()
        if self.start_time:
            self.duration = (self.end_time - self.start_time).total_seconds()
    
    def cancel(self) -> None:
        """Cancel workflow execution."""
        self.status = WorkflowStatus.CANCELLED
        self.end_time = datetime.now()
        if self.start_time:
            self.duration = (self.end_time - self.start_time).total_seconds()
        
        # Mark pending steps as skipped
        for step in self.steps:
            if step.status == StepStatus.PENDING:
                step.skip("Workflow cancelled")
    
    def get_progress(self) -> Dict[str, Any]:
        """Get workflow progress information."""
        total_steps = len(self.steps)
        completed_steps = len(self.get_steps_by_status(StepStatus.COMPLETED))
        failed_steps = len(self.get_steps_by_status(StepStatus.FAILED))
        running_steps = len(self.get_steps_by_status(StepStatus.RUNNING))
        skipped_steps = len(self.get_steps_by_status(StepStatus.SKIPPED))
        
        progress_percentage = (completed_steps / total_steps * 100) if total_steps > 0 else 0
        
        return {
            'total_steps': total_steps,
            'completed_steps': completed_steps,
            'failed_steps': failed_steps,
            'running_steps': running_steps,
            'skipped_steps': skipped_steps,
            'progress_percentage': progress_percentage,
            'status': self.status.value,
            'duration': self.duration,
            'start_time': self.start_time,
            'end_time': self.end_time
        }
    
    def validate(self) -> List[str]:
        """
        Validate workflow definition.
        
        Returns:
            List of validation errors
        """
        errors = []
        
        # Check for duplicate step IDs
        step_ids = [step.step_id for step in self.steps]
        if len(step_ids) != len(set(step_ids)):
            errors.append("Duplicate step IDs found")
        
        # Check dependencies
        step_id_set = set(step_ids)
        for step in self.steps:
            for dep in step.depends_on:
                if dep not in step_id_set:
                    errors.append(f"Step {step.step_id} depends on non-existent step {dep}")
        
        # Check for circular dependencies (simplified check)
        for step in self.steps:
            if step.step_id in step.depends_on:
                errors.append(f"Step {step.step_id} has circular dependency on itself")
        
        return errors
    
    def is_valid(self) -> bool:
        """Check if workflow is valid."""
        return len(self.validate()) == 0
    
    def get_execution_summary(self) -> Dict[str, Any]:
        """Get summary of workflow execution."""
        progress = self.get_progress()
        
        summary = {
            'workflow_id': self.workflow_id,
            'name': self.name,
            'status': self.status.value,
            'progress': progress,
            'success_rate': (progress['completed_steps'] / progress['total_steps'] * 100) 
                          if progress['total_steps'] > 0 else 0,
        }
        
        # Add step details
        step_details = []
        for step in self.steps:
            step_details.append({
                'step_id': step.step_id,
                'name': step.name,
                'status': step.status.value,
                'duration': step.duration,
                'error_message': step.error_message
            })
        
        summary['steps'] = step_details
        
        return summary


# Predefined workflow templates
def create_standard_workflow(workflow_id: str, parameters: Dict[str, Any] = None) -> Workflow:
    """Create a standard cell analysis workflow."""
    workflow = Workflow(
        workflow_id=workflow_id,
        name="Standard Cell Analysis",
        description="Complete single-cell analysis workflow",
        parameters=parameters or {}
    )
    
    # Define standard steps
    steps = [
        WorkflowStep("data_selection", "Data Selection", "Select and validate input data"),
        WorkflowStep("segmentation", "Cell Segmentation", "Segment cells using Cellpose", 
                    depends_on=["data_selection"]),
        WorkflowStep("roi_processing", "ROI Processing", "Process and validate ROIs", 
                    depends_on=["segmentation"]),
        WorkflowStep("cell_extraction", "Cell Extraction", "Extract single cells", 
                    depends_on=["roi_processing"]),
        WorkflowStep("thresholding", "Threshold Analysis", "Apply thresholding to cells", 
                    depends_on=["cell_extraction"]),
        WorkflowStep("analysis", "Final Analysis", "Generate analysis results", 
                    depends_on=["thresholding"])
    ]
    
    for step in steps:
        workflow.add_step(step)
    
    return workflow


def create_custom_workflow(workflow_id: str, step_names: List[str], 
                         parameters: Dict[str, Any] = None) -> Workflow:
    """Create a custom workflow with specified steps."""
    workflow = Workflow(
        workflow_id=workflow_id,
        name="Custom Workflow",
        description="User-defined workflow",
        parameters=parameters or {}
    )
    
    # Create steps with simple linear dependencies
    for i, step_name in enumerate(step_names):
        depends_on = [step_names[i-1]] if i > 0 else []
        step = WorkflowStep(
            step_id=step_name,
            name=step_name.replace('_', ' ').title(),
            depends_on=depends_on
        )
        workflow.add_step(step)
    
    return workflow
