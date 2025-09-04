from percell.domain.value_objects.imaging import ImageDimensions, Resolution


def test_image_dimensions_defaults():
    dims = ImageDimensions(width=640, height=480)
    assert dims.width == 640
    assert dims.height == 480
    assert dims.channels == 1


def test_resolution_defaults():
    res = Resolution(x=0.25, y=0.25)
    assert res.x == 0.25
    assert res.units == 'pixel'
