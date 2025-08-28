from __future__ import annotations

from typing import Optional

from percell.services.plugin_manager import PluginManager
from percell.domain.plugin import AnalysisPlugin


def register_all_plugins(manager: PluginManager, *extra_plugins: AnalysisPlugin) -> None:
    """Register all built-in plugins and any provided extra plugins."""
    try:
        from .sample_analysis_plugin import SampleAnalysisPlugin
        manager.register_plugin(SampleAnalysisPlugin())
    except Exception:
        # Safe to ignore if sample plugin not available
        pass

    for plugin in extra_plugins:
        try:
            manager.register_plugin(plugin)
        except Exception:
            pass


__all__ = ["register_all_plugins"]


