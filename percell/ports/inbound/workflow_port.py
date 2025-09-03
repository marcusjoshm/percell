"""
Workflow port interface for Percell.

Defines the contract for workflow execution operations.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any, Callable
from percell.domain.entities.workflow import Workflow, WorkflowStep
from percell.domain.value_objects.file_path import FilePath


class WorkflowPort(ABC):
    """
    Port interface for workflow operations.
    
    This interface defines how external systems (CLI, GUI, API) can
    trigger and manage workflow execution.
    """
    
    @abstractmethod
    def execute_workflow(self, workflow: Workflow, 
                        parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a complete workflow.
        
        Args:
            workflow: Workflow to execute
            parameters: Execution parameters
            
        Returns:
            Workflow execution results
            
        Raises:
            WorkflowError: If workflow execution fails
        """
        pass
    
    @abstractmethod
    def execute_step(self, step: WorkflowStep, 
                    parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a single workflow step.
        
        Args:
            step: Step to execute
            parameters: Step parameters
            
        Returns:
            Step execution results
            
        Raises:
            WorkflowError: If step execution fails
        """
        pass
    
    @abstractmethod
    def validate_workflow(self, workflow: Workflow) -> List[str]:
        """
        Validate a workflow definition.
        
        Args:
            workflow: Workflow to validate
            
        Returns:
            List of validation errors (empty if valid)
        """
        pass
    
    @abstractmethod
    def get_workflow_status(self, workflow_id: str) -> Dict[str, Any]:
        """
        Get status of a running workflow.
        
        Args:
            workflow_id: ID of the workflow
            
        Returns:
            Workflow status information
        """
        pass
    
    @abstractmethod
    def cancel_workflow(self, workflow_id: str) -> bool:
        """
        Cancel a running workflow.
        
        Args:
            workflow_id: ID of the workflow to cancel
            
        Returns:
            True if successfully cancelled
        """
        pass
    
    @abstractmethod
    def pause_workflow(self, workflow_id: str) -> bool:
        """
        Pause a running workflow.
        
        Args:
            workflow_id: ID of the workflow to pause
            
        Returns:
            True if successfully paused
        """
        pass
    
    @abstractmethod
    def resume_workflow(self, workflow_id: str) -> bool:
        """
        Resume a paused workflow.
        
        Args:
            workflow_id: ID of the workflow to resume
            
        Returns:
            True if successfully resumed
        """
        pass
    
    @abstractmethod
    def get_available_workflows(self) -> List[str]:
        """
        Get list of available workflow templates.
        
        Returns:
            List of workflow template names
        """
        pass
    
    @abstractmethod
    def create_workflow_from_template(self, template_name: str, 
                                    parameters: Dict[str, Any]) -> Workflow:
        """
        Create a workflow from a template.
        
        Args:
            template_name: Name of the workflow template
            parameters: Template parameters
            
        Returns:
            Created workflow instance
        """
        pass


class WorkflowError(Exception):
    """Exception raised by workflow operations."""
    pass
