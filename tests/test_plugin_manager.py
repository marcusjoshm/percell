from __future__ import annotations

from percell.services.plugin_manager import PluginManager
from percell.plugins.registry import register_all_plugins
from percell.domain.plugin import AnalysisContext


def test_plugin_manager_registration_and_execution():
    manager = PluginManager()
    register_all_plugins(manager)

    available = manager.get_available_plugins()
    assert "sample_noop" in available

    ctx = AnalysisContext(input_dir="/tmp", output_dir="/tmp", parameters={})
    result = manager.execute_plugin("sample_noop", ctx)
    assert result.success
    assert result.details.get("message") == "noop"


