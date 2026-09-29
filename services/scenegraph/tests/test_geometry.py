"""M1-SCEN-02 vector-math helpers."""

import math

from scenegraph import geometry as g


def test_cross_and_normal_of_ccw_triangle_points_up():
    v0, v1, v2 = (0.0, 0.0, 0.0), (1.0, 0.0, 0.0), (0.0, 0.0, -1.0)
    n = g.tri_normal(v0, v1, v2)
    assert n == (0.0, 1.0, 0.0)


def test_tri_area_and_centroid():
    v0, v1, v2 = (0.0, 0.0, 0.0), (2.0, 0.0, 0.0), (0.0, 0.0, 2.0)
    assert math.isclose(g.tri_area(v0, v1, v2), 2.0)
    assert g.tri_centroid(v0, v1, v2) == (2.0 / 3.0, 0.0, 2.0 / 3.0)


def test_normalize_zero_is_zero():
    assert g.normalize((0.0, 0.0, 0.0)) == (0.0, 0.0, 0.0)


def test_slope_deg_flat_vertical_and_45():
    assert math.isclose(g.slope_deg((0.0, 1.0, 0.0)), 0.0, abs_tol=1e-9)
    assert math.isclose(g.slope_deg((0.0, -1.0, 0.0)), 0.0, abs_tol=1e-9)  # facing down, still flat
    assert math.isclose(g.slope_deg((1.0, 0.0, 0.0)), 90.0, abs_tol=1e-9)
    assert math.isclose(g.slope_deg(g.normalize((1.0, 1.0, 0.0))), 45.0, abs_tol=1e-9)


def test_angle_deg_orthogonal_and_parallel():
    assert math.isclose(g.angle_deg((1.0, 0.0, 0.0), (0.0, 1.0, 0.0)), 90.0)
    assert math.isclose(g.angle_deg((1.0, 0.0, 0.0), (2.0, 0.0, 0.0)), 0.0)
