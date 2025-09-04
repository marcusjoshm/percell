import pytest

from percell.domain.services.roi_tracking_service import ROITrackingService, ROI


def test_polygon_centroid_degenerate_to_mean():
    service = ROITrackingService()
    # Nearly colinear polygon (area ~ 0) should fallback to mean of vertices
    x = [0.0, 1.0, 2.0, 0.0]
    y = [0.0, 0.0, 0.0, 0.0]
    cx, cy = service._polygon_centroid(x, y)
    assert cx == pytest.approx((0.0 + 1.0 + 2.0) / 3.0)
    assert cy == pytest.approx(0.0)


def test_get_centroid_invalid_polygon_raises():
    service = ROITrackingService()
    with pytest.raises(ValueError):
        service._get_centroid(ROI(id=1, x=[0.0], y=[]))


def test_match_rois_empty_lists():
    service = ROITrackingService()
    assert service.match_rois([], []) == {}


