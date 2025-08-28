from __future__ import annotations

from percell.domain.plugin import AnalysisPlugin, AnalysisContext, AnalysisResult


class SampleAnalysisPlugin(AnalysisPlugin):
    """A minimal example plugin that no-ops successfully."""

    @property
    def name(self) -> str:
        return "sample_noop"

    def validate_inputs(self, context: AnalysisContext) -> bool:
        return True

    def process(self, context: AnalysisContext) -> AnalysisResult:
        return AnalysisResult(success=True, details={"message": "noop"})


__all__ = ["SampleAnalysisPlugin"]


