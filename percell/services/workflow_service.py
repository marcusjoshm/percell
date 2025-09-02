from __future__ import annotations

from typing import List, Optional

from percell.infrastructure.filesystem.paths import get_path, get_path_str
from percell.services.module_runner import ModuleRunner
from percell.main.composition_root import get_composition_root


class WorkflowService:
    """High-level helpers that wrap legacy Python modules with consistent execution."""

    def __init__(self, module_runner: ModuleRunner) -> None:
        self._runner = module_runner
        # Try to get the hexagonal workflow service if available
        try:
            self._hexagonal_service = get_composition_root().get_service('hexagonal_workflow_service')
            self._use_hexagonal = True
        except Exception:
            self._hexagonal_service = None
            self._use_hexagonal = False

    def bin_images(self, output_dir: str, conditions: List[str], regions: List[str], timepoints: List[str], channels: List[str]) -> int:
        # Use hexagonal service if available
        if self._use_hexagonal and self._hexagonal_service:
            return self._hexagonal_service.bin_images(output_dir, conditions, regions, timepoints, channels)
        
        # Fall back to old module-based approach
        script = get_path("bin_images_module")
        args: List[str] = [
            "--input", f"{output_dir}/raw_data",
            "--output", f"{output_dir}/preprocessed",
            "--verbose",
        ]
        if conditions:
            args.extend(["--conditions"] + conditions)
        if regions:
            args.extend(["--regions"] + regions)
        if timepoints:
            args.extend(["--timepoints"] + timepoints)
        if channels:
            args.extend(["--channels"] + channels)
        return self._runner.run(str(script), args, title="bin_images")

    def combine_masks(self, output_dir: str, analysis_channels: List[str]) -> int:
        # Use hexagonal service if available
        if self._use_hexagonal and self._hexagonal_service:
            return self._hexagonal_service.combine_masks(output_dir, analysis_channels)
        
        # Fall back to old module-based approach
        script = get_path("combine_masks_module")
        args: List[str] = [
            "--input-dir", f"{output_dir}/grouped_masks",
            "--output-dir", f"{output_dir}/combined_masks",
            "--channels",
        ] + analysis_channels
        return self._runner.run(str(script), args, title="combine_masks")

    def create_cell_masks(self, output_dir: str, imagej_path: str, analysis_channels: List[str]) -> int:
        # Use hexagonal service if available
        if self._use_hexagonal and self._hexagonal_service:
            return self._hexagonal_service.create_cell_masks(output_dir, imagej_path, analysis_channels)
        
        # Fall back to old module-based approach
        script = get_path("create_cell_masks_module")
        args: List[str] = [
            "--roi-dir", f"{output_dir}/ROIs",
            "--mask-dir", f"{output_dir}/combined_masks",
            "--output-dir", f"{output_dir}/masks",
            "--imagej", imagej_path,
            "--macro", get_path_str("create_cell_masks_macro"),
            "--auto-close",
            "--channels",
        ] + analysis_channels
        return self._runner.run(str(script), args, title="create_masks")

    def analyze_cell_masks(self, output_dir: str, imagej_path: str, regions: Optional[List[str]], timepoints: Optional[List[str]], analysis_channels: List[str]) -> int:
        script = get_path("analyze_cell_masks_module")
        args: List[str] = [
            "--input", f"{output_dir}/masks",
            "--output", f"{output_dir}/analysis",
            "--imagej", imagej_path,
            "--macro", get_path_str("analyze_cell_masks_macro"),
            "--channels",
        ] + analysis_channels
        if regions:
            args.extend(["--regions"] + regions)
        if timepoints:
            args.extend(["--timepoints"] + timepoints)
        return self._runner.run(str(script), args, title="analyze_masks")

    def threshold_grouped_cells(self, output_dir: str, imagej_path: str, analysis_channels: List[str]) -> int:
        # Use hexagonal service if available
        if self._use_hexagonal and self._hexagonal_service:
            return self._hexagonal_service.threshold_grouped_cells(output_dir, imagej_path, analysis_channels)
        
        # Fall back to old module-based approach
        script = get_path("otsu_threshold_grouped_cells_module")
        args: List[str] = [
            "--input-dir", f"{output_dir}/grouped_cells",
            "--output-dir", f"{output_dir}/grouped_masks",
            "--imagej", imagej_path,
            "--macro", get_path_str("threshold_grouped_cells_macro"),
            "--channels",
        ] + analysis_channels
        return self._runner.run(str(script), args, title="threshold")

    def include_group_metadata(self, output_dir: str, analysis_channels: List[str]) -> int:
        # Use hexagonal service if available
        if self._use_hexagonal and self._hexagonal_service:
            return self._hexagonal_service.include_group_metadata(output_dir, analysis_channels)
        
        # Fall back to old module-based approach
        script = get_path("include_group_metadata_module")
        args: List[str] = [
            "--grouped-cells-dir", f"{output_dir}/grouped_cells",
            "--analysis-dir", f"{output_dir}/analysis",
            "--output-dir", f"{output_dir}/analysis",
            "--overwrite",
            "--replace",
            "--verbose",
            "--channels",
        ] + analysis_channels
        return self._runner.run(str(script), args, title="metadata")

    # Process single-cell helpers
    def track_rois(self, output_dir: str, timepoints: List[str]) -> int:
        # Use hexagonal service if available
        if self._use_hexagonal and self._hexagonal_service:
            return self._hexagonal_service.track_rois(output_dir, timepoints)
        
        # Fall back to old module-based approach
        script = get_path("track_rois_module")
        args: List[str] = [
            "--input", f"{output_dir}/preprocessed",
            "--timepoints",
        ] + timepoints + ["--recursive"]
        return self._runner.run(str(script), args, title="track_rois")

    def resize_rois(self, output_dir: str, imagej_path: str, segmentation_channel: str) -> int:
        # Use hexagonal service if available
        if self._use_hexagonal and self._hexagonal_service:
            # Note: The hexagonal service has a different signature, so we'll use the old approach for now
            pass
        
        # Fall back to old module-based approach
        script = get_path("resize_rois_module")
        args: List[str] = [
            "--input", f"{output_dir}/preprocessed",
            "--output", f"{output_dir}/ROIs",
            "--imagej", imagej_path,
            "--channel", segmentation_channel,
            "--macro", get_path_str("resize_rois_macro"),
            "--auto-close",
        ]
        return self._runner.run(str(script), args, title="resize_rois")

    def duplicate_rois_for_channels(
        self,
        output_dir: str,
        segmentation_channel: str,
        conditions: List[str],
        regions: List[str],
        timepoints: List[str],
        analysis_channels: List[str],
    ) -> int:
        # Use hexagonal service if available
        if self._use_hexagonal and self._hexagonal_service:
            # Note: The hexagonal service has a different signature, so we'll use the old approach for now
            pass
        
        # Fall back to old module-based approach
        script = get_path("duplicate_rois_for_channels_module")
        args: List[str] = [
            "--roi-dir", f"{output_dir}/ROIs",
            "--segmentation-channel", segmentation_channel,
        ]
        if conditions:
            args += ["--conditions"] + conditions
        if regions:
            args += ["--regions"] + regions
        if timepoints:
            args += ["--timepoints"] + timepoints
        args += ["--channels"] + analysis_channels + ["--verbose"]
        return self._runner.run(str(script), args, title="dup_rois")

    def extract_cells(self, output_dir: str, imagej_path: str, analysis_channels: List[str]) -> int:
        # Use hexagonal service if available
        if self._use_hexagonal and self._hexagonal_service:
            # Note: The hexagonal service has a different signature, so we'll use the old approach for now
            pass
        
        # Fall back to old module-based approach
        script = get_path("extract_cells_module")
        args: List[str] = [
            "--roi-dir", f"{output_dir}/ROIs",
            "--raw-data-dir", f"{output_dir}/raw_data",
            "--output-dir", f"{output_dir}/cells",
            "--imagej", imagej_path,
            "--macro", get_path_str("extract_cells_macro"),
            "--auto-close",
            "--channels",
        ] + analysis_channels
        return self._runner.run(str(script), args, title="extract")

    def group_cells(self, output_dir: str, bins: int, analysis_channels: List[str]) -> int:
        # Use hexagonal service if available
        if self._use_hexagonal and self._hexagonal_service:
            return self._hexagonal_service.group_cells(output_dir, bins, analysis_channels)
        
        # Fall back to old module-based approach
        script = get_path("group_cells_module")
        args: List[str] = [
            "--cells-dir", f"{output_dir}/cells",
            "--output-dir", f"{output_dir}/grouped_cells",
            "--bins", str(bins),
            "--force-clusters",
            "--channels",
        ] + analysis_channels
        return self._runner.run(str(script), args, title="group_cells")


__all__ = ["WorkflowService"]


