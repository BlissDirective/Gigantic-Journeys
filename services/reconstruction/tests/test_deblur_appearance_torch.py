"""Items 4+5 torch maths (skipped without torch): trajectory vs exposure_trajectory,
zero-init identity, lazy-stepped appearance learning, deblur gradients."""

from __future__ import annotations

import math

import pytest
from reconstruction import deblur_appearance_torch as da
from reconstruction import exposure_trajectory as et
from reconstruction.appearance import AppearanceModel

torch = pytest.importorskip("torch")


def _quat_to_mat(q):
    w, x, y, z = q
    return [
        [1 - 2 * (y * y + z * z), 2 * (x * y - w * z), 2 * (x * z + w * y)],
        [2 * (x * y + w * z), 1 - 2 * (x * x + z * z), 2 * (y * z - w * x)],
        [2 * (x * z - w * y), 2 * (y * z + w * x), 1 - 2 * (x * x + y * y)],
    ]


def test_so3_exp_matches_axis_angle():
    axis, ang = (0.0, 0.0, 1.0), 0.3
    r = da.so3_exp(torch.tensor([0.0, 0.0, ang], dtype=torch.float64))
    q = (math.cos(ang / 2), *(a * math.sin(ang / 2) for a in axis))
    assert torch.allclose(r, torch.tensor(_quat_to_mat(q), dtype=torch.float64), atol=1e-12)
    assert torch.allclose(da.so3_exp(torch.zeros(3)), torch.eye(3))


def test_trajectory_matches_exposure_trajectory_sample_linear():
    """Identity base pose, pure rotations about z + translations: the Lie-linear trajectory
    equals slerp/lerp (exposure_trajectory.sample_linear) exactly for a shared axis."""
    ang_s, ang_e = -0.02, 0.04
    ds = torch.tensor([0, 0, ang_s, 0.01, 0, 0], dtype=torch.float64)
    de = torch.tensor([0, 0, ang_e, -0.02, 0.03, 0], dtype=torch.float64)
    c2w = torch.cat([torch.eye(3, dtype=torch.float64), torch.zeros(3, 1, dtype=torch.float64)], 1)
    got = da.apply_delta(c2w[None].expand(5, 3, 4), da.trajectory_deltas(ds, de, 5))

    def pose(a, t):
        return ((math.cos(a / 2), 0.0, 0.0, math.sin(a / 2)), t)

    ref = et.sample_linear(pose(ang_s, (0.01, 0, 0)), pose(ang_e, (-0.02, 0.03, 0)), 5)
    for k, (q, t) in enumerate(ref):
        assert torch.allclose(
            got[k, :, :3], torch.tensor(_quat_to_mat(q), dtype=torch.float64), atol=1e-6
        )
        assert torch.allclose(got[k, :, 3], torch.tensor(t, dtype=torch.float64), atol=1e-6)
    assert len(et.exposure_weights(5)) == 5  # uniform averaging == torch mean(0)


def test_zero_init_is_sharp_and_canonical():
    st = da.TrainState(4, "cpu", deblur_samples=5, appearance=True)
    c2w = torch.rand(3, 4)
    assert torch.allclose(st.sub_poses(c2w, 2), c2w[None].expand(5, 3, 4), atol=1e-6)
    rgb = torch.rand(8, 8, 3)
    assert torch.allclose(st.apply_color(rgb, 1), rgb)
    canon = AppearanceModel().apply(None, (0.2, 0.5, 0.7))
    assert canon == (0.2, 0.5, 0.7)
    assert float(st.reg_loss(0)) == 0.0


def test_lazy_step_learns_exposure_gain():
    """A view rendered 30% too dark is absorbed by its appearance transform."""
    torch.manual_seed(0)
    st = da.TrainState(2, "cpu", deblur_samples=1, appearance=True)
    rgb = torch.rand(16, 16, 3) * 0.7
    target = rgb * 0.7
    for _ in range(1500):
        st.step_pending()
        loss = ((st.apply_color(rgb, 0) - target) ** 2).mean()
        loss.backward()
    st.step_pending()
    assert float(((st.apply_color(rgb, 0) - target) ** 2).mean()) < 1e-4
    assert st.steps > 0


def test_deblur_gradient_reaches_trajectory():
    st = da.TrainState(1, "cpu", deblur_samples=3, appearance=False)
    poses = st.sub_poses(torch.cat([torch.eye(3), torch.zeros(3, 1)], 1), 0)
    poses[:, :, 3].sum().backward()
    assert st.delta.grad is not None and st.delta.grad.abs().sum() > 0


def test_with_pose_leaves_original():
    class Cam:
        def __init__(self):
            self.camera_to_worlds = torch.zeros(1, 3, 4)
            self.fx = 1.0

    c = Cam()
    d = da.with_pose(c, torch.ones(1, 3, 4))
    assert float(c.camera_to_worlds.sum()) == 0 and float(d.camera_to_worlds.sum()) == 12
    assert d.fx == 1.0
