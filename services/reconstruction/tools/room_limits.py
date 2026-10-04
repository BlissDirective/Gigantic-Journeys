"""Derive a splat room's play-area and camera limits from its training camera poses.

Box/operator tool (needs numpy; CI tests skip without it). The splat only looks right
from where the source video looked, so the room's walkable area, camera bounds and orbit
limits should stay where the training cameras were and what they saw (M1-UNITY-01, build
50 feedback: smears and blobs wherever the player looked beyond the capture).

    python -m tools.room_limits <colmap sparse dir> <splat-room.json> [--eye-height 1.5]

Steps:

1. Read the COLMAP model the splat was trained from and put each camera into the splat
   PLY's frame exactly like nerfstudio 1.1.5's colmap dataparser does (COLMAP->OpenGL axes,
   the world swap, "up" orientation, centring on the poses, auto scale). The splat PLY is
   exported in that frame, so the room placement (position / rotation / scale) of the JSON
   maps the cameras into the Unity room.
2. Rescale the room so the median training camera height is ``--eye-height`` metres above the
   floor (y = 0): a handheld walk-through is filmed at about eye height, so the character and
   the follow camera then see the room from the heights it was captured at.
3. Floor coverage: on a grid, count the training cameras whose frustum (within ``--max-view``
   metres) contains the point at knee and head height; ``--min-views`` makes a cell "covered".
   The walkable rectangle is the largest all-covered axis-aligned rectangle, inset by
   ``--inset``.
4. Camera limits: the orbit's highest elevation is the training cameras' 95th-percentile
   downward look plus 5 degrees (they rarely looked down, so the floor is only seen at grazing
   angles); the allowed view yaw is the cameras' circular mean heading +- their 90th-percentile
   deviation (both over the cameras that see the walk area); the camera box is the walk
   rectangle grown by ``--camera-margin`` and capped at the
   95th-percentile camera height + 0.5 m.
5. Occluders: a solid wall just outside the camera box on each side whose next ``--band``
   metres are thinly covered (< half of ``--min-views``), so the camera never looks into the
   unreconstructed side; never on the side the cameras faced (within 45 degrees of the mean
   heading), which they filmed from further away.

Prints a JSON proposal with the fields of ``SplatRoomDescriptor`` it would change, plus stats.
"""

from __future__ import annotations

import argparse
import json
import math
import struct
import sys
from pathlib import Path


def _np():
    import numpy as np

    return np


def read_images_bin(path: Path) -> list[tuple[int, list[float], list[float], str]]:
    """COLMAP images.bin: (image_id, qvec wxyz, tvec, name), keypoints skipped."""
    out = []
    with path.open("rb") as f:
        (n,) = struct.unpack("<Q", f.read(8))
        for _ in range(n):
            iid, qw, qx, qy, qz, tx, ty, tz, _cid = struct.unpack("<IdddddddI", f.read(64))
            name = bytearray()
            while (c := f.read(1)) != b"\0":
                name += c
            (n2d,) = struct.unpack("<Q", f.read(8))
            f.seek(24 * n2d, 1)
            out.append((iid, [qw, qx, qy, qz], [tx, ty, tz], name.decode()))
    return out


def read_camera_bin(path: Path) -> tuple[int, int, float, float]:
    """First camera of a COLMAP cameras.bin: (width, height, fx, fy)."""
    with path.open("rb") as f:
        (n,) = struct.unpack("<Q", f.read(8))
        if n < 1:
            raise ValueError("no camera in cameras.bin")
        _cid, model, w, h = struct.unpack("<iiQQ", f.read(24))
        p = struct.unpack("<4d", f.read(32))
    fy = p[1] if model in (1, 4, 5, 6, 7, 8, 10) else p[0]  # PINHOLE-family has fx, fy
    return int(w), int(h), float(p[0]), float(fy)


def qvec_to_rot(q):
    np = _np()
    w, x, y, z = q
    return np.array(
        [
            [1 - 2 * (y * y + z * z), 2 * (x * y - w * z), 2 * (x * z + w * y)],
            [2 * (x * y + w * z), 1 - 2 * (x * x + z * z), 2 * (y * z - w * x)],
            [2 * (x * z - w * y), 2 * (y * z + w * x), 1 - 2 * (x * x + y * y)],
        ]
    )


def _rotation_between(a, b):
    np = _np()
    a = a / np.linalg.norm(a)
    b = b / np.linalg.norm(b)
    v = np.cross(a, b)
    if np.abs(v).sum() < 1e-6:
        v = np.cross(a, np.array([1.0, 0, 0]) if abs(a[0]) < 1e-6 else np.array([0, 1.0, 0]))
    v = v / np.linalg.norm(v)
    k = np.array([[0, -v[2], v[1]], [v[2], 0, -v[0]], [-v[1], v[0], 0]])
    t = math.acos(float(np.clip(a @ b, -1, 1)))
    return np.eye(3) + math.sin(t) * k + (1 - math.cos(t)) * (k @ k)


