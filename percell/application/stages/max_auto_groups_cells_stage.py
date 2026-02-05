"""
MaxAutoGroupsCellsStage - Application Layer Stage

Groups extracted cells into automatically determined bins using GMM clustering
based on maximum fluorescence intensity per cell (peak intensity).
"""

from __future__ import annotations

from percell.application.stages_api import StageBase


class MaxAutoGroupsCellsStage(StageBase):
    """
    Max Auto Groups Cells Stage

    Groups extracted cells into automatically determined bins based on
    maximum fluorescence intensity per cell (peak intensity) using
    Gaussian Mixture Model (GMM) clustering with BIC for optimal cluster
    selection.

    Unlike AUC-based grouping which uses total pixel intensity, or mean-based
    grouping which uses average intensity, this method uses the peak/maximum
    intensity value in each cell, which can be useful for detecting cells
    with bright puncta or localized signals.
    """

    def __init__(self, config, logger, stage_name="max_auto_groups_cells"):
        super().__init__(config, logger, stage_name)

    def validate_inputs(self, **kwargs) -> bool:
        """Validate inputs for max auto groups cells stage."""
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
            self.logger.error(
                f"Missing data selection parameters: {missing_params}"
            )
            return False

        return True

    def run(self, **kwargs) -> bool:
        """Run the max auto groups cells stage."""
        try:
            self.logger.info("Starting Max Auto Groups Cells Stage")

            # Get data selection parameters from config
            data_selection = self.config.get('data_selection')
            if not data_selection:
                self.logger.error(
                    "No data selection information found in config"
                )
                return False

            # Get output directory
            output_dir = kwargs.get('output_dir')
            if not output_dir:
                self.logger.error("Output directory is required")
                return False

            # Get max_clusters parameter (default: 10)
            max_clusters = kwargs.get('max_clusters', 10)

            # Group cells using GMM auto-clustering on max intensity
            self.logger.info(
                f"Auto-grouping cells by max intensity "
                f"(max {max_clusters} clusters)..."
            )
            from percell.application.image_processing_tasks import (
                group_cells_max_auto as _group_cells_max_auto
            )
            ok_group = _group_cells_max_auto(
                cells_dir=f"{output_dir}/cells",
                output_dir=f"{output_dir}/grouped_cells",
                max_clusters=max_clusters,
                channels=data_selection.get('analysis_channels'),
                imgproc=kwargs.get('imgproc'),
            )
            if not ok_group:
                self.logger.error("Failed to auto-group cells by max intensity")
                return False
            self.logger.info(
                "Cells auto-grouped by max intensity successfully"
            )

            return True

        except Exception as e:
            self.logger.error(f"Error in Max Auto Groups Cells Stage: {e}")
            return False
