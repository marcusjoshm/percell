from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Any

from percell.services.plugin_manager import PluginManager
from percell.domain.plugin import AnalysisPlugin, AnalysisContext, AnalysisResult


class _AlwaysInvalidPlugin(AnalysisPlugin):
    @property
    def name(self) -> str:
        return "always_invalid"

    def validate_inputs(self, context: AnalysisContext) -> bool:
        return False

    def process(self, context: AnalysisContext) -> AnalysisResult:
        # Should never be called
        return AnalysisResult(success=True, details={})


def test_plugin_manager_invalid_name_returns_error():
    manager = PluginManager()
    ctx = AnalysisContext(input_dir="/tmp", output_dir="/tmp", parameters={})
    result = manager.execute_plugin("does_not_exist", ctx)
    assert result.success is False
    assert "Plugin not found" in result.details.get("error", "")


def test_plugin_manager_validation_failure_returns_error():
    manager = PluginManager()
    manager.register_plugin(_AlwaysInvalidPlugin())
    ctx = AnalysisContext(input_dir="/tmp", output_dir="/tmp", parameters={})
    result = manager.execute_plugin("always_invalid", ctx)
    assert result.success is False
    assert "validation" in result.details.get("error", "").lower()


