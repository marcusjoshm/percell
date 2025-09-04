from pathlib import Path
from unittest.mock import Mock

from percell.application.use_cases.track_rois import TrackROIsUseCase
from percell.domain.services.roi_tracking_service import ROITrackingService, ROI


def test_track_rois_use_case_simple(tmp_path: Path):
    tracker = ROITrackingService()
    repo = Mock()

    # Create two simple ROI sets: centers at (0,0) and (10,0)
    rois0 = [ROI(id=0, left=0, top=0, width=2, height=2), ROI(id=1, left=9, top=0, width=2, height=2)]
    rois1 = [ROI(id=10, left=10, top=0, width=2, height=2), ROI(id=11, left=0, top=0, width=2, height=2)]
    names0 = ['a', 'b']
    names1 = ['c', 'd']

    bytes_map1 = {'c': b'1', 'd': b'2'}
    repo.load_rois.side_effect = [ (rois0, names0, {}), (rois1, names1, bytes_map1) ]

    output_zip = tmp_path / 'out.zip'
    use_case = TrackROIsUseCase(tracker, repo)
    result = use_case.execute(Path('t0.zip'), Path('t1.zip'), output_zip)

    assert result.matched_count == 2
    repo.save_reordered.assert_called()


def test_track_rois_use_case_with_max_distance(tmp_path: Path):
    tracker = ROITrackingService()
    repo = Mock()

    rois0 = [ROI(id=0, left=0, top=0, width=2, height=2)]
    rois1 = [ROI(id=10, left=100, top=0, width=2, height=2)]
    names0 = ['a']
    names1 = ['b']
    bytes_map1 = {'b': b'Z'}
    repo.load_rois.side_effect = [ (rois0, names0, {}), (rois1, names1, bytes_map1) ]

    out = tmp_path / 'o.zip'
    use_case = TrackROIsUseCase(tracker, repo)
    result = use_case.execute(Path('t0.zip'), Path('t1.zip'), out, max_distance=10.0)
    assert result.matched_count == 0
    repo.save_reordered.assert_called()
