"""BAD-Gaussians in-exposure camera trajectory sampling."""

import math

import pytest
from reconstruction.exposure_trajectory import (
    exposure_weights,
    normalize_quat,
    sample_cubic_bspline,
    sample_linear,
    slerp,
)

IDENT = (1.0, 0.0, 0.0, 0.0)


def _unit(q):
    return math.sqrt(sum(c * c for c in q)) == pytest.approx(1.0, abs=1e-9)


def test_normalize_handles_zero():
    assert normalize_quat((0.0, 0.0, 0.0, 0.0)) == IDENT


def test_slerp_endpoints_and_unit():
    q1 = normalize_quat((math.cos(0.4), 0.0, math.sin(0.4), 0.0))
    assert slerp(IDENT, q1, 0.0) == pytest.approx(IDENT)
    assert slerp(IDENT, q1, 1.0) == pytest.approx(q1)
    assert _unit(slerp(IDENT, q1, 0.3))


def test_linear_endpoints_and_midpoint():
    start = (IDENT, (0.0, 0.0, 0.0))
    end = (IDENT, (2.0, 0.0, 0.0))
    poses = sample_linear(start, end, 3)
    assert len(poses) == 3
    assert poses[0][1] == pytest.approx((0.0, 0.0, 0.0))
    assert poses[1][1] == pytest.approx((1.0, 0.0, 0.0))  # midpoint translation
    assert poses[2][1] == pytest.approx((2.0, 0.0, 0.0))


def test_linear_single_sample_is_mid_exposure():
    start = (IDENT, (0.0, 0.0, 0.0))
    end = (IDENT, (4.0, 0.0, 0.0))
    (pose,) = sample_linear(start, end, 1)
    assert pose[1] == pytest.approx((2.0, 0.0, 0.0))


def test_cubic_bspline_shape_unit_and_deterministic():
    controls = [
        (IDENT, (0.0, 0.0, 0.0)),
        (IDENT, (1.0, 0.0, 0.0)),
        (IDENT, (2.0, 0.5, 0.0)),
        (IDENT, (3.0, 0.5, 0.0)),
    ]
    poses = sample_cubic_bspline(controls, 5)
    assert len(poses) == 5
    assert all(_unit(p[0]) for p in poses)
    assert poses == sample_cubic_bspline(controls, 5)  # deterministic
    with pytest.raises(ValueError, match="4 control"):
        sample_cubic_bspline(controls[:3], 5)


def test_exposure_weights_sum_to_one():
    w = exposure_weights(4)
    assert len(w) == 4 and sum(w) == pytest.approx(1.0)
