"""Bedroom cleanup stage 1 (coverage map) + stage 3 prep (planar proxies) on a synthetic
COLMAP text model: a 4 x 3 x 2.5 room (floor, ceiling, 2 walls) seen by a ring of cameras."""

from __future__ import annotations

import json
import math

import pytest

np = pytest.importorskip("numpy")
pytest.importorskip("PIL")

from reconstruction import coverage_map as cm  # noqa: E402
from reconstruction import planar_proxies as pp  # noqa: E402


def _look_at_quat(c, target, up=(0.0, 1.0, 0.0)):
    """World->camera quaternion (OpenCV: +z forward, +y down) for a camera at c."""
    z = np.asarray(target, float) - c
    z /= np.linalg.norm(z)
    x = np.cross(z, -np.asarray(up))
    x /= np.linalg.norm(x)
    y = np.cross(z, x)
    r = np.stack([x, y, z])  # rows = camera axes in world -> world->camera rotation
    return _mat_to_quat(r), r


def _mat_to_quat(m):
    """Shepperd's method (robust for any rotation)."""
    t = np.trace(m)
    if t > 0:
        s = 2 * math.sqrt(t + 1)
        return (s / 4, (m[2, 1] - m[1, 2]) / s, (m[0, 2] - m[2, 0]) / s, (m[1, 0] - m[0, 1]) / s)
    i = int(np.argmax(np.diag(m)))
    j, k = (i + 1) % 3, (i + 2) % 3
    s = 2 * math.sqrt(1 + m[i, i] - m[j, j] - m[k, k])
    q = [0.0, 0.0, 0.0, 0.0]
    q[0] = (m[k, j] - m[j, k]) / s
    q[1 + i] = s / 4
    q[1 + j] = (m[j, i] + m[i, j]) / s
    q[1 + k] = (m[k, i] + m[i, k]) / s
    return tuple(q)


def _model(tmp_path, n_cams=24, seen_by_few=False):
    rng = np.random.default_rng(1)
    d = tmp_path / "sparse"
    d.mkdir()
    (d / "cameras.txt").write_text("1 PINHOLE 640 480 500 500 320 240\n")
    cams, lines = [], []
    for i in range(n_cams):
        a = 2 * math.pi * i / n_cams
        c = np.array([2 + 0.6 * math.cos(a), 1.4, 1.5 + 0.6 * math.sin(a)])
        tgt = np.array([2 + 3 * math.cos(a), 1.0, 1.5 + 3 * math.sin(a)])
        q, r = _look_at_quat(c, tgt)
        t = -r @ c
        cams.append(c)
        lines.append(f"{i + 1} {' '.join(map(str, q))} {' '.join(map(str, t))} 1 f{i:03d}.jpg\n\n")
    (d / "images.txt").write_text("".join(lines))
    pts = []
    for _ in range(1500):  # floor y=0, ceiling y=2.5, wall x=0, wall z=3
        pts.append((rng.uniform(0, 4), 0.0, rng.uniform(0, 3)))
        pts.append((rng.uniform(0, 4), 2.5, rng.uniform(0, 3)))
        pts.append((0.0, rng.uniform(0, 2.5), rng.uniform(0, 3)))
        pts.append((rng.uniform(0, 4), rng.uniform(0, 2.5), 3.0))
    out = []
    for k, p in enumerate(pts):
        if seen_by_few and p[0] == 0.0 and p[2] < 1.0:
            track = [1, 2]  # a corner only two frames saw
        else:
            track = sorted(rng.choice(n_cams, 8, replace=False) + 1)
        tr = " ".join(f"{i} 0" for i in track)
        out.append(f"{k + 1} {p[0]} {p[1]} {p[2]} 128 128 128 0.5 {tr}\n")
    (d / "points3D.txt").write_text("".join(out))
    return d


def test_coverage_finds_weak_corner_and_up(tmp_path):
    d = _model(tmp_path, seen_by_few=True)
    cov = cm.build_coverage(d, None, grid=20, min_spread_deg=0.0)
    assert np.allclose(cov.up, [0, -1, 0], atol=0.2) or np.allclose(cov.up, [0, 1, 0], atol=0.2)
    s = cov.summary()
    assert s["weak_voxels"] > 0 and s["weak_regions"]
    top = s["weak_regions"][0]
    assert top["centroid"][0] < 0.5 and top["centroid"][2] < 1.2 and "views" in top["why"]
    assert s["camera_bounds"]["min"] and s["camera_bounds"]["max"]
    json.dumps(s)
    png = cm.heatmap_png(cov, tmp_path / "h.png")
    assert png.stat().st_size > 0


def test_coverage_full_when_well_seen(tmp_path):
    cov = cm.build_coverage(_model(tmp_path), None, grid=20, min_spread_deg=0.0)
    assert cov.summary()["weak_voxels"] == 0


def test_planes_floor_ceiling_walls(tmp_path):
    planes = pp.detect_planes(_model(tmp_path), max_walls=4, iters=400)
    labels = sorted(p.label for p in planes)
    assert labels.count("wall") == 2 and "floor" in labels and "ceiling" in labels
    cams = np.array([2.0, 1.4, 1.5])
    for p in planes:
        n = np.asarray(p.normal)
        assert n @ cams + p.offset > 0  # faces the room
        assert len(p.corners) == 4


def test_perspective_coeffs_roundtrip():
    dst = [(0, 10), (10, 10), (10, 0), (0, 0)]
    src = [(5, 25), (40, 30), (35, 2), (3, 4)]
    c = pp.perspective_coeffs(dst, src)
    for (x, y), (u, v) in zip(dst, src, strict=True):
        den = c[6] * x + c[7] * y + 1
        assert abs((c[0] * x + c[1] * y + c[2]) / den - u) < 1e-9
        assert abs((c[3] * x + c[4] * y + c[5]) / den - v) < 1e-9
