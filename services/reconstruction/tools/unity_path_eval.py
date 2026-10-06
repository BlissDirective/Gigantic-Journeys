"""Score a room package in the *Unity* render path against its held-out source frames.

The training metrics (``ns_finish``) come from gsplat's renderer; the phone renders the
converted package with the Unity Gaussian-splatting shaders. This tool closes that gap
(M1-PIPE-02 / M1-UNITY-01, 2026-10-06 build-61 device check):

``poses``  COLMAP sparse model + the room descriptor -> JSON of the held-out camera poses
           (nerfstudio colmap dataparser: images sorted by id, every 8th held out; ``up``
           orientation, ``poses`` centring, auto scale) mapped into the Unity room world
           with the descriptor's position / rotation / scale. ``SplatRoomScene.RunPoseRenders``
           (Unity batch mode) renders the shipped package from them.
``score``  Unity renders vs ground truth (the left half of ns_finish ``eval_img_*.png``, i.e.
           the undistorted held-out frame), and optionally vs the gsplat render (right half):
           PSNR per view and mean, written as JSON (numbers only).

Box/operator tool (numpy + Pillow); media never leaves the private staging folder.

    python -m tools.unity_path_eval poses --sparse S --room R.json --out poses.json
    python -m tools.unity_path_eval score --renders DIR --unity DIR --out score.json
"""

from __future__ import annotations

import argparse
import json
import math
import struct
from pathlib import Path

CAMERA_PARAMS = {0: 3, 1: 4, 2: 4, 3: 5, 4: 8, 5: 8}


def _np():
    import numpy as np

    return np


def read_images_bin(path: Path) -> list[tuple[int, list[float], list[float], str]]:
    out = []
    with open(path, "rb") as f:
        (n,) = struct.unpack("<Q", f.read(8))
        for _ in range(n):
            iid, qw, qx, qy, qz, tx, ty, tz, _cid = struct.unpack("<IdddddddI", f.read(64))
            name = b""
            while (c := f.read(1)) != b"\0":
                name += c
            (n2d,) = struct.unpack("<Q", f.read(8))
            f.seek(24 * n2d, 1)
            out.append((iid, [qw, qx, qy, qz], [tx, ty, tz], name.decode()))
    return sorted(out, key=lambda r: r[0])


def read_camera_bin(path: Path) -> dict:
    with open(path, "rb") as f:
        (n,) = struct.unpack("<Q", f.read(8))
        _cid, model, w, h = struct.unpack("<iiQQ", f.read(24))
        params = struct.unpack(f"<{CAMERA_PARAMS[model]}d", f.read(8 * CAMERA_PARAMS[model]))
    fy = params[1] if model in (1, 4, 5) else params[0]
    return {"model": model, "width": w, "height": h, "fy": fy, "params": list(params)}


def qmat(q):
    np = _np()
    w, x, y, z = q
    return np.array(
        [
            [1 - 2 * (y * y + z * z), 2 * (x * y - w * z), 2 * (x * z + w * y)],
            [2 * (x * y + w * z), 1 - 2 * (x * x + z * z), 2 * (y * z - w * x)],
            [2 * (x * z - w * y), 2 * (y * z + w * x), 1 - 2 * (x * x + y * y)],
        ]
    )


def rot_between(a, b):
    np = _np()
    a = a / np.linalg.norm(a)
    b = b / np.linalg.norm(b)
    v = np.cross(a, b)
    s = np.linalg.norm(v)
    if s < 1e-12:
        return np.eye(3)
    v = v / s
    k = np.array([[0, -v[2], v[1]], [v[2], 0, -v[0]], [-v[1], v[0], 0]])
    t = math.acos(max(-1.0, min(1.0, float(a @ b))))
    return np.eye(3) + math.sin(t) * k + (1 - math.cos(t)) * k @ k


def dataparser_poses(images) -> tuple:
    """COLMAP images -> nerfstudio 1.1.5 colmap-dataparser camera-to-world (OpenGL axes)."""
    np = _np()
    applied = np.eye(4)[[0, 2, 1, 3], :]
    applied[2, :] *= -1
    poses = []
    for _iid, q, t, _name in images:
        w2c = np.eye(4)
        w2c[:3, :3] = qmat(q)
        w2c[:3, 3] = t
        c2w = np.linalg.inv(w2c)
        c2w[0:3, 1:3] *= -1
        poses.append(applied @ c2w)
    poses = np.array(poses)
    trans = poses[:, :3, 3].mean(0)
    up = poses[:, :3, 1].mean(0)
    r = rot_between(up / np.linalg.norm(up), np.array([0.0, 0.0, 1.0]))
    t4 = np.eye(4)
    t4[:3, :3] = r
    t4[:3, 3] = r @ -trans
    oriented = t4 @ poses
    scale = 1.0 / np.abs(oriented[:, :3, 3]).max()
    oriented[:, :3, 3] *= scale
    return oriented, scale


