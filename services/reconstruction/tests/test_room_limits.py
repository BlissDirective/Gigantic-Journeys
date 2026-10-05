"""room_limits: pure helpers (rectangle search, yaw maths) and the nerfstudio frame on a toy rig."""

from __future__ import annotations

import argparse
import math

import pytest
from tools import room_limits as rl


def test_largest_rectangle_finds_the_biggest_all_true_block():
    mask = [
        [0, 1, 1, 0],
        [1, 1, 1, 0],
        [1, 1, 1, 1],
        [0, 1, 0, 1],
    ]
    grid = [[bool(v) for v in r] for r in mask]
    r0, r1, c0, c1 = rl.largest_rectangle(grid)
    assert (r1 - r0 + 1) * (c1 - c0 + 1) == 6
    assert all(grid[r][c] for r in range(r0, r1 + 1) for c in range(c0, c1 + 1))
    assert rl.largest_rectangle([[False, False]]) is None


def test_yaw_helpers_wrap():
    assert rl.wrap_deg(190.0) == pytest.approx(-170.0)
    assert rl.circular_mean_deg([170.0, -170.0]) == pytest.approx(180.0, abs=1e-6) or (
        rl.circular_mean_deg([170.0, -170.0]) == pytest.approx(-180.0, abs=1e-6)
    )
    assert rl.circular_mean_deg([10.0, -10.0]) == pytest.approx(0.0, abs=1e-9)


def test_nerfstudio_frame_centres_and_scales_the_cameras():
    np = pytest.importorskip("numpy")
    # Four identity-rotation cameras on a square (COLMAP world), looking down +z (OpenCV).
    images = []
    for i, (x, y) in enumerate([(0, 0), (2, 0), (0, 2), (2, 2)]):
        # w2c translation t = -R c with R = I
        images.append((i + 1, [1.0, 0.0, 0.0, 0.0], [-x, -y, -5.0], f"{i}.jpg"))
    centres, forwards, world, scale = rl.nerfstudio_cameras(images)
    assert centres.shape == (4, 3)
    assert np.allclose(centres.mean(0), 0.0, atol=1e-9), "centred on the poses"
    assert np.abs(centres).max() == pytest.approx(1.0), "auto-scaled to the unit cube"
    assert np.allclose(np.linalg.norm(forwards, axis=1), 1.0)
    # A raw point maps with the same transform the dataparser applies to points3D.
    p = (world @ np.array([1.0, 1.0, 5.0, 1.0]))[:3] * scale
    assert np.allclose(p, 0.0, atol=1e-9), "the cameras' centroid maps to the origin"


def test_views_of_counts_only_cameras_facing_the_point():
    np = pytest.importorskip("numpy")
    centres = np.array([[0.0, 1.0, 0.0], [0.0, 1.0, 0.0]])
    forwards = np.array([[0.0, 0.0, 1.0], [0.0, 0.0, -1.0]])
    t = math.tan(math.radians(30))
    assert rl.views_of(np.array([0.0, 1.0, 3.0]), centres, forwards, t, t, 10.0) == 1
    assert rl.views_of(np.array([0.0, 1.0, 30.0]), centres, forwards, t, t, 10.0) == 0


def test_blocked_cells_marks_furniture_in_the_height_band():
    np = pytest.importorskip("numpy")
    xs = np.arange(0.0, 1.01, 0.25)
    zs = np.arange(0.0, 0.51, 0.25)
    bed = [[0.5, 0.4, 0.25]] * 50  # 50 splats 0.4 m up over cell (z 0.25, x 0.5)
    rug = [[0.0, 0.02, 0.0]] * 80  # floor splats never block
    lamp = [[1.0, 1.6, 0.5]] * 80  # above the band
    few = [[0.25, 0.5, 0.5]] * 10  # too sparse
    grid = rl.blocked_cells(bed + rug + lamp + few, xs, zs, 0.25, 0.12, 1.2, 40)
    assert grid.shape == (3, 5)
    assert grid.sum() == 1 and grid[1, 2]


def test_floor_around_a_bed_becomes_walk_bounds_plus_blockers():
    np = pytest.importorskip("numpy")
    # 10 x 12 floor (rows = z), a 4 x 5 bed with 3-cell aisles, a 1-cell leak past the wall
    free = np.zeros((12, 16), dtype=bool)
    free[1:11, 1:13] = True
    free[4:8, 4:9] = False  # bed
    free[5, 13:16] = True  # thin leak past the wall: opened away
    comp = rl.connected_from(rl.opened(free), (1, 1))
    rows, cols = np.flatnonzero(comp.any(1)), np.flatnonzero(comp.any(0))
    assert (rows[0], rows[-1], cols[0], cols[-1]) == (1, 10, 1, 12)
    sub = ~comp[1:11, 1:13]
    args = argparse.Namespace(obstacle_high=1.2, blocker_min_cells=3, max_blockers=12)
    xs = np.arange(1, 13) * 0.1
    zs = np.arange(1, 11) * 0.1
    boxes = rl.blocker_boxes(sub, xs, zs, 0.1, args)
    assert len(boxes) == 1
    b = boxes[0]
    assert b["size"] == [0.5, 1.2, 0.4]
    assert b["center"] == [0.6, 0.6, 0.55]
