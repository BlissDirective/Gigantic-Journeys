"""weak_regions helpers on synthetic data (box tool; skipped without numpy)."""

import pytest

np = pytest.importorskip("numpy")

from tools import weak_regions as wr  # noqa: E402


def test_isolated_mask_flags_lone_splats_only():
    rng = np.random.default_rng(0)
    cluster = rng.normal(0.0, 0.02, size=(200, 3))
    lone = np.array([[5.0, 5.0, 5.0], [-4.0, 1.0, 2.0]])
    mask = wr.isolated_mask(np.vstack([cluster, lone]))
    assert not mask[:200].any()
    assert mask[200:].all()


def test_room_to_colmap_inverts_the_room_placement():
    from tools import room_limits as rl

    room = {"position": [0.3, 1.8, 2.7], "rotation": [0.58, 0.21, 0.02, 0.78], "scale": [2, 2, -2]}
    n = np.linalg.norm(room["rotation"])
    room["rotation"] = [q / n for q in room["rotation"]]
    world = np.eye(4)
    world[:3, 3] = [0.1, -0.2, 0.3]
    scale = 0.5
    raw = np.array([[1.0, 2.0, 3.0], [-1.0, 0.5, 0.0]])
    ply = (world @ np.c_[raw, np.ones(2)].T).T[:, :3] * scale
    room_pts = rl.to_room(ply, room)
    assert np.allclose(wr.room_to_colmap(room_pts, room, world, scale), raw)
