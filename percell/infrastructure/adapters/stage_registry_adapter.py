"""
Stage registry adapter implementing StageRegistryPort.

This adapter provides concrete implementations for stage registration and execution
in the Percell pipeline system.
"""

from typing import Dict, Any, Type
from percell.domain.ports import StageRegistryPort
from percell.domain.exceptions import StageExecutionError


class StageRegistryAdapter(StageRegistryPort):
    """Concrete implementation of StageRegistryPort for pipeline stage management."""
    
    def __init__(self):
        """Initialize the stage registry."""
        self._stages: Dict[str, type] = {}
    
    def register_stage(self, stage_name: str, stage_class: Type) -> None:
        """
        Register a stage class with the registry.
        
        Args:
            stage_name: Name to register the stage under
            stage_class: The stage class to register
        """
        if not isinstance(stage_class, Type):
            raise ValueError(f"stage_class must be a class, got {type(stage_class)}")
        
        self._stages[stage_name] = stage_class
    
    def get_stage_registry(self) -> Dict[str, Type]:
        """
        Get the current stage registry.
        
        Returns:
            Dictionary mapping stage names to stage classes
        """
        return self._stages.copy()
    
    def execute_stage(self, stage_name: str, **kwargs) -> Any:
        """
        Execute a stage by name.
        
        Args:
            stage_name: Name of the stage to execute
            **kwargs: Arguments to pass to the stage
            
        Returns:
            Result of stage execution
            
        Raises:
            StageExecutionError: If stage execution fails
        """
        if stage_name not in self._stages:
            raise StageExecutionError(f"Stage '{stage_name}' not found in registry")
        
        try:
            stage_class = self._stages[stage_name]
            stage_instance = stage_class(**kwargs)
            
            # Execute the stage (assuming it has a run method)
            if hasattr(stage_instance, 'run'):
                return stage_instance.run()
            elif hasattr(stage_instance, 'execute'):
                return stage_instance.execute()
            else:
                raise StageExecutionError(
                    f"Stage '{stage_name}' has no 'run' or 'execute' method"
                )
                
        except Exception as e:
            raise StageExecutionError(
                f"Failed to execute stage '{stage_name}': {str(e)}"
            ) from e
    
    def has_stage(self, stage_name: str) -> bool:
        """
        Check if a stage is registered.
        
        Args:
            stage_name: Name of the stage to check
            
        Returns:
            True if stage is registered, False otherwise
        """
        return stage_name in self._stages
    
    def list_stages(self) -> list[str]:
        """
        List all registered stage names.
        
        Returns:
            List of registered stage names
        """
        return list(self._stages.keys())
    
    def unregister_stage(self, stage_name: str) -> None:
        """
        Unregister a stage from the registry.
        
        Args:
            stage_name: Name of the stage to unregister
        """
        if stage_name in self._stages:
            del self._stages[stage_name]
