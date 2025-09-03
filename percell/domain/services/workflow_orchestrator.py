"""
Domain service: WorkflowOrchestrator.

Coordinates workflow execution using the outbound ports. This is a skeleton
aligned to the ports/adapters guide and can be expanded with real logic.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
import numpy as np

from percell.domain.entities.workflow import Workflow, WorkflowStep
from percell.domain.entities.image import Image
from percell.domain.entities.roi import ROI
from percell.domain.services.metadata_service import MetadataService
from percell.domain.services.cell_analyzer import CellAnalyzer
from percell.domain.services.threshold_calculator import ThresholdCalculator
from percell.domain.value_objects.file_path import FilePath
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
        Execute a workflow by iterating its steps and delegating to ports and
        domain services as appropriate. Uses parameters on the workflow to
        determine input/output locations and options.
        """
        workflow.start()

        params = workflow.parameters or {}
        input_dir = FilePath.from_string(params.get("input_dir", "."))
        output_dir = FilePath.from_string(params.get("output_dir", "./output"))
        segmentation_params = params.get("segmentation", {})
        selected_channels: Optional[List[str]] = params.get("channels")
        selected_timepoints: Optional[List[str]] = params.get("timepoints")
        selected_regions: Optional[List[str]] = params.get("regions")

        metadata_service = MetadataService(storage=self.storage, metadata_port=self.metadata)
        analyzer = CellAnalyzer()
        thresholder = ThresholdCalculator()

        try:
            for step in workflow.steps:
                step.start()
                if step.step_id == "data_selection":
                    selection = self._select_images(metadata_service, input_dir, selected_channels, selected_timepoints, selected_regions)
                    step.complete({"num_images": len(selection)})
                    workflow.results["selection"] = selection
                elif step.step_id == "segmentation":
                    selection = workflow.results.get("selection", [])
                    roi_outputs = self._segment_and_save_rois(selection, output_dir, segmentation_params)
                    step.complete({"roi_files": roi_outputs})
                    workflow.results["roi_files"] = roi_outputs
                elif step.step_id == "roi_processing":
                    # Placeholder for ROI validation/resize/duplication using ports/services if needed
                    step.complete()
                elif step.step_id == "cell_extraction":
                    selection = workflow.results.get("selection", [])
                    roi_files = workflow.results.get("roi_files", [])
                    extracted = self._extract_cells(selection, roi_files, output_dir)
                    step.complete({"cells": extracted})
                    workflow.results["cells"] = extracted
                elif step.step_id == "thresholding":
                    cells = workflow.results.get("cells", [])
                    masks = self._threshold_cells(cells, output_dir, thresholder)
                    step.complete({"masks": masks})
                    workflow.results["masks"] = masks
                elif step.step_id == "analysis":
                    masks = workflow.results.get("masks", [])
                    summary_path = self._analyze_masks(masks, output_dir, analyzer)
                    step.complete({"analysis_csv": str(summary_path) if summary_path else None})
                    workflow.results["analysis_csv"] = summary_path
                else:
                    step.complete()
            workflow.complete()
        except Exception as exc:
            step.fail(str(exc))
            workflow.fail()
        return workflow.get_execution_summary()

    def _select_images(
        self,
        metadata_service: MetadataService,
        input_dir: FilePath,
        channels: Optional[List[str]],
        timepoints: Optional[List[str]],
        regions: Optional[List[str]],
    ) -> List[Dict[str, Any]]:
        md_list = metadata_service.scan_directory_for_metadata(input_dir, recursive=True)
        def _ok(md) -> bool:
            if channels and getattr(md, "channel", None) not in set(channels):
                return False
            if timepoints and getattr(md, "timepoint", None) not in set(timepoints):
                return False
            if regions:
                reg = getattr(md, "region", "") or ""
                if not any((r in reg) or (reg in r) for r in regions):
                    return False
            return True
        selection: List[Dict[str, Any]] = []
        for md in md_list:
            if not getattr(md, "file_path", None):
                continue
            if not _ok(md):
                continue
            selection.append({
                "file": md.file_path,
                "condition": getattr(md, "condition", None),
                "region": getattr(md, "region", None),
                "channel": getattr(md, "channel", None),
                "timepoint": getattr(md, "timepoint", None),
            })
        return selection

    def _segment_and_save_rois(
        self,
        selection: List[Dict[str, Any]],
        output_root: FilePath,
        segmentation_params: Dict[str, Any],
    ) -> List[FilePath]:
        roi_outputs: List[FilePath] = []
        rois_root = output_root.join("ROIs")
        if not self.storage.directory_exists(rois_root):
            self.storage.create_directory(rois_root)
        for item in selection:
            img_path = FilePath.from_string(str(item["file"]))
            img = Image(image_id=img_path.get_stem(), file_path=img_path.path)
            params = dict(segmentation_params)
            params.setdefault("channel", item.get("channel"))
            params.setdefault("timepoint", item.get("timepoint"))
            rois: List[ROI] = self.segmentation.segment_cells(img, params)
            condition = item.get("condition") or "condition"
            target_dir = rois_root.join(condition)
            if not self.storage.directory_exists(target_dir):
                self.storage.create_directory(target_dir)
            region = item.get("region") or img_path.get_stem()
            channel = item.get("channel") or "ch00"
            timepoint = item.get("timepoint") or "t00"
            fname = f"ROIs_{region}_{channel}_{timepoint}_rois.zip"
            out_path = target_dir.join(fname)
            self.storage.write_roi_file(rois, out_path)
            roi_outputs.append(out_path)
        return roi_outputs

    def _extract_cells(
        self,
        selection: List[Dict[str, Any]],
        roi_files: List[FilePath],
        output_root: FilePath,
    ) -> List[FilePath]:
        cells_out: List[FilePath] = []
        cells_root = output_root.join("cells")
        if not self.storage.directory_exists(cells_root):
            self.storage.create_directory(cells_root)
        roi_index: Dict[str, List[ROI]] = {}
        for rf in roi_files:
            rois = self.storage.read_roi_file(rf)
            roi_index[str(rf.get_name())] = rois
        for item in selection:
            img_path = FilePath.from_string(str(item["file"]))
            img_data = self.storage.read_image(img_path)
            image = Image(image_id=img_path.get_stem(), data=img_data)
            condition = item.get("condition") or "condition"
            region = item.get("region") or image.image_id
            channel = item.get("channel") or "ch00"
            timepoint = item.get("timepoint") or "t00"
            key = f"ROIs_{region}_{channel}_{timepoint}_rois.zip"
            rois = roi_index.get(key)
            if not rois:
                continue
            target_dir = cells_root.join(condition).join(f"{region}_{channel}_{timepoint}")
            if not self.storage.directory_exists(target_dir):
                self.storage.create_directory(target_dir)
            for idx, roi in enumerate(rois, start=1):
                try:
                    crop = self.image_processing.extract_cell_region(image, roi, padding=0)
                    out_name = f"CELL{idx}.tif"
                    out_path = target_dir.join(out_name)
                    self.storage.write_image(crop.data, out_path)
                    cells_out.append(out_path)
                except Exception:
                    continue
        return cells_out

    def _threshold_cells(
        self,
        cell_paths: List[FilePath],
        output_root: FilePath,
        thresholder: ThresholdCalculator,
    ) -> List[FilePath]:
        masks_root = output_root.join("grouped_masks")
        if not self.storage.directory_exists(masks_root):
            self.storage.create_directory(masks_root)
        masks: List[FilePath] = []
        for cp in cell_paths:
            try:
                img = self.storage.read_image(cp)
                thr, mask = thresholder.generate_binary_mask(img)
                mask_out_dir = masks_root.join(cp.get_parent().get_parent().get_name())
                if not self.storage.directory_exists(mask_out_dir):
                    self.storage.create_directory(mask_out_dir)
                out_name = cp.get_stem() + "_mask.tif"
                out_path = mask_out_dir.join(out_name)
                self.storage.write_image((mask * 255).astype(img.dtype if np.issubdtype(img.dtype, np.integer) else np.uint8), out_path)  # type: ignore[name-defined]
                masks.append(out_path)
            except Exception:
                continue
        return masks

    def _analyze_masks(
        self,
        mask_paths: List[FilePath],
        output_root: FilePath,
        analyzer: CellAnalyzer,
    ) -> Optional[FilePath]:
        if not mask_paths:
            return None
        try:
            import csv
            analysis_dir = output_root.join("analysis")
            if not self.storage.directory_exists(analysis_dir):
                self.storage.create_directory(analysis_dir)
            out_csv = analysis_dir.join("combined_results.csv")
            rows: List[List[Any]] = [["path", "mean", "std", "min", "max"]]
            for mp in mask_paths:
                img = self.storage.read_image(mp)
                stats = analyzer.calculate_intensity_statistics(img)
                rows.append([str(mp), stats.mean, stats.std, stats.min, stats.max])
            content_lines = [",".join(map(str, row)) + "\n" for row in rows]
            self.storage.write_text_file("".join(content_lines), out_csv)
            return out_csv
        except Exception:
            return None