def nerfstudio_cameras(images) -> tuple:
    """Camera centres and forward vectors in nerfstudio's colmap-dataparser frame.

    Returns ``(centres (N,3), forwards (N,3), world_transform (4,4), scale)``; a raw COLMAP
    point ``p`` maps to ``(world_transform @ [p, 1])[:3] * scale``.
    """
    np = _np()
    swap = np.eye(4)[[0, 2, 1, 3], :]
    swap[2, :] *= -1
    poses = []
    for _iid, q, t, _name in sorted(images, key=lambda r: r[0]):
        w2c = np.eye(4)
        w2c[:3, :3] = qvec_to_rot(q)
        w2c[:3, 3] = t
        c2w = np.linalg.inv(w2c)
        c2w[0:3, 1:3] *= -1
        poses.append(swap @ c2w)
    poses = np.array(poses)
    centre = poses[:, :3, 3].mean(0)
    up = poses[:, :3, 1].mean(0)
    rot = _rotation_between(up, np.array([0.0, 0.0, 1.0]))
    orient = np.eye(4)
    orient[:3, :3] = rot
    orient[:3, 3] = rot @ -centre
    oriented = orient @ poses
    scale = 1.0 / float(np.abs(oriented[:, :3, 3]).max())
    return oriented[:, :3, 3] * scale, -oriented[:, :3, 2], orient @ swap, scale


def unity_rot(q_xyzw):
    x, y, z, w = q_xyzw
    return qvec_to_rot([w, x, y, z])


def to_room(points, room: dict, k: float = 1.0):
    """PLY-frame points -> Unity room world (the JSON placement), scaled by ``k`` about 0."""
    np = _np()
    r = unity_rot(room["rotation"])
    s = np.array(room["scale"], dtype=float)
    p = np.array(room["position"], dtype=float)
    return k * ((r @ (np.asarray(points) * s).T).T + p)


def dirs_to_room(dirs, room: dict):
    np = _np()
    r = unity_rot(room["rotation"])
    d = (r @ (np.asarray(dirs) * np.array(room["scale"], dtype=float)).T).T
    return d / np.linalg.norm(d, axis=1, keepdims=True)


def views_of(point, centres, forwards, tan_half_w, tan_half_h, max_view, min_view=0.3) -> int:
    """How many cameras see ``point`` in their frustum, ``min_view``..``max_view`` m away."""
    seen = _seen_mask(point, centres, forwards, tan_half_w, tan_half_h, max_view, min_view)
    return int(seen.sum())


def _seen_mask(point, centres, forwards, tan_half_w, tan_half_h, max_view, min_view=0.3):
    np = _np()
    v = point - centres
    d = np.linalg.norm(v, axis=1)
    v = v / np.maximum(d, 1e-9)[:, None]
    right = np.cross(forwards, np.array([0.0, 1.0, 0.0]))
    right /= np.maximum(np.linalg.norm(right, axis=1, keepdims=True), 1e-9)
    up = np.cross(right, forwards)
    z = (v * forwards).sum(1)
    zs = np.maximum(z, 1e-6)
    x = (v * right).sum(1) / zs
    y = (v * up).sum(1) / zs
    ok = (z > 0.05) & (np.abs(x) < tan_half_w) & (np.abs(y) < tan_half_h)
    return ok & (d < max_view) & (d > min_view)


def largest_rectangle(mask) -> tuple[int, int, int, int] | None:
    """Largest all-True axis-aligned rectangle of a 2D bool grid: (row0, row1, col0, col1)."""
    rows = len(mask)
    cols = len(mask[0]) if rows else 0
    heights = [0] * cols
    best = (0, None)
    for r in range(rows):
        for c in range(cols):
            heights[c] = heights[c] + 1 if mask[r][c] else 0
        stack: list[int] = []
        for c in range(cols + 1):
            h = heights[c] if c < cols else 0
            start = c
            while stack and heights[stack[-1]] >= h:
                top = stack.pop()
                start = stack[-1] + 1 if stack else 0
                area = heights[top] * (c - start)
                if area > best[0]:
                    best = (area, (r - heights[top] + 1, r, start, c - 1))
            stack.append(c)
    return best[1]


def circular_mean_deg(angles) -> float:
    s = sum(math.sin(math.radians(a)) for a in angles)
    c = sum(math.cos(math.radians(a)) for a in angles)
    return math.degrees(math.atan2(s, c))


