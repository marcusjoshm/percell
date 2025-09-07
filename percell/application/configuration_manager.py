from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Optional
import json
import tempfile


@dataclass(slots=True)
class ConfigurationManager:
    """Application-layer configuration manager with simple nested get/set.

    Stores config as JSON on disk. Supports dot-path access (e.g.,
    "paths.imagej") for nested dictionaries.
    """

    path: Path
    _data: Dict[str, Any] = field(default_factory=dict)

    def load(self) -> None:
        if self.path.exists():
            self._data = json.loads(self.path.read_text(encoding="utf-8"))
        else:
            self._data = {}

    def save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        tmp_fd, tmp_name = tempfile.mkstemp(prefix="cfg_", suffix=".json", dir=str(self.path.parent))
        tmp_path = Path(tmp_name)
        try:
            tmp_path.write_text(json.dumps(self._data, indent=2, sort_keys=True), encoding="utf-8")
            tmp_path.replace(self.path)
        finally:
            if tmp_path.exists() and tmp_path != self.path:
                try:
                    tmp_path.unlink()
                except Exception:
                    pass

    def get(self, key: str, default: Any = None) -> Any:
        return self._data.get(key, default)

    def set(self, key: str, value: Any) -> None:
        self._data[key] = value

    def get_nested(self, dotted: str, default: Any = None) -> Any:
        node: Any = self._data
        for part in dotted.split('.'):
            if isinstance(node, dict) and part in node:
                node = node[part]
            else:
                return default
        return node

    def set_nested(self, dotted: str, value: Any) -> None:
        parts = dotted.split('.')
        node: Dict[str, Any] = self._data
        for part in parts[:-1]:
            nxt = node.get(part)
            if not isinstance(nxt, dict):
                nxt = {}
                node[part] = nxt
            node = nxt
        node[parts[-1]] = value

    def update(self, values: Dict[str, Any]) -> None:
        self._data.update(values)


