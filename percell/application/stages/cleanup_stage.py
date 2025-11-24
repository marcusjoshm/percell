"""
CleanupStage - Application Layer Stage

Auto-generated from stage_classes.py split.
"""

from __future__ import annotations

import subprocess
import os
import re
import sys
import shutil
from pathlib import Path
from typing import Dict, Any, List, Set, Optional

from percell.application.progress_api import run_subprocess_with_spinner
from percell.domain import WorkflowOrchestrationService
from percell.domain.models import WorkflowStep, WorkflowState, WorkflowConfig
from percell.domain import DataSelectionService, FileNamingService
from percell.application.stages_api import StageBase


class CleanupStage(StageBase):
    """
    Cleanup Stage
    
    Empties cells, masks, and related directories to free up disk space.
    Preserves directory structure while removing contents.
    """
    
    def __init__(self, config, logger, stage_name="cleanup"):
        super().__init__(config, logger, stage_name)
        self.cleanup_directories = [
            'cells',
            'masks'
        ]
        
    def validate_inputs(self, **kwargs) -> bool:
        """Validate inputs for cleanup stage."""
        output_dir = kwargs.get('output_dir')
        if not output_dir:
            self.logger.error("Output directory is required for cleanup")
            return False
        if not Path(output_dir).exists():
            self.logger.error(f"Output directory does not exist: {output_dir}")
            return False
        return True
    
    def run(self, **kwargs) -> bool:
        """Run the cleanup stage."""
        try:
            self.logger.info("Starting Cleanup Stage")
            
            output_dir = Path(kwargs['output_dir'])
            
            # Import cleanup functionality
            try:
                from percell.application.image_processing_tasks import cleanup_directories, scan_cleanup_directories
            except ImportError as e:
                self.logger.error(f"Could not import cleanup helpers: {e}")
                return False
            
            # Scan directories to see what can be cleaned up
            self.logger.info("Scanning directories for cleanup...")
            directories_info = scan_cleanup_directories(
                str(output_dir),
                include_cells=True,
                include_masks=True,
                include_combined_masks=False,
                include_grouped_cells=False,
                include_grouped_masks=False
            )
            
            # Check if any directories have content
            total_size = sum(info['size_bytes'] for info in directories_info.values() if info['exists'])
            
            if total_size == 0:
                self.logger.info("No directories found with content to clean up.")
                return True
            
            # Show what will be cleaned up
            self.logger.info("=" * 80)
            self.logger.info("Directories available for cleanup:")
            self.logger.info("-" * 80)
            
            for dir_name, info in directories_info.items():
                if info['exists']:
                    self.logger.info(f"  • {dir_name:<20} {info['size_formatted']:>15}")
            
            self.logger.info("-" * 80)
            self.logger.info(f"  Total space to free: {sum(info['size_bytes'] for info in directories_info.values() if info['exists']):>15} bytes")
            self.logger.info("=" * 80)
            
            # Perform cleanup
            self.logger.info("Performing cleanup...")
            deleted_count, freed_bytes = cleanup_directories(
                str(output_dir),
                delete_cells=True,
                delete_masks=True,
                delete_combined_masks=False,
                delete_grouped_cells=False,
                delete_grouped_masks=False,
                dry_run=False,
                force=True,  # Force cleanup in pipeline mode
                logger=self.logger
            )
            
            self.logger.info(f"Cleanup completed successfully!")
            self.logger.info(f"  • Directories emptied: {deleted_count}")
            self.logger.info(f"  • Total space freed: {freed_bytes} bytes")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error in Cleanup Stage: {e}")
            return False


