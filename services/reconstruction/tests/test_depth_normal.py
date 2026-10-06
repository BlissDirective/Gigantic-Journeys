"""DN-Splatter depth/normal regularisation references."""

import pytest
from reconstruction.depth_normal import (
    edge_aware_log_l1,
    normal_consistency,
    normal_tv,
    pearson_depth_loss,
)

FLAT_IMG = [[0.5, 0.5, 0.5], [0.5, 0.5, 0.5], [0.5, 0.5, 0.5]]


def test_log_l1_zero_when_pred_equals_gt():
    d = [[1.0, 2.0, 3.0], [1.5, 2.5, 3.5], [2.0, 3.0, 4.0]]
    assert edge_aware_log_l1(d, d, FLAT_IMG) == pytest.approx(0.0)


def test_log_l1_positive_and_edge_downweighted():
    gt = [[1.0, 1.0, 1.0], [1.0, 1.0, 1.0], [1.0, 1.0, 1.0]]
    pred = [[1.5, 1.5, 1.5], [1.5, 1.5, 1.5], [1.5, 1.5, 1.5]]  # constant error everywhere
    flat = edge_aware_log_l1(pred, gt, FLAT_IMG)
    edged = edge_aware_log_l1(pred, gt, [[0.0, 1.0, 0.0], [1.0, 0.0, 1.0], [0.0, 1.0, 0.0]])
    assert flat > 0.0
    assert edged < flat  # image edges down-weight the depth loss


def test_log_l1_skips_nonpositive_gt():
    gt = [[0.0, 0.0], [0.0, 0.0]]  # no valid pixels
    pred = [[1.0, 1.0], [1.0, 1.0]]
    assert edge_aware_log_l1(pred, gt, [[0.5, 0.5], [0.5, 0.5]]) == 0.0


def test_pearson_is_scale_invariant():
    gt = [[1.0, 2.0, 3.0], [4.0, 5.0, 6.0]]
    pred = [[2.0 * v + 1.0 for v in row] for row in gt]  # perfectly correlated, different scale
    assert pearson_depth_loss(pred, gt) == pytest.approx(0.0, abs=1e-9)
    anti = [[-2.0 * v for v in row] for row in gt]
    assert pearson_depth_loss(anti, gt) == pytest.approx(2.0, abs=1e-9)


def test_normal_consistency_and_tv():
    up = [[(0.0, 1.0, 0.0), (0.0, 1.0, 0.0)], [(0.0, 1.0, 0.0), (0.0, 1.0, 0.0)]]
    assert normal_consistency(up, up) == pytest.approx(0.0)
    down = [[(0.0, -1.0, 0.0)] * 2] * 2
    assert normal_consistency(up, down) == pytest.approx(2.0)
    assert normal_tv(up) == pytest.approx(0.0)  # constant field -> smooth
    mixed = [[(0.0, 1.0, 0.0), (1.0, 0.0, 0.0)], [(0.0, 1.0, 0.0), (0.0, 1.0, 0.0)]]
    assert normal_tv(mixed) > 0.0


def test_dim_mismatch_raises():
    with pytest.raises(ValueError, match="dimensions"):
        edge_aware_log_l1([[1.0]], [[1.0, 2.0]], [[0.5]])
