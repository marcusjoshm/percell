"""
Domain service: WorkflowOrchestrator.

Coordinates workflow execution using the outbound ports. This is a skeleton
aligned to the ports/adapters guide and can be expanded with real logic.
"""

from __future__ import annotations

from typing import Any, Dict

from percell.domain.entities.workflow import Workflow, WorkflowStep
from percell.ports.outbound.storage_port import StoragePort
from percell.ports.outbound.segmentation_port import SegmentationPort
from percell.ports.outbound.image_processing_port import ImageProcessingPort
from percell.ports.outbound.metadata_port import MetadataPort


class WorkflowOrchestrator:
    def __init__(
        self,
        storage: StoragePort,
        segmentation: SegmentationPort,
        image_processing: ImageProcessingPort,
        metadata: MetadataPort,
    ) -> None:
        self.storage = storage
        self.segmentation = segmentation
        self.image_processing = image_processing
        self.metadata = metadata

    def execute_workflow(self, workflow: Workflow) -> Dict[str, Any]:
        """
        Execute the provided workflow definition.

        Returns a minimal summary for now.
        """
        # Skeleton: mark workflow as started and immediately complete
        workflow.start()
        for step in workflow.steps:
            step.start()
            step.complete()
        workflow.complete()
        return workflow.get_execution_summary()


