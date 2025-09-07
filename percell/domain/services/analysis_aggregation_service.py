"""Aggregation and CSV generation of analysis results."""

from __future__ import annotations

from pathlib import Path

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

        raise NotImplementedError

    def generate_csv(self, result: AnalysisResult, output_path: Path) -> Path:
        """Generate a CSV file from analysis results.

        Args:
            result: Aggregated analysis result.
            output_path: Desired path for the CSV file.

        Returns:
            Path to the generated CSV file.
        """

        raise NotImplementedError


