"""
AUCGroupCellsStage - Application Layer Stage

Groups extracted cells by intensity (AUC) for batch thresholding.
"""

from __future__ import annotations

from percell.application.stages_api import StageBase


class AUCGroupCellsStage(StageBase):
    """
    AUC Group Cells Stage

    Groups extracted cells into bins based on Area Under Curve (AUC) intensity
    metrics for batch thresholding operations.
    """

    def __init__(self, config, logger, stage_name="auc_group_cells"):
        super().__init__(config, logger, stage_name)

    def validate_inputs(self, **kwargs) -> bool:
        """Validate inputs for AUC group cells stage."""
        # Check if data selection has been completed
        data_selection = self.config.get('data_selection')
        if not data_selection:
            self.logger.error(
                "Data selection has not been completed. "
                "Please run data selection first."
            )
            return False

        # Check if required data selection parameters are available
        required_params = ['analysis_channels']
        missing_params = [
            param for param in required_params
            if not data_selection.get(param)
        ]
        if missing_params:
            self.logger.error(f"Missing data selection parameters: {missing_params}")
            return False

        return True

    def run(self, **kwargs) -> bool:
        """Run the AUC group cells stage."""
        try:
            self.logger.info("Starting AUC Group Cells Stage")

            # Get data selection parameters from config
            data_selection = self.config.get('data_selection')
            if not data_selection:
                self.logger.error("No data selection information found in config")
                return False

            # Get output directory
            output_dir = kwargs.get('output_dir')
            if not output_dir:
                self.logger.error("Output directory is required")
                return False

            # Group cells by AUC intensity
            self.logger.info("Grouping cells by AUC intensity...")
            from percell.application.image_processing_tasks import (
                group_cells as _group_cells
            )
            ok_group = _group_cells(
                cells_dir=f"{output_dir}/cells",
                output_dir=f"{output_dir}/grouped_cells",
                bins=int(kwargs.get('bins', 5)),
                force_clusters=True,
                channels=data_selection.get('analysis_channels'),
                imgproc=kwargs.get('imgproc'),
            )
            if not ok_group:
                self.logger.error("Failed to group cells by AUC")
                return False
            self.logger.info("Cells grouped by AUC successfully")

            return True

        except Exception as e:
            self.logger.error(f"Error in AUC Group Cells Stage: {e}")
            return False
