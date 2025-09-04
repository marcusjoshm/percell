from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Optional

from percell.ports.inbound.configuration_port import ConfigurationPort


class JSONConfigurationAdapter(ConfigurationPort):
    """JSON-backed configuration adapter compatible with the ConfigurationPort."""

    def __init__(self, path: Path):
        self._path = Path(path)
        self._data: Dict[str, Any] = {}

    def load(self) -> None:
        if self._path.exists():
            with self._path.open('r', encoding='utf-8') as f:
                self._data = json.load(f)
        else:
            self._data = {}

    def save(self) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        with self._path.open('w', encoding='utf-8') as f:
            json.dump(self._data, f, indent=2)

    def get(self, key_path: str, default: Optional[Any] = None) -> Any:
        parts = key_path.split('.') if key_path else []
        node: Any = self._data
        for p in parts:
            if isinstance(node, dict) and p in node:
                node = node[p]
            else:
                return default
        return node

    def set(self, key_path: str, value: Any) -> None:
        parts = key_path.split('.') if key_path else []
        node: Dict[str, Any] = self._data
        for p in parts[:-1]:
            if p not in node or not isinstance(node[p], dict):
                node[p] = {}
            node = node[p]  # type: ignore[assignment]
        if parts:
            node[parts[-1]] = value

    def to_dict(self) -> Dict[str, Any]:
        return dict(self._data)