def unity_quat_mat(q):
    x, y, z, w = q
    return qmat([w, x, y, z])


def heldout_poses(sparse: Path, room: dict, interval: int = 8) -> dict:
    np = _np()
    images = read_images_bin(sparse / "images.bin")
    cam = read_camera_bin(sparse / "cameras.bin")
    poses, _scale = dataparser_poses(images)
    rq = unity_quat_mat(room["rotation"])
    s = np.array(room["scale"], dtype=float)
    p = np.array(room["position"], dtype=float)
    views = []
    for i in range(0, len(images), interval):
        c2w = poses[i]
        pos = rq @ (c2w[:3, 3] * s) + p
        fwd = rq @ (-c2w[:3, 2] * s)
        up = rq @ (c2w[:3, 1] * s)
        views.append(
            {
                "name": f"eval_{i // interval:04d}",
                "image": images[i][3],
                "pos": [round(float(v), 6) for v in pos],
                "fwd": [round(float(v), 6) for v in fwd / np.linalg.norm(fwd)],
                "up": [round(float(v), 6) for v in up / np.linalg.norm(up)],
            }
        )
    fov = math.degrees(2 * math.atan(cam["height"] / 2 / cam["fy"]))
    return {
        "fov_y_deg": round(fov, 4),
        "width": cam["width"],
        "height": cam["height"],
        "views": views,
    }


def psnr(a, b) -> float:
    np = _np()
    mse = float(np.mean((a.astype(np.float64) - b.astype(np.float64)) ** 2)) / 255.0**2
    return 99.0 if mse <= 1e-12 else 10 * math.log10(1.0 / mse)


def score(renders: Path, unity: Path) -> dict:
    np = _np()
    from PIL import Image

    rows = []
    for u in sorted(unity.glob("eval_*.png")):
        idx = int(u.stem.split("_")[1])
        ref = Image.open(renders / f"eval_img_{idx:04d}.png").convert("RGB")
        w, h = ref.size
        gt = ref.crop((0, 0, w // 2, h))
        gs = ref.crop((w // 2, 0, w, h))
        un = Image.open(u).convert("RGB").resize(gt.size, Image.BILINEAR)
        rows.append(
            {
                "view": idx,
                "psnr_unity_vs_gt": round(psnr(np.asarray(un), np.asarray(gt)), 3),
                "psnr_gsplat_vs_gt": round(psnr(np.asarray(gs), np.asarray(gt)), 3),
                "psnr_unity_vs_gsplat": round(psnr(np.asarray(un), np.asarray(gs)), 3),
            }
        )
    keys = ("psnr_unity_vs_gt", "psnr_gsplat_vs_gt", "psnr_unity_vs_gsplat")
    mean = {k: round(sum(r[k] for r in rows) / max(len(rows), 1), 3) for k in keys}
    return {"views": len(rows), "mean": mean, "per_view": rows}


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="tools.unity_path_eval")
    sub = ap.add_subparsers(dest="cmd", required=True)
    a = sub.add_parser("poses")
    a.add_argument("--sparse", type=Path, required=True)
    a.add_argument("--room", type=Path, required=True)
    a.add_argument("--out", type=Path, required=True)
    a.add_argument("--interval", type=int, default=8)
    b = sub.add_parser("score")
    b.add_argument("--renders", type=Path, required=True)
    b.add_argument("--unity", type=Path, required=True)
    b.add_argument("--out", type=Path, required=True)
    args = ap.parse_args(argv)
    if args.cmd == "poses":
        room = json.loads(args.room.read_text(encoding="utf-8"))
        result = heldout_poses(args.sparse, room, args.interval)
    else:
        result = score(args.renders, args.unity)
    args.out.write_text(json.dumps(result, indent=1) + "\n", encoding="utf-8")
    if "mean" in result:
        print(json.dumps(result["mean"]))
    else:
        print(json.dumps({"views": len(result["views"])}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
