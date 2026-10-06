"""Parity: the torch DN-Splatter / mono-prior mirror equals the stdlib Brain-B contract.

Skipped where torch is absent (CI installs nothing for this service); run on the box /
in the CUDA image. The stdlib reference (depth_normal.py, depth_prior.py) is the contract.
"""

import math
import random

import pytest

torch = pytest.importorskip("torch")

from reconstruction import depth_normal as ref  # noqa: E402
from reconstruction import depth_prior as ref_prior  # noqa: E402
from reconstruction import dn_torch as dt  # noqa: E402


def _grid(h, w, lo=0.5, hi=3.0, seed=1, zero_frac=0.1):
    rng = random.Random(seed)
    return [
        [0.0 if rng.random() < zero_frac else rng.uniform(lo, hi) for _ in range(w)]
        for _ in range(h)
    ]


def _normals(h, w, seed=3):
    rng = random.Random(seed)
    return [
        [(rng.uniform(-1, 1), rng.uniform(-1, 1), rng.uniform(-1, 1)) for _ in range(w)]
        for _ in range(h)
    ]


def _mask(h, w, seed=5):
    rng = random.Random(seed)
    return [[rng.random() > 0.2 for _ in range(w)] for _ in range(h)]


T = lambda g: torch.tensor(g, dtype=torch.float64)  # noqa: E731
B = lambda g: torch.tensor(g, dtype=torch.bool)  # noqa: E731


@pytest.mark.parametrize("masked", [False, True])
def test_edge_aware_log_l1_parity(masked):
    pred, gt, img = _grid(9, 7, seed=1), _grid(9, 7, seed=2), _grid(9, 7, 0, 1, seed=3, zero_frac=0)
    m = _mask(9, 7) if masked else None
    want = ref.edge_aware_log_l1(pred, gt, img, m, edge_weight=2.0)
    got = dt.edge_aware_log_l1(T(pred), T(gt), T(img), B(m) if m else None, edge_weight=2.0)
    assert float(got) == pytest.approx(want, rel=1e-9, abs=1e-12)


@pytest.mark.parametrize("masked", [False, True])
def test_pearson_parity_and_scale_invariance(masked):
    pred, gt = _grid(8, 8, seed=4), _grid(8, 8, seed=5)
    m = _mask(8, 8) if masked else None
    want = ref.pearson_depth_loss(pred, gt, m)
    got = dt.pearson_depth_loss(T(pred), T(gt), B(m) if m else None)
    assert float(got) == pytest.approx(want, rel=1e-9, abs=1e-12)
    scaled = dt.pearson_depth_loss(3.0 * T(pred) + 1.0, T(gt), B(m) if m else None)
    assert float(scaled) == pytest.approx(float(got), abs=1e-9)


@pytest.mark.parametrize("masked", [False, True])
def test_normal_losses_parity(masked):
    a, b = _normals(6, 5, seed=7), _normals(6, 5, seed=8)
    m = _mask(6, 5) if masked else None
    assert float(dt.normal_consistency(T(a), T(b), B(m) if m else None)) == pytest.approx(
        ref.normal_consistency(a, b, m), rel=1e-9
    )
    assert float(dt.normal_tv(T(a), B(m) if m else None)) == pytest.approx(
        ref.normal_tv(a, m), rel=1e-9
    )


def test_degenerate_inputs_return_zero_like_the_reference():
    z = [[0.0, 0.0], [0.0, 0.0]]
    one = [[1.0, 1.0], [1.0, 1.0]]
    assert float(dt.pearson_depth_loss(T(one), T(z))) == ref.pearson_depth_loss(one, z) == 0.0
    assert (
        float(dt.edge_aware_log_l1(T(one), T(z), T(one)))
        == ref.edge_aware_log_l1(one, z, one)
        == 0.0
    )
    loss = dt.pearson_depth_loss(T(one).requires_grad_(), T(one))
    loss.backward()  # zero losses stay differentiable


def test_align_scale_shift_parity():
    rel, metric = _grid(5, 6, seed=9, zero_frac=0), _grid(5, 6, seed=10)
    s, b = ref_prior.align_scale_shift(rel, metric)
    ts, tb = dt.align_scale_shift(T(rel), T(metric))
    assert (float(ts), float(tb)) == pytest.approx((s, b), rel=1e-9)
    got = dt.to_metric(T(rel), T(metric))
    want = ref_prior.to_metric(rel, metric)
    assert got.flatten().tolist() == pytest.approx([v for r in want for v in r], rel=1e-9)


def test_losses_are_differentiable_through_rendered_depth():
    pred = T(_grid(6, 6, seed=11, zero_frac=0)).requires_grad_()
    gt, img = T(_grid(6, 6, seed=12)), T(_grid(6, 6, 0, 1, seed=13, zero_frac=0))
    (dt.edge_aware_log_l1(pred, gt, img) + dt.pearson_depth_loss(pred, gt)).backward()
    assert pred.grad is not None and torch.isfinite(pred.grad).all()


def test_normals_from_depth_of_a_tilted_plane():
    # Plane z = 2 + 0.5 * x_cam  (metres) seen by a pinhole camera.
    h, w, f, cx, cy = 16, 20, 20.0, 10.0, 8.0
    depth = torch.empty(h, w, dtype=torch.float64)
    for i in range(h):
        for j in range(w):
            u = (j - cx) / f
            depth[i, j] = 2.0 / (1.0 - 0.5 * u)  # z = 2 + 0.5 * (u * z)
    n = dt.normals_from_depth(depth, f, f, cx, cy)
    expect = torch.tensor([0.5, 0.0, -1.0], dtype=torch.float64) / math.sqrt(1.25)
    centre = n[2:-2, 2:-2].reshape(-1, 3)
    assert torch.allclose(centre, expect.expand_as(centre), atol=1e-6)
    assert float(dt.normal_tv(n[2:-2, 2:-2])) == pytest.approx(0.0, abs=1e-6)
