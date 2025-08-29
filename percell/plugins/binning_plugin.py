from __future__ import annotations

from typing import Any, Dict

from percell.domain.plugin import AnalysisPlugin, AnalysisContext, AnalysisResult
from percell.domain.services.image_binning_service import ImageBinningService


class BinningPlugin(AnalysisPlugin):
    @property
    def name(self) -> str:
        return "bin_images"

    def validate_inputs(self, context: AnalysisContext) -> bool:
        return bool(context.input_dir and context.output_dir)

    def process(self, context: AnalysisContext) -> AnalysisResult:
        service = ImageBinningService()
        p: Dict[str, Any] = context.parameters or {}
        processed = service.bin_images(
            input_dir=context.input_dir,
            output_dir=context.output_dir,
            bin_factor=int(p.get("bin_factor", 4)),
            conditions=p.get("conditions"),
            regions=p.get("regions"),
            timepoints=p.get("timepoints"),
            channels=p.get("channels"),
        )
        return AnalysisResult(success=True, details={"processed": processed})


__all__ = ["BinningPlugin"]


