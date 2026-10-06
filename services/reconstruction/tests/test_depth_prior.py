"""Monocular depth prior scale/shift alignment to ARKit metric depth."""

import pytest
from reconstruction.depth_prior import (
    MockDepthPrior,
    align_scale_shift,
    apply_scale_shift,
    to_metric,
)


def test_align_recovers_known_scale_and_shift():
    rel = [[1.0, 2.0, 3.0], [4.0, 5.0, 6.0]]
    metric = [[2.0 * v + 3.0 for v in row] for row in rel]  # metric = 2*rel + 3
    scale, shift = align_scale_shift(rel, metric)
    assert scale == pytest.approx(2.0, abs=1e-9)
    assert shift == pytest.approx(3.0, abs=1e-9)


def test_apply_and_to_metric():
    rel = [[1.0, 2.0], [3.0, 4.0]]
    assert apply_scale_shift(rel, 2.0, 1.0) == [[3.0, 5.0], [7.0, 9.0]]
    metric = [[2.0 * v + 1.0 for v in row] for row in rel]
    got = to_metric(rel, metric)
    assert [v for row in got for v in row] == pytest.approx([v for row in metric for v in row])


def test_mask_and_nonpositive_metric_are_skipped():
    rel = [[1.0, 2.0, 3.0]]
    metric = [[5.0, 0.0, 7.0]]  # middle pixel invalid (0 depth)
    # Only pixels 0 and 2 fit: metric = 1*rel + 4  -> scale 1, shift 4
    scale, shift = align_scale_shift(rel, metric)
    assert scale == pytest.approx(1.0) and shift == pytest.approx(4.0)


def test_insufficient_or_degenerate_raises():
    with pytest.raises(ValueError, match="2 valid"):
        align_scale_shift([[1.0]], [[2.0]])
    with pytest.raises(ValueError, match="variance"):
        align_scale_shift([[2.0, 2.0]], [[1.0, 3.0]])  # relative has no variance


def test_mock_prior_shape():
    img = [[0.0, 0.0, 0.0], [0.0, 0.0, 0.0]]
    out = MockDepthPrior().predict(img)
    assert len(out) == 2 and len(out[0]) == 3
