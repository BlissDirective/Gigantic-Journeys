"""Bedroom cleanup stages 3 + 6: planar proxies and coverage camera bounds -> Unity room.

Box/operator tool (numpy). Maps the outputs of ``reconstruction.planar_proxies`` (stage 3)
and ``reconstruction.coverage_map`` (stage 1) from the COLMAP frame into the Unity room of
a ``splat-room*.json`` descriptor, the same way ``room_limits`` maps the training cameras
(nerfstudio colmap-dataparser transform, then the descriptor placement), and prints a
**proposal** (never edits the descriptor):

* ``planeProxies``: world-space quads (4 corners, Unity room metres) + texture name +
  mean colour fallback, with ``planeProxiesEnabled: false`` (default off). The loader draws
  them as opaque cut-out quads; the splat composite (ZTest Always) lands on top, so the
  planes only show through holes. Each quad is pushed ``--pushback`` metres away from the
  room so splats lying on a wall stay in front.
* ``coverageCameraBox``: the descriptor camera box intersected with the well-covered
  volume from the coverage map (strong voxels + camera footprint), for stage 6. Apply by
  copying it into ``cameraMin`` / ``cameraMax`` once the Owner build checks it.

Textures are bedroom imagery: they stay in the box's chmod-700 staging and travel only
inside the private splat package (AUTH #046 / #047), never in git.

    python -m tools.cleanup_proxies <sparse> <splat-room.json> --planes planes.json \\
        --frames <blurred frames> [--pushback 0.03]
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

try:
    from tools import room_limits as rl
except ImportError:  # run from tools/
    import room_limits as rl  # type: ignore[no-redef]


def colmap_to_room(points, sparse: Path, room: dict):
    """Raw COLMAP points (N,3) -> Unity room world via the nerfstudio frame + placement."""
    np = rl._np()
    images = rl.read_images_bin(sparse / "images.bin")
    _c, _f, world, scale = rl.nerfstudio_cameras(images)
    p = np.asarray(points, dtype=float)
    ply = (world @ np.c_[p, np.ones(len(p))].T).T[:, :3] * scale
    return rl.to_room(ply, room)


def plane_to_room(plane: dict, sparse: Path, room: dict, pushback: float) -> dict:
    np = rl._np()
    corners = colmap_to_room(plane["corners"], sparse, room)
    n = np.cross(corners[1] - corners[0], corners[3] - corners[0])
    n /= max(np.linalg.norm(n), 1e-12)
    cams = colmap_to_room(_camera_centres(sparse), sparse, room)
    if n @ (cams.mean(0) - corners.mean(0)) < 0:
        n = -n  # face the room
    corners = corners - pushback * n  # behind the surface splats
    return {
        "name": plane.get("id", ""),
        "label": plane["label"],
        "corners": [round(float(v), 4) for v in corners.reshape(-1)],
        "texture": Path(plane["texture"]).stem if plane.get("texture") else "",
        "color": plane.get("color", [0.5, 0.5, 0.5]),
    }


def _camera_centres(sparse: Path):
    np = rl._np()
    out = []
    for _iid, q, t, _name in rl.read_images_bin(sparse / "images.bin"):
        r = rl.qvec_to_rot(q)
        out.append(-r.T @ np.asarray(t))
    return np.array(out)


def coverage_camera_box(strong_centres, sparse: Path, room: dict, margin: float = 0.3) -> dict:
    """Descriptor camera box clipped to strong voxels (+``margin`` m) and camera footprint."""
    np = rl._np()
    pts = colmap_to_room(strong_centres, sparse, room)
    cams = colmap_to_room(_camera_centres(sparse), sparse, room)
    lo = np.percentile(pts, 2, axis=0) - margin
    hi = np.percentile(pts, 98, axis=0) + margin
    lo = np.minimum(lo, np.percentile(cams, 5, axis=0))
    hi = np.maximum(hi, np.percentile(cams, 95, axis=0))
    if room.get("cameraMin"):
        lo = np.maximum(lo, np.asarray(room["cameraMin"], float))
        hi = np.minimum(hi, np.asarray(room["cameraMax"], float))
    walk_lo, walk_hi = room["walkMin"], room["walkMax"]  # the box must contain the walk
    lo[0], lo[2] = min(lo[0], walk_lo[0]), min(lo[2], walk_lo[1])
    hi[0], hi[2] = max(hi[0], walk_hi[0]), max(hi[2], walk_hi[1])
    lo[1] = max(lo[1], 0.05)
    return {"cameraMin": lo.round(3).tolist(), "cameraMax": hi.round(3).tolist()}


def keep_reason(plane: dict, room_plane: dict, min_fill: float, min_wall_height: float) -> str:
    """'' to keep, else why the plane is dropped (sparse fit, or a strip, not a wall)."""
    np = rl._np()
    if plane.get("fill", 1.0) < min_fill:
        return f"fill {plane.get('fill')} < {min_fill}"
    if room_plane["label"] == "wall":
        ys = np.asarray(room_plane["corners"]).reshape(4, 3)[:, 1]
        if ys.max() - ys.min() < min_wall_height:
            return f"height {ys.max() - ys.min():.2f} m < {min_wall_height}"
    return ""


def mean_color(path: Path) -> list[float]:
    np = rl._np()
    from PIL import Image

    a = np.asarray(Image.open(path).convert("RGBA"), dtype=float)
    m = a[..., 3] > 0
    return (a[..., :3][m].mean(0) / 255).round(3).tolist() if m.any() else [0.5, 0.5, 0.5]


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("sparse", type=Path)
    ap.add_argument("room", type=Path)
    ap.add_argument("--planes", type=Path, help="planar_proxies planes.json")
    ap.add_argument("--frames", type=Path, help="frames for the coverage map (optional)")
    ap.add_argument("--pushback", type=float, default=0.03, help="m behind the surface")
    ap.add_argument("--min-fill", type=float, default=0.35, help="drop sparse RANSAC planes")
    ap.add_argument("--min-wall-height", type=float, default=0.3, help="m; drop strips")
    ap.add_argument("--min-views", type=int, default=5)
    ap.add_argument("--min-spread", type=float, default=6.0)
    a = ap.parse_args(argv)
    room = json.loads(a.room.read_text(encoding="utf-8"))
    out: dict = {"planeProxiesEnabled": False, "planeProxies": [], "planesDropped": []}
    if a.planes:
        for p in json.loads(a.planes.read_text(encoding="utf-8")):
            if p.get("texture"):
                p["color"] = mean_color(a.planes.parent / p["texture"])
            q = plane_to_room(p, a.sparse, room, a.pushback)
            why = keep_reason(p, q, a.min_fill, a.min_wall_height)
            if why:
                out["planesDropped"].append({"name": q["name"], "label": q["label"], "why": why})
            else:
                out["planeProxies"].append(q)
    from reconstruction.coverage_map import build_coverage

    cov = build_coverage(a.sparse, a.frames, min_views=a.min_views, min_spread_deg=a.min_spread)
    strong = [v["centre"] for v in cov.voxels.values() if not v["weak"]]
    out["coverageCameraBox"] = coverage_camera_box(strong, a.sparse, room)
    out["coverageCameraBox"]["current"] = {
        "cameraMin": room.get("cameraMin"),
        "cameraMax": room.get("cameraMax"),
    }
    print(json.dumps(out, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
