"""
SGAutoGroupsCellsStage - Application Layer Stage

Groups extracted cells into automatically determined bins using GMM clustering
based on SG (Signal-to-Ground) contrast ratio per cell.

The SG ratio is computed as:
    sum of pixels >= 95th percentile / sum of pixels <= 50th percentile
"""

from __future__ import annotations

from percell.application.stages_api import StageBase


class SGAutoGroupsCellsStage(StageBase):
    """
    SG Auto Groups Cells Stage

    Groups extracted cells into automatically determined bins based on
    SG (Signal-to-Ground) contrast ratio using Gaussian Mixture Model (GMM)
    clustering with BIC for optimal cluster selection.

    The SG ratio measures the contrast between bright signal pixels (95th
    percentile) and median background pixels (50th percentile). This is
    useful for grouping cells by signal contrast rather than absolute
    intensity, helping identify cells with punctate/localized signals
    vs diffuse staining.
    """

    def __init__(self, config, logger, stage_name="sg_auto_groups_cells"):
        super().__init__(config, logger, stage_name)

    def validate_inputs(self, **kwargs) -> bool:
        """Validate inputs for SG auto groups cells stage."""
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
        """Run the SG auto groups cells stage."""
        try:
            self.logger.info("Starting SG Auto Groups Cells Stage")

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

            # Group cells using GMM auto-clustering on SG contrast ratio
            self.logger.info(
                f"Auto-grouping cells by SG contrast ratio "
                f"(max {max_clusters} clusters)..."
            )
            from percell.application.image_processing_tasks import (
                group_cells_sg_auto as _group_cells_sg_auto
            )
            ok_group = _group_cells_sg_auto(
                cells_dir=f"{output_dir}/cells",
                output_dir=f"{output_dir}/grouped_cells",
                max_clusters=max_clusters,
                channels=data_selection.get('analysis_channels'),
                imgproc=kwargs.get('imgproc'),
            )
            if not ok_group:
                self.logger.error(
                    "Failed to auto-group cells by SG contrast ratio"
                )
                return False
            self.logger.info(
                "Cells auto-grouped by SG contrast ratio successfully"
            )

            return True

        except Exception as e:
            self.logger.error(f"Error in SG Auto Groups Cells Stage: {e}")
            return False
