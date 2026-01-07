"""Background subtraction preprocessing service.

Prepares percell analysis outputs for the Intensityanalysisbs plugin by:
1. Copying combined masks and raw data to BS directory structure
2. Processing P-body and stress granule data with ImageJ
3. Organizing outputs into the expected Processed directory format
"""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class BSPreprocessingService:
    """Service for preparing percell data for background subtraction intensity analysis."""

    def _detect_channel_pattern(self, data_dir: Path) -> str:
        """Detect whether files use ch0/ch1/ch2 or ch00/ch01/ch02 naming.

        Args:
            data_dir: Directory to search for channel files

        Returns:
            Channel pattern prefix: either "ch" or "ch0"
        """
        # Look for any tif files in the directory tree
        sample_files = list(data_dir.glob("**/*.tif"))[:20]  # Check first 20 files

        for f in sample_files:
            if not f.name.startswith("._"):
                # Check for zero-padded pattern (ch00, ch01, ch02)
                if "_ch00_" in f.name or "_ch01_" in f.name or "_ch02_" in f.name:
                    logger.info(f"Detected zero-padded channel naming (ch00/ch01/ch02)")
                    return "ch0"
                # Check for non-padded pattern (ch0, ch1, ch2)
                elif "_ch0_" in f.name or "_ch1_" in f.name or "_ch2_" in f.name:
                    logger.info(f"Detected standard channel naming (ch0/ch1/ch2)")
                    return "ch"

        # Default to standard naming if nothing detected
        logger.warning("Could not detect channel naming pattern, defaulting to ch0/ch1/ch2")
        return "ch"

    def prepare_bs_directory(
        self,
        percell_analysis_dir: Path,
        output_dir: Optional[Path] = None
    ) -> Path:
        """Prepare BS directory structure from percell analysis outputs.

        Args:
            percell_analysis_dir: Path to percell analysis directory containing
                                 combined_masks/ and raw_data/
            output_dir: Optional output directory. If None, creates {analysis_dir}_BS

        Returns:
            Path to the created BS directory

        Raises:
            FileNotFoundError: If required source directories don't exist
            ValueError: If percell_analysis_dir is invalid
        """
        if not percell_analysis_dir.exists():
            raise FileNotFoundError(f"Analysis directory not found: {percell_analysis_dir}")

        combined_masks_dir = percell_analysis_dir / "combined_masks"
        raw_data_dir = percell_analysis_dir / "raw_data"

        if not combined_masks_dir.exists():
            raise FileNotFoundError(f"combined_masks directory not found: {combined_masks_dir}")
        if not raw_data_dir.exists():
            raise FileNotFoundError(f"raw_data directory not found: {raw_data_dir}")

        # Determine output directory
        if output_dir is None:
            output_dir = percell_analysis_dir.parent / f"{percell_analysis_dir.name}_BS"

        # Create directory structure
        masks_dir = output_dir / "Masks"
        raw_dir = output_dir / "Raw Data"
        processed_dir = output_dir / "Processed"

        masks_dir.mkdir(parents=True, exist_ok=True)
        raw_dir.mkdir(parents=True, exist_ok=True)
        processed_dir.mkdir(parents=True, exist_ok=True)

        logger.info(f"Created BS directory structure at {output_dir}")

        # Detect channel naming pattern
        ch_pattern = self._detect_channel_pattern(raw_data_dir)

        # Copy mask files
        self._copy_masks(combined_masks_dir, masks_dir)

        # Copy ch1 and ch2 raw data files (or ch01 and ch02 if zero-padded)
        channels = [f"{ch_pattern}1", f"{ch_pattern}2"]
        self._copy_channel_data(raw_data_dir, raw_dir, channels=channels)

        logger.info(f"Copied masks and raw data to {output_dir}")

        return output_dir

    def _copy_masks(self, source_dir: Path, dest_dir: Path) -> None:
        """Copy all .tif mask files from source to destination.

        Searches recursively for .tif files to handle nested directory structures.

        Args:
            source_dir: Source directory containing masks
            dest_dir: Destination directory for masks
        """
        # Use recursive glob to find all .tif files, excluding macOS dot files
        mask_files = [f for f in source_dir.glob("**/*.tif") if not f.name.startswith("._")]
        logger.info(f"Copying {len(mask_files)} mask files")

        for mask_file in mask_files:
            dest_file = dest_dir / mask_file.name
            shutil.copy2(mask_file, dest_file)
            logger.debug(f"Copied {mask_file.name}")

    def _copy_channel_data(
        self,
        source_dir: Path,
        dest_dir: Path,
        channels: list[str]
    ) -> None:
        """Copy channel-specific .tif files from source to destination.

        Searches recursively for channel files to handle nested directory structures.

        Args:
            source_dir: Source directory containing raw data
            dest_dir: Destination directory for raw data
            channels: List of channel identifiers to copy (e.g., ["ch1", "ch2"])
        """
        for channel in channels:
            # Use recursive glob to find all channel files, excluding macOS dot files
            channel_files = [f for f in source_dir.glob(f"**/*{channel}*.tif") if not f.name.startswith("._")]
            logger.info(f"Copying {len(channel_files)} {channel} files")

            for channel_file in channel_files:
                dest_file = dest_dir / channel_file.name
                shutil.copy2(channel_file, dest_file)
                logger.debug(f"Copied {channel_file.name}")

    def copy_ch0_to_processed(
        self,
        percell_analysis_dir: Path,
        bs_dir: Path,
        condition_map: Optional[dict[str, str]] = None
    ) -> None:
        """Copy ch0 intensity files to Processed directories with renamed convention.

        Args:
            percell_analysis_dir: Path to percell analysis directory
            bs_dir: Path to BS directory with Processed subdirectories
            condition_map: Optional mapping of filename patterns to condition names.
                          If None, uses default detection of "1Hr_NaAsO2" and "Untreated"
        """
        raw_data_dir = percell_analysis_dir / "raw_data"
        processed_dir = bs_dir / "Processed"

        if not raw_data_dir.exists():
            raise FileNotFoundError(f"raw_data directory not found: {raw_data_dir}")
        if not processed_dir.exists():
            raise FileNotFoundError(f"Processed directory not found: {processed_dir}")

        # Default condition detection
        if condition_map is None:
            condition_map = {
                "1Hr_NaAsO2": "1Hr_NaAsO2",
                "Untreated": "Untreated"
            }

        # Detect channel naming pattern and search for ch0 or ch00 files
        ch_pattern = self._detect_channel_pattern(raw_data_dir)
        ch0_channel = f"{ch_pattern}0" if ch_pattern == "ch0" else "ch0"

        # Find all ch0/ch00 files recursively, excluding macOS dot files
        ch0_files = [f for f in raw_data_dir.glob(f"**/*{ch0_channel}*.tif") if not f.name.startswith("._")]
        logger.info(f"Found {len(ch0_files)} {ch0_channel} files to copy")

        for ch0_file in ch0_files:
            # Determine condition from filename
            condition = None
            for pattern, cond_name in condition_map.items():
                if pattern in ch0_file.name:
                    condition = cond_name
                    break

            if condition is None:
                logger.warning(f"Could not determine condition for {ch0_file.name}, skipping")
                continue

            # Check if condition subdirectory exists in Processed
            condition_dir = processed_dir / condition
            if not condition_dir.exists():
                logger.warning(f"Condition directory not found: {condition_dir}, skipping")
                continue

            # Create new filename: {condition}_Cap_Intensity.tif
            new_filename = f"{condition}_Cap_Intensity.tif"
            dest_file = condition_dir / new_filename

            shutil.copy2(ch0_file, dest_file)
            logger.info(f"Copied {ch0_file.name} -> {condition}/{new_filename}")

    def extract_condition_from_filename(self, filename: str) -> Optional[str]:
        """Extract condition identifier from a mask or raw data filename.

        Expected format: MASK_MAX_z-stack_{condition}_Merged_ch{X}_t00.tif
                        or MAX_z-stack_{condition}_Merged_ch{X}_t00.tif

        Args:
            filename: The filename to parse

        Returns:
            Condition string or None if not found
        """
        # Remove common prefixes
        name = filename
        for prefix in ["MASK_MAX_z-stack_", "MAX_z-stack_"]:
            if name.startswith(prefix):
                name = name[len(prefix):]
                break

        # Remove common suffixes
        for suffix in ["_Merged_ch1_t00.tif", "_Merged_ch2_t00.tif", "_Merged_ch0_t00.tif"]:
            if name.endswith(suffix):
                name = name[:-len(suffix)]
                break

        return name if name else None

    def get_conditions_from_masks(self, masks_dir: Path) -> list[str]:
        """Extract unique condition identifiers from mask files.

        Args:
            masks_dir: Directory containing mask files

        Returns:
            List of unique condition identifiers
        """
        conditions = set()
        mask_files = list(masks_dir.glob("MASK_MAX_z-stack_*_ch*.tif"))

        for mask_file in mask_files:
            condition = self.extract_condition_from_filename(mask_file.name)
            if condition:
                conditions.add(condition)

        return sorted(list(conditions))
