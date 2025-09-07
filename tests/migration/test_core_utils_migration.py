from pathlib import Path
import stat
import pytest
import importlib.util

# Skip this migration test if utils module (or core package) no longer exists
try:
    spec = importlib.util.find_spec("percell.core.utils")
except ModuleNotFoundError:
    spec = None
if spec is None:
    pytest.skip("percell.core.utils removed after migration", allow_module_level=True)

from percell.core import utils as legacy
from percell.application.paths_api import get_path_config


def test_get_package_root_matches_paths():
    cfg = get_path_config()
    assert legacy.get_package_root() == cfg.get_package_root()


def test_get_package_resource_and_helpers_exist():
    root = legacy.get_package_root()
    # Known resources
    bash_script = legacy.get_bash_script('launch_segmentation_tools.sh')
    assert bash_script.exists()
    cfg_file = legacy.get_config_file('config.json')
    assert cfg_file.exists()
    macro_file = legacy.get_macro_file('analyze_cell_masks.ijm')
    assert macro_file.exists()
    # Generic resource
    assert legacy.get_package_resource('bash/prepare_input_structure.sh').exists()


def test_get_package_resource_missing_raises():
    with pytest.raises(FileNotFoundError):
        legacy.get_package_resource('nope/does_not_exist.xyz')


def test_ensure_executable_sets_exec_bit(tmp_path: Path):
    f = tmp_path / 'run.sh'
    f.write_text('#!/bin/sh\necho ok\n')
    f.chmod(0o644)
    legacy.ensure_executable(f)
    mode = f.stat().st_mode
    assert mode & stat.S_IXUSR


