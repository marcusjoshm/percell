from __future__ import annotations

"""Application-level configuration API compatible with legacy core.config.

Exposes: Config, ConfigError, create_default_config, validate_software_paths,
detect_software_paths
"""

import json
from pathlib import Path
from typing import Any, Dict


class ConfigError(Exception):
    pass


class Config:
    def __init__(self, config_path: str):
        self.config_path = Path(config_path)
        self.config_data: Dict[str, Any] = {}
        self.load()

    def load(self) -> None:
        if not self.config_path.exists():
            raise ConfigError(f"Configuration file not found: {self.config_path}")
        try:
            self.config_data = json.loads(self.config_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as e:
            raise ConfigError(f"Invalid JSON in configuration file: {e}")
        except Exception as e:
            raise ConfigError(f"Error loading configuration: {e}")

    def save(self) -> None:
        try:
            self.config_path.parent.mkdir(parents=True, exist_ok=True)
            self.config_path.write_text(json.dumps(self.config_data, indent=2), encoding="utf-8")
        except Exception as e:
            raise ConfigError(f"Error saving configuration: {e}")

    def get(self, key: str, default: Any = None) -> Any:
        parts = key.split('.')
        node: Any = self.config_data
        for part in parts:
            if isinstance(node, dict) and part in node:
                node = node[part]
            else:
                return default
        return node

    def set(self, key: str, value: Any) -> None:
        parts = key.split('.')
        node: Dict[str, Any] = self.config_data
        for part in parts[:-1]:
            nxt = node.get(part)
            if not isinstance(nxt, dict):
                nxt = {}
                node[part] = nxt
            node = nxt
        node[parts[-1]] = value

    def validate(self) -> bool:
        # Be permissive: only python_path is strictly required for running the CLI
        # External tools (ImageJ/Cellpose) may be configured later or not used in all flows
        required_keys = ["python_path"]
        missing = [k for k in required_keys if not self.get(k)]
        if missing:
            raise ConfigError(f"Missing required configuration keys: {missing}")
        return True

    def to_dict(self) -> Dict[str, Any]:
        return dict(self.config_data)

    def update(self, updates: Dict[str, Any]) -> None:
        for k, v in updates.items():
            self.set(k, v)

    def get_software_paths(self) -> Dict[str, str]:
        return {
            "imagej": self.get("imagej_path", ""),
            "cellpose": self.get("cellpose_path", ""),
            "python": self.get("python_path", ""),
            "fiji": self.get("fiji_path", ""),
        }

    def get_analysis_settings(self) -> Dict[str, Any]:
        return {
            "default_bins": self.get("analysis.default_bins", 5),
            "segmentation_model": self.get("analysis.segmentation_model", "cyto"),
            "cell_diameter": self.get("analysis.cell_diameter", 100),
            "niter_dynamics": self.get("analysis.niter_dynamics", 250),
            "flow_threshold": self.get("analysis.flow_threshold", 0.4),
            "cellprob_threshold": self.get("analysis.cellprob_threshold", 0),
        }

    def get_output_settings(self) -> Dict[str, Any]:
        return {
            "create_subdirectories": self.get("output.create_subdirectories", True),
            "save_intermediate": self.get("output.save_intermediate", True),
            "compression": self.get("output.compression", "lzw"),
            "overwrite": self.get("output.overwrite", False),
        }


def create_default_config(config_path: str) -> Config:
    default = {
        "imagej_path": "",
        "cellpose_path": "",
        "python_path": "",
        "fiji_path": "",
        "analysis": {
            "default_bins": 5,
            "segmentation_model": "cyto",
            "cell_diameter": 100,
            "niter_dynamics": 250,
            "flow_threshold": 0.4,
            "cellprob_threshold": 0,
        },
        "output": {
            "create_subdirectories": True,
            "save_intermediate": True,
            "compression": "lzw",
            "overwrite": False,
        },
        "directories": {
            "input": "",
            "output": "",
            "recent_inputs": [],
            "recent_outputs": [],
        },
        "data_selection": {
            "selected_datatype": None,
            "selected_conditions": [],
            "selected_timepoints": [],
            "selected_regions": [],
            "segmentation_channel": None,
            "analysis_channels": [],
            "experiment_metadata": {
                "conditions": [],
                "regions": [],
                "timepoints": [],
                "channels": [],
                "region_to_channels": {},
                "datatype_inferred": None,
                "directory_timepoints": [],
            },
        },
    }

    path = Path(config_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(default, indent=2), encoding="utf-8")
    return Config(str(path))


def validate_software_paths(config: Config) -> Dict[str, bool]:
    results: Dict[str, bool] = {}
    paths = config.get_software_paths()
    for software, p in paths.items():
        pth = Path(p) if p else None
        if software == "python":
            results[software] = bool(pth and pth.exists() and pth.is_file())
        else:
            results[software] = bool(pth and pth.exists() and pth.is_dir())
    return results


def detect_software_paths() -> Dict[str, str]:
    detected: Dict[str, str] = {}
    # Python path
    import sys

    detected["python"] = sys.executable

    # ImageJ/Fiji common locations
    for candidate in [
        "/Applications/ImageJ.app",
        "/Applications/Fiji.app",
        "/usr/local/ImageJ",
        "/opt/ImageJ",
    ]:
        if Path(candidate).exists():
            detected["imagej"] = candidate
            break

    # Cellpose importability check (best-effort)
    import subprocess

    try:
        result = subprocess.run(
            [sys.executable, "-c", "import cellpose; import pathlib; print(pathlib.Path(cellpose.__file__).parent)"] ,
            capture_output=True,
            text=True,
            timeout=10,
        )
        if result.returncode == 0:
            detected["cellpose"] = result.stdout.strip()
        else:
            detected["cellpose"] = ""
    except Exception:
        detected["cellpose"] = ""

    return detected


