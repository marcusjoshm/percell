import numpy as np
import pytest
from percell.domain.services.roi_tracking_service import ROITrackingService, ROI


def test_polygon_centroid_closed_and_open():
    service = ROITrackingService()
    # triangle (closed)
    tri_x = [0.0, 2.0, 0.0, 0.0]
    tri_y = [0.0, 0.0, 2.0, 0.0]
    cx, cy = service._polygon_centroid(tri_x, tri_y)
    # centroid of right triangle with vertices (0,0),(2,0),(0,2) is (2/3, 2/3)
    assert cx == pytest.approx(2.0 / 3.0)
    assert cy == pytest.approx(2.0 / 3.0)

    # same triangle but open; service should auto-close
    tri_x_open = [0.0, 2.0, 0.0]
    tri_y_open = [0.0, 0.0, 2.0]
    roi = ROI(id=1, x=tri_x_open, y=tri_y_open)
    cx2, cy2 = service._get_centroid(roi)
    assert cx2 == pytest.approx(cx)
    assert cy2 == pytest.approx(cy)


def test_rectangle_centroid_variants():
    service = ROITrackingService()
    # width/height variant
    roi_wh = ROI(id=2, left=10, top=20, width=6, height=4)
    cx, cy = service._get_centroid(roi_wh)
    assert cx == 13.0
    assert cy == 22.0

    # left/top/right/bottom variant
    roi_ltrb = ROI(id=3, left=10, top=20, right=16, bottom=24)
    cx2, cy2 = service._get_centroid(roi_ltrb)
    assert cx2 == 13.0
    assert cy2 == 22.0


def test_match_rois_without_threshold():
    service = ROITrackingService()
    # two points near (0,0) and (10,0)
    src = [ROI(id=1, left=0, top=0, width=2, height=2), ROI(id=2, left=9, top=0, width=2, height=2)]
    tgt = [ROI(id=10, left=10, top=0, width=2, height=2), ROI(id=11, left=0, top=0, width=2, height=2)]
    matches = service.match_rois(src, tgt)
    assert matches == {1: 11, 2: 10}


def test_match_rois_with_max_distance_filters():
    service = ROITrackingService()
    src = [ROI(id=1, left=0, top=0, width=2, height=2)]
    tgt = [ROI(id=10, left=100, top=0, width=2, height=2)]
    matches = service.match_rois(src, tgt, max_distance=10.0)
    assert matches == {}
