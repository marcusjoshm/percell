from __future__ import annotations

"""
Application-level centralized paths API, compatible with legacy percell.core.paths
exports. Provides `get_path`, `get_path_str`, `path_exists`, `ensure_executable`,
`list_all_paths`, and `get_path_config`.
"""

from pathlib import Path
from typing import Dict
import sys


class PathConfig:
    def __init__(self) -> None:
        self._package_root = self._find_package_root()
        self._paths = self._initialize_paths()

    def _find_package_root(self) -> Path:
        current_file = Path(__file__)
        package_root = current_file.parent.parent  # percell/
        expected_dirs = ["bash", "config", "macros", "core", "modules"]
        if all((package_root / d).exists() for d in expected_dirs):
            return package_root
        for p in sys.path:
            pr = Path(p) / "percell"
            if pr.exists() and all((pr / d).exists() for d in expected_dirs):
                return pr
        cwd = Path.cwd()
        pr = cwd / "percell"
        if pr.exists() and all((pr / d).exists() for d in expected_dirs):
            return pr
        cur = cwd
        for _ in range(10):
            pr = cur / "percell"
            if pr.exists() and all((pr / d).exists() for d in expected_dirs):
                return pr
            if cur == cur.parent:
                break
            cur = cur.parent
        return Path(__file__).parent.parent

    def _initialize_paths(self) -> Dict[str, Path]:
        root = self._package_root
        return {
            "package_root": root,
            "core": root / "core",
            "modules": root / "modules",
            "main": root / "main",
            "config_dir": root / "config",
            "config_template": root / "config" / "config.template.json",
            "config_default": root / "config" / "config.json",
            "bash_dir": root / "bash",
            "setup_output_structure_script": root / "bash" / "setup_output_structure.sh",
            "prepare_input_structure_script": root / "bash" / "prepare_input_structure.sh",
            "launch_segmentation_tools_script": root / "bash" / "launch_segmentation_tools.sh",
            "duplicate_rois_for_channels_module": root / "modules" / "duplicate_rois_for_channels.py",
            "include_group_metadata_module": root / "modules" / "include_group_metadata.py",
            "otsu_threshold_grouped_cells_module": root / "modules" / "otsu_threshold_grouped_cells.py",
            "set_directories_module": root / "modules" / "set_directories.py",
            "stage_classes_module": root / "modules" / "stage_classes.py",
            "stage_registry_module": root / "modules" / "stage_registry.py",
            "track_rois_module": root / "modules" / "track_rois.py",
            "macros_dir": root / "macros",
            "analyze_cell_masks_macro": root / "macros" / "analyze_cell_masks.ijm",
            "create_cell_masks_macro": root / "macros" / "create_cell_masks.ijm",
            "extract_cells_macro": root / "macros" / "extract_cells.ijm",
            "measure_roi_area_macro": root / "macros" / "measure_roi_area.ijm",
            "resize_rois_macro": root / "macros" / "resize_rois.ijm",
            "threshold_grouped_cells_macro": root / "macros" / "threshold_grouped_cells.ijm",
            "art_dir": root / "art",
            "percell_terminal_window_image": root / "art" / "percell_terminal_window.png",
            "setup_dir": root / "setup",
            "requirements_file": root / "setup" / "requirements.txt",
            "requirements_cellpose_file": root / "setup" / "requirements_cellpose.txt",
            "install_script": root / "setup" / "install.py",
        }

    def get_path(self, path_name: str) -> Path:
        if path_name not in self._paths:
            raise KeyError(f"Path '{path_name}' not found. Available paths: {list(self._paths.keys())}")
        return self._paths[path_name]

    def get_path_str(self, path_name: str) -> str:
        return str(self.get_path(path_name))

    def exists(self, path_name: str) -> bool:
        try:
            return self.get_path(path_name).exists()
        except KeyError:
            return False

    def ensure_executable(self, path_name: str) -> None:
        file_path = self.get_path(path_name)
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        file_path.chmod(0o755)

    def list_paths(self) -> Dict[str, str]:
        return {name: str(path) for name, path in self._paths.items()}

    def get_package_root(self) -> Path:
        return self._package_root


_path_config: PathConfig | None = None


def get_path_config() -> PathConfig:
    global _path_config
    if _path_config is None:
        _path_config = PathConfig()
    return _path_config


def get_path(path_name: str) -> Path:
    return get_path_config().get_path(path_name)


def get_path_str(path_name: str) -> str:
    return get_path_config().get_path_str(path_name)


def path_exists(path_name: str) -> bool:
    return get_path_config().exists(path_name)


def ensure_executable(path_name: str) -> None:
    get_path_config().ensure_executable(path_name)


def list_all_paths() -> Dict[str, str]:
    return get_path_config().list_paths()


