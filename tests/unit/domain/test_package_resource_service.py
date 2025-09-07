from pathlib import Path
import pytest

from percell.domain.services.package_resource_service import PackageResourceService


def test_verify_root_and_resource_access():
    root = Path(__file__).resolve().parents[3] / 'percell'
    svc = PackageResourceService(package_root=root)
    assert svc.verify_root() is True
    # Known resources
    assert svc.bash('launch_segmentation_tools.sh').exists()
    assert svc.config('config.json').exists()
    assert svc.macro('analyze_cell_masks.ijm').exists()


def test_missing_resource_raises():
    root = Path(__file__).resolve().parents[3] / 'percell'
    svc = PackageResourceService(package_root=root)
    with pytest.raises(FileNotFoundError):
        svc.resource('does/not/exist.xyz')


