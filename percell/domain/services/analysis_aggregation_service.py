"""Aggregation and CSV generation of analysis results."""

from __future__ import annotations

from pathlib import Path
from typing import List, Dict, Any

from ..models import AnalysisResult


class AnalysisAggregationService:
    """Combines results and produces summary artifacts."""

    def combine_results(self, results: list[AnalysisResult]) -> AnalysisResult:
        """Combine multiple analysis results into a single aggregate.

        Args:
            results: Individual results to merge.

        Returns:
            Aggregated result instance.
        """
        combined = AnalysisResult()
        for r in results or []:
            if r and r.metrics:
                combined.metrics.extend(r.metrics)
        return combined

    def to_tabular(self, result: AnalysisResult) -> List[Dict[str, Any]]:
        """Convert analysis result into tabular rows (pure data, no I/O).

        Adapters are responsible for serializing these rows to CSV/Excel/etc.
        """
        rows: List[Dict[str, Any]] = []
        for m in result.metrics:
            rows.append(
                {
                    "cell_id": m.cell_id,
                    "area": m.area,
                    "mean_intensity": m.mean_intensity,
                    "integrated_intensity": m.integrated_intensity,
                    "perimeter": m.perimeter,
                }
            )
        return rows

    def combine_summary_tables(self, tables: List[List[Dict[str, Any]]]) -> List[Dict[str, Any]]:
        """Combine multiple tabular summaries into a single list of rows.

        This is a pure data operation; adapters supply the rows.
        """
        combined: List[Dict[str, Any]] = []
        for t in tables or []:
            if not t:
                continue
            combined.extend(t)
        return combined