def wrap_deg(a: float) -> float:
    return (a + 180.0) % 360.0 - 180.0


def propose(sparse: Path, room: dict, args) -> dict:
    np = _np()
    images = read_images_bin(sparse / "images.bin")
    w, h, fx, fy = read_camera_bin(sparse / "cameras.bin")
    centres_ply, fwd_ply, _world, _scale = nerfstudio_cameras(images)
    cams0 = to_room(centres_ply, room)
    median_h = float(np.median(cams0[:, 1]))
    k = args.eye_height / median_h if args.eye_height > 0 else 1.0
    cams = cams0 * k
    fwd = dirs_to_room(fwd_ply, room)
    tw, th = w / 2 / fx, h / 2 / fy

    cell = args.cell
    lo = cams[:, [0, 2]].min(0) - args.max_view
    hi = cams[:, [0, 2]].max(0) + args.max_view
    xs = np.arange(lo[0], hi[0] + 1e-9, cell)
    zs = np.arange(lo[1], hi[1] + 1e-9, cell)
    cov = np.zeros((len(zs), len(xs)), dtype=int)
    for i, z in enumerate(zs):
        for j, x in enumerate(xs):
            cov[i, j] = min(
                views_of(np.array([x, hgt, z]), cams, fwd, tw, th, args.max_view)
                for hgt in (args.knee, args.head)
            )
    covered = (cov >= args.min_views).tolist()
    rect = largest_rectangle(covered)
    if rect is None:
        raise SystemExit("no covered floor cell; lower --min-views")
    r0, r1, c0, c1 = rect
    walk_min = [float(xs[c0]) + args.inset, float(zs[r0]) + args.inset]
    walk_max = [float(xs[c1]) - args.inset, float(zs[r1]) - args.inset]

    # Orbit limits from the cameras that actually see the walk area (a 3 x 3 sample of it).
    sees = np.zeros(len(cams), dtype=bool)
    for fx_ in (0.2, 0.5, 0.8):
        for fz_ in (0.2, 0.5, 0.8):
            for hgt in (args.knee, args.head):
                pt = np.array(
                    [
                        walk_min[0] + fx_ * (walk_max[0] - walk_min[0]),
                        hgt,
                        walk_min[1] + fz_ * (walk_max[1] - walk_min[1]),
                    ]
                )
                sees |= _seen_mask(pt, cams, fwd, tw, th, args.max_view)
    used = fwd[sees] if sees.sum() >= 3 else fwd
    yaw = [math.degrees(math.atan2(f[0], f[2])) for f in used]
    pitch = [math.degrees(math.asin(max(-1.0, min(1.0, f[1])))) for f in used]
    yaw_c = circular_mean_deg(yaw)
    dev = sorted(abs(wrap_deg(a - yaw_c)) for a in yaw)
    yaw_half = min(180.0, max(45.0, dev[int(0.9 * (len(dev) - 1))]))
    down = sorted(-p for p in pitch)
    max_elev = min(45.0, max(10.0, down[int(0.95 * (len(down) - 1))] + 5.0))
    top = float(np.percentile(cams[:, 1], 95)) + 0.5

    cam_min = [walk_min[0] - args.camera_margin, 0.25, walk_min[1] - args.camera_margin]
    cam_max = [walk_max[0] + args.camera_margin, top, walk_max[1] + args.camera_margin]

    # Back of the walk area relative to the view direction: spawn there, facing the yaw centre.
    fwd_c = np.array([math.sin(math.radians(yaw_c)), math.cos(math.radians(yaw_c))])
    mid = (np.array(walk_min) + np.array(walk_max)) / 2
    half = (np.array(walk_max) - np.array(walk_min)) / 2
    reach = float(np.abs(fwd_c * half).sum())
    spawn_xz = mid - fwd_c * max(0.0, reach - args.spawn_back)

    def band(axis: str, side: int) -> float:
        # mean coverage of the band from the camera box edge to --band metres beyond it
        a = int(round((args.camera_margin + args.inset) / cell))
        n = max(1, int(round(args.band / cell)))
        if axis == "x":
            cols = (
                range(min(len(xs), c1 + 1 + a), min(len(xs), c1 + 1 + a + n))
                if side > 0
                else range(max(0, c0 - a - n), max(0, c0 - a))
            )
            vals = [cov[i, j] for i in range(r0, r1 + 1) for j in cols]
        else:
            rows = (
                range(min(len(zs), r1 + 1 + a), min(len(zs), r1 + 1 + a + n))
                if side > 0
                else range(max(0, r0 - a - n), max(0, r0 - a))
            )
            vals = [cov[i, j] for i in rows for j in range(c0, c1 + 1)]
        return float(np.mean(vals)) if vals else 0.0

    occluders = []
    t = args.occluder_thickness
    gap = args.camera_margin + t / 2
    wall_h = round(top + 0.5, 2)
    for axis, side in (("x", -1), ("x", 1), ("z", -1), ("z", 1)):
        b = band(axis, side)
        if b >= args.min_views / 2:
            continue
        # Never wall off the side the cameras looked towards: what is there (e.g. a far wall)
        # was filmed, from further than --max-view; walling it would hide the best part.
        outward = np.array([side, 0.0]) if axis == "x" else np.array([0.0, side])
        if float(outward @ fwd_c) > math.cos(math.radians(45.0)):
            continue
        if axis == "x":
            x = (walk_min[0] - gap) if side < 0 else (walk_max[0] + gap)
            centre = [x, wall_h / 2, float(mid[1])]
            size = [t, wall_h, float(2 * half[1] + 2 * (args.camera_margin + t))]
        else:
            z = (walk_min[1] - gap) if side < 0 else (walk_max[1] + gap)
            centre = [float(mid[0]), wall_h / 2, z]
            size = [float(2 * half[0] + 2 * (args.camera_margin + t)), wall_h, t]
        occluders.append(
            {
                "name": f"Wall {'-' if side < 0 else '+'}{axis.upper()}",
                "center": [round(v, 2) for v in centre],
                "size": [round(v, 2) for v in size],
                "outsideCoverage": round(b, 1),
            }
        )

    r2 = lambda v: [round(float(a), 2) for a in v]  # noqa: E731
    return {
        "rescale": round(k, 4),
        "position": r2(np.array(room["position"]) * k),
        "scale": r2(np.array(room["scale"]) * k),
        "walkMin": r2(walk_min),
        "walkMax": r2(walk_max),
        "spawn": [round(float(spawn_xz[0]), 2), 0.02, round(float(spawn_xz[1]), 2)],
        "spawnYawDeg": round(yaw_c, 1),
        "cameraMin": r2(cam_min),
        "cameraMax": r2(cam_max),
        "orbitMinElevationDeg": -10.0,
        "orbitMaxElevationDeg": round(max_elev, 1),
        "viewYawCenterDeg": round(yaw_c, 1),
        "viewYawHalfRangeDeg": round(yaw_half, 1),
        "occluders": occluders,
        "stats": {
            "cameras": len(images),
            "median_camera_height_before_m": round(median_h, 3),
            "camera_height_p5_p50_p95_m": r2(np.percentile(cams[:, 1], [5, 50, 95])),
            "camera_pitch_p5_p50_p95_deg": r2(np.percentile(pitch, [5, 50, 95])),
            "camera_x_p5_p95_m": r2(np.percentile(cams[:, 0], [5, 95])),
            "camera_z_p5_p95_m": r2(np.percentile(cams[:, 2], [5, 95])),
            "hfov_deg": round(math.degrees(2 * math.atan(tw)), 1),
            "cameras_seeing_walk_area": int(sees.sum()),
            "their_pitch_p5_p50_p95_deg": r2(np.percentile(pitch, [5, 50, 95])),
            "covered_cells": int((cov >= args.min_views).sum()),
            "walk_rect_mean_views": round(float(cov[r0 : r1 + 1, c0 : c1 + 1].mean()), 1),
        },
    }


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("sparse", type=Path, help="COLMAP sparse model dir (images.bin, cameras.bin)")
    ap.add_argument("room", type=Path, help="splat-room.json with the current placement")
    ap.add_argument(
        "--eye-height", type=float, default=1.5, help="target median camera height (0 = keep)"
    )
    ap.add_argument("--cell", type=float, default=0.25)
    ap.add_argument("--max-view", type=float, default=10.0, help="metres a view counts for")
    ap.add_argument("--min-views", type=int, default=8)
    ap.add_argument("--knee", type=float, default=0.5)
    ap.add_argument("--head", type=float, default=1.7)
    ap.add_argument("--inset", type=float, default=0.3)
    ap.add_argument("--camera-margin", type=float, default=1.0)
    ap.add_argument("--spawn-back", type=float, default=1.0)
    ap.add_argument("--occluder-thickness", type=float, default=0.2)
    ap.add_argument(
        "--band", type=float, default=2.0, help="metres beyond the camera box checked for occluders"
    )
    args = ap.parse_args(argv)
    room = json.loads(args.room.read_text(encoding="utf-8"))
    json.dump(propose(args.sparse, room, args), sys.stdout, indent=2)
    print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
