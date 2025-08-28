from __future__ import annotations

from typing import Dict, List, Optional

from percell.domain.plugin import AnalysisPlugin, AnalysisContext, AnalysisResult


class PluginManager:
    """Registry and executor for `AnalysisPlugin` implementations."""

    def __init__(self) -> None:
        self._plugins: Dict[str, AnalysisPlugin] = {}

    def register_plugin(self, plugin: AnalysisPlugin) -> None:
        self._plugins[plugin.name] = plugin

    def get_available_plugins(self) -> List[str]:
        return sorted(self._plugins.keys())

    def get(self, name: str) -> Optional[AnalysisPlugin]:
        return self._plugins.get(name)

    def execute_plugin(self, name: str, context: AnalysisContext) -> AnalysisResult:
        plugin = self.get(name)
        if plugin is None:
            return AnalysisResult(success=False, details={"error": f"Plugin not found: {name}"})

        if not plugin.validate_inputs(context):
            return AnalysisResult(success=False, details={"error": "Input validation failed"})

        return plugin.process(context)


__all__ = ["PluginManager"]


