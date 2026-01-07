"""Background subtraction workflow orchestration.

Coordinates the full preprocessing workflow for BS intensity analysis:
1. Copy percell analysis outputs to BS directory structure
2. Detect presence of stress granule (ch1) files
3. Run appropriate ImageJ macros:
   - If ch1 files exist: P-body with SG subtraction + SG processing
   - If no ch1 files: P-body only (no subtraction)
4. Copy ch0 files to processed directories
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Optional

from percell.domain.services.bs_preprocessing_service import BSPreprocessingService
from percell.ports.driven.imagej_integration_port import ImageJIntegrationPort
from percell.domain.services.package_resource_service import PackageResourceService

logger = logging.getLogger(__name__)


class BSWorkflow:
    """Orchestrates the complete BS preprocessing workflow."""

    def __init__(
        self,
        preprocessing_service: BSPreprocessingService,
        imagej_adapter: ImageJIntegrationPort,
        resource_service: PackageResourceService
    ):
        """Initialize BS workflow orchestrator.

        Args:
            preprocessing_service: Service for file operations
            imagej_adapter: Adapter for running ImageJ macros
            resource_service: Service for accessing package resources
        """
        self._preprocess = preprocessing_service
        self._imagej = imagej_adapter
        self._resources = resource_service

    def run_full_preprocessing(
        self,
        percell_analysis_dir: Path,
        output_dir: Optional[Path] = None,
        condition_map: Optional[dict[str, str]] = None
    ) -> Path:
        """Run the complete BS preprocessing workflow.

        Args:
            percell_analysis_dir: Path to percell analysis directory
            output_dir: Optional output directory (defaults to {analysis_dir}_BS)
            condition_map: Optional mapping for ch0 condition detection

        Returns:
            Path to the processed BS directory ready for intensity analysis

        Raises:
            FileNotFoundError: If required directories or files don't exist
            ImageJError: If ImageJ macro execution fails
        """
        logger.info("Starting BS preprocessing workflow")
        logger.info(f"Input: {percell_analysis_dir}")

        # Step 1: Prepare BS directory structure and copy files
        logger.info("Step 1: Preparing BS directory structure")
        bs_dir = self._preprocess.prepare_bs_directory(
            percell_analysis_dir,
            output_dir
        )
        logger.info(f"BS directory created at: {bs_dir}")

        # Step 2: Check if ch1 files exist to determine which macros to run
        has_stress_granules = self._check_for_ch1_files(bs_dir)

        if has_stress_granules:
            # Step 2a: Run P-body macro with SG subtraction
            logger.info("Step 2: Processing P-body data with SG subtraction")
            pb_macro_path = self._get_macro_path("pb_background_subtraction.ijm")
            self._imagej.run_macro(pb_macro_path, [str(bs_dir)])
            logger.info("P-body processing complete")

            # Step 3: Run stress granule macro
            logger.info("Step 3: Processing stress granule data")
            sg_macro_path = self._get_macro_path("sg_background_subtraction.ijm")
            self._imagej.run_macro(sg_macro_path, [str(bs_dir)])
            logger.info("Stress granule processing complete")
        else:
            # Step 2b: Run P-body only macro (no SG subtraction)
            logger.info("Step 2: No ch1 files detected, processing P-body only")
            pb_only_macro_path = self._get_macro_path(
                "pb_only_background_subtraction.ijm"
            )
            self._imagej.run_macro(pb_only_macro_path, [str(bs_dir)])
            logger.info("P-body only processing complete")

        # Step 4: Copy ch0 files to processed directories
        logger.info("Step 4: Copying ch0 files to processed directories")
        self._preprocess.copy_ch0_to_processed(
            percell_analysis_dir,
            bs_dir,
            condition_map
        )
        logger.info("Ch0 files copied")

        logger.info(f"BS preprocessing complete. Output: {bs_dir}")
        return bs_dir

    def _check_for_ch1_files(self, bs_dir: Path) -> bool:
        """Check if ch1/ch01 files exist in Masks or Raw Data directories.

        Args:
            bs_dir: BS directory containing Masks/ and Raw Data/

        Returns:
            True if ch1/ch01 files are found, False otherwise
        """
        masks_dir = bs_dir / "Masks"
        raw_data_dir = bs_dir / "Raw Data"

        # Check both directories for ch1 or ch01 files
        for directory in [masks_dir, raw_data_dir]:
            if directory.exists():
                # Look for files containing ch1 or ch01
                ch1_files = list(directory.glob("*ch1*.tif"))
                ch01_files = list(directory.glob("*ch01*.tif"))

                if ch1_files or ch01_files:
                    logger.info(
                        f"Found {len(ch1_files) + len(ch01_files)} ch1 files "
                        f"in {directory.name}"
                    )
                    return True

        logger.info("No ch1/ch01 files found, will use PB-only workflow")
        return False

    def _get_macro_path(self, macro_name: str) -> Path:
        """Get the path to a bundled ImageJ macro.

        Args:
            macro_name: Name of the macro file

        Returns:
            Path to the macro file

        Raises:
            FileNotFoundError: If macro file doesn't exist
        """
        # Try to get from package resources
        try:
            macro_path = self._resources.macro(macro_name)
            if macro_path.exists():
                return macro_path
        except Exception as e:
            logger.warning(f"Could not load macro from resources: {e}")

        # Fallback: look in percell/macros directory
        import percell
        package_dir = Path(percell.__file__).parent
        macro_path = package_dir / "macros" / macro_name

        if not macro_path.exists():
            raise FileNotFoundError(f"ImageJ macro not found: {macro_name}")

        return macro_path
