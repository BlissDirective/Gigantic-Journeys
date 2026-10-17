"""Per-region coverage map of a reconstruction (bedroom cleanup stage 1; stage 6 bounds).

M1-PIPE-02 bedroom cleanup. From an SfM model (COLMAP / GLOMAP ``sparse/``: cameras,
images, points3D *with tracks*) and optionally its frames, voxelise the reconstructed
surface and record per voxel:

* ``views``: distinct images that observe a point in the voxel (from the tracks, so it
  is real visibility, not frustum guessing);
* ``spread_deg``: angular spread of those viewing rays (parallax; low = depth unsure);
* ``sharpness``: median Laplacian variance of the observing frames (blur proxy).

A voxel is **weak** when views < ``min_views`` OR spread < ``min_spread_deg`` OR its
sharpness is in the bottom quartile of the frames. Weak voxels are grouped into
connected regions (the list the cleanup stages target), and a top-down heatmap (up axis
from the cameras) is written as PNG. ``camera_bounds`` gives the well-covered volume for
the game camera (stage 6): the up-aligned box of strong voxels, shrunk to the camera
positions' footprint, plus the transform from SfM world to that frame.

numpy + Pillow (lazy imports). Runs on the box CPU: no GPU, nothing leaves the box.
"""

from __future__ import annotations

import json
import struct
from collections import deque
from dataclasses import dataclass, field
from pathlib import Path

from .prior_alignment import find_model_dir, read_colmap_cameras


def read_images_with_ids(model_dir: Path) -> dict[int, tuple[str, tuple, tuple]]:
    """``{image_id: (name, (qw,qx,qy,qz), (tx,ty,tz))}`` world->camera, bin or txt."""
    out: dict[int, tuple[str, tuple, tuple]] = {}
    binary, text = model_dir / "images.bin", model_dir / "images.txt"
    if binary.exists():
        with binary.open("rb") as fh:
            (n,) = struct.unpack("<Q", fh.read(8))
            for _ in range(n):
                iid, qw, qx, qy, qz, tx, ty, tz, _cid = struct.unpack("<I7dI", fh.read(64))
                name = bytearray()
                while (ch := fh.read(1)) != b"\0":
                    name += ch
                (npts,) = struct.unpack("<Q", fh.read(8))
                fh.seek(24 * npts, 1)
                out[iid] = (name.decode(), (qw, qx, qy, qz), (tx, ty, tz))
    elif text.exists():
        lines = [ln for ln in text.read_text(encoding="utf-8").splitlines() if ln[:1] != "#"]
        for line in lines[::2]:
            if not line.strip():
                continue
            f = line.split()
            out[int(f[0])] = (f[9], tuple(map(float, f[1:5])), tuple(map(float, f[5:8])))
    return out


def read_points_with_tracks(model_dir: Path) -> tuple[list[tuple], list[list[int]]]:
    """Point xyz list and, per point, the image ids of its track (bin or txt)."""
    xyz: list[tuple] = []
    tracks: list[list[int]] = []
    binary, text = model_dir / "points3D.bin", model_dir / "points3D.txt"
    if binary.exists():
        with binary.open("rb") as fh:
            (n,) = struct.unpack("<Q", fh.read(8))
            for _ in range(n):
                _pid, x, y, z = struct.unpack("<Q3d", fh.read(32))
                fh.read(3 + 8)
                (tl,) = struct.unpack("<Q", fh.read(8))
                ids = struct.unpack(f"<{2 * tl}i", fh.read(8 * tl))[::2]
                xyz.append((x, y, z))
                tracks.append(sorted(set(ids)))
    elif text.exists():
        for line in text.read_text(encoding="utf-8").splitlines():
            if not line or line.startswith("#"):
                continue
            f = line.split()
            xyz.append((float(f[1]), float(f[2]), float(f[3])))
            tracks.append(sorted({int(v) for v in f[8::2]}))
    return xyz, tracks


def quat_to_rot(q):
    import numpy as np

    w, x, y, z = q
    return np.array(
        [
            [1 - 2 * (y * y + z * z), 2 * (x * y - w * z), 2 * (x * z + w * y)],
            [2 * (x * y + w * z), 1 - 2 * (x * x + z * z), 2 * (y * z - w * x)],
            [2 * (x * z - w * y), 2 * (y * z + w * x), 1 - 2 * (x * x + y * y)],
        ]
    )


def camera_centres_and_up(images: dict[int, tuple]) -> tuple[dict[int, object], object]:
    """World camera centres per image id and the world up vector (−mean camera +y)."""
    import numpy as np

    centres, downs = {}, []
    for iid, (_n, q, t) in images.items():
        r = quat_to_rot(q)
        centres[iid] = -r.T @ np.asarray(t)
        downs.append(r.T @ np.array([0.0, 1.0, 0.0]))  # OpenCV camera +y is image-down
    up = -np.mean(downs, axis=0)
    return centres, up / max(np.linalg.norm(up), 1e-12)


def up_frame(up):
    """Rotation whose rows are (x, y=up, z): world -> up-aligned frame."""
    import numpy as np

    a = np.array([1.0, 0.0, 0.0]) if abs(up[0]) < 0.9 else np.array([0.0, 0.0, 1.0])
    x = np.cross(up, a)
    x /= np.linalg.norm(x)
    z = np.cross(x, up)
    return np.stack([x, up, z])


def laplacian_variance(path: Path, long_side: int = 640) -> float:
    """Blur proxy: variance of the 4-neighbour Laplacian of the downscaled grey frame."""
    import numpy as np
    from PIL import Image

    with Image.open(path) as im:
        im = im.convert("L")
        s = long_side / max(im.size)
        if s < 1:
            im = im.resize((max(1, round(im.width * s)), max(1, round(im.height * s))))
        g = np.asarray(im, dtype=np.float64)
    lap = -4 * g[1:-1, 1:-1] + g[:-2, 1:-1] + g[2:, 1:-1] + g[1:-1, :-2] + g[1:-1, 2:]
    return float(lap.var())


@dataclass
class CoverageMap:
    voxel: float
    origin: list[float]
    up: list[float]
    voxels: dict[tuple[int, int, int], dict] = field(default_factory=dict)
    weak_regions: list[dict] = field(default_factory=list)
    thresholds: dict = field(default_factory=dict)
    camera_bounds: dict = field(default_factory=dict)

    def summary(self) -> dict:
        n = len(self.voxels)
        weak = sum(1 for v in self.voxels.values() if v["weak"])
        return {
            "voxel_m_or_units": round(self.voxel, 4),
            "occupied_voxels": n,
            "weak_voxels": weak,
            "weak_fraction": round(weak / max(n, 1), 4),
            "thresholds": self.thresholds,
            "weak_regions": self.weak_regions,
            "camera_bounds": self.camera_bounds,
        }


def build_coverage(
    model_dir: Path,
    frames_dir: Path | None = None,
    grid: int = 40,
    min_views: int = 5,
    min_spread_deg: float = 10.0,
    min_region_voxels: int = 3,
) -> CoverageMap:
    import numpy as np

    images = read_images_with_ids(model_dir)
    xyz_l, tracks = read_points_with_tracks(model_dir)
    if not xyz_l:
        raise ValueError(f"no points in {model_dir}")
    centres, up = camera_centres_and_up(images)
    xyz = np.asarray(xyz_l)
    lo, hi = np.percentile(xyz, 1, axis=0), np.percentile(xyz, 99, axis=0)
    keep = np.all((xyz >= lo) & (xyz <= hi), axis=1)
    voxel = float(np.linalg.norm(hi - lo) / grid)
    sharp: dict[int, float] = {}
    if frames_dir is not None:
        for iid, (name, _q, _t) in images.items():
            p = frames_dir / name
            if p.exists():
                sharp[iid] = laplacian_variance(p)
    q25 = float(np.percentile(list(sharp.values()), 25)) if sharp else None
    cells: dict[tuple[int, int, int], dict] = {}
    for i in np.nonzero(keep)[0]:
        key = tuple(int(v) for v in np.floor((xyz[i] - lo) / voxel))
        c = cells.setdefault(key, {"points": 0, "views": set()})
        c["points"] += 1
        c["views"].update(tracks[i])
    out: dict[tuple[int, int, int], dict] = {}
    for key, c in cells.items():
        centre = lo + (np.asarray(key) + 0.5) * voxel
        ids = [v for v in c["views"] if v in centres]
        dirs = np.array([centres[v] - centre for v in ids]) if ids else np.zeros((0, 3))
        spread = 0.0
        if len(dirs) >= 2:
            d = dirs / np.linalg.norm(dirs, axis=1, keepdims=True)
            m = d.mean(0)
            m /= max(np.linalg.norm(m), 1e-12)
            spread = float(2 * np.degrees(np.arccos(np.clip(d @ m, -1, 1)).max()))
        sh = [sharp[v] for v in ids if v in sharp]
        sharpness = float(np.median(sh)) if sh else None
        weak_why = []
        if len(ids) < min_views:
            weak_why.append("views")
        if spread < min_spread_deg:
            weak_why.append("parallax")
        if q25 is not None and sharpness is not None and sharpness < q25:
            weak_why.append("blur")
        out[key] = {
            "centre": centre.tolist(),
            "points": c["points"],
            "views": len(ids),
            "spread_deg": round(spread, 1),
            "sharpness": None if sharpness is None else round(sharpness, 1),
            "weak": bool(weak_why),
            "why": weak_why,
        }
    cov = CoverageMap(voxel=voxel, origin=lo.tolist(), up=up.tolist(), voxels=out)
    cov.thresholds = {
        "min_views": min_views,
        "min_spread_deg": min_spread_deg,
        "blur_q25_laplacian_var": None if q25 is None else round(q25, 1),
    }
    cov.weak_regions = weak_regions(out, voxel, min_region_voxels)
    cov.camera_bounds = camera_bounds(out, centres, up)
    return cov


def weak_regions(voxels: dict, voxel: float, min_size: int) -> list[dict]:
    """26-connected components of weak voxels, largest first."""
    import numpy as np

    weak = {k for k, v in voxels.items() if v["weak"]}
    seen: set = set()
    regions = []
    for start in weak:
        if start in seen:
            continue
        comp, dq = [], deque([start])
        seen.add(start)
        while dq:
            k = dq.popleft()
            comp.append(k)
            for dx in (-1, 0, 1):
                for dy in (-1, 0, 1):
                    for dz in (-1, 0, 1):
                        n = (k[0] + dx, k[1] + dy, k[2] + dz)
                        if n in weak and n not in seen:
                            seen.add(n)
                            dq.append(n)
        if len(comp) < min_size:
            continue
        cs = np.array([voxels[k]["centre"] for k in comp])
        why: dict[str, int] = {}
        for k in comp:
            for w in voxels[k]["why"]:
                why[w] = why.get(w, 0) + 1
        regions.append(
            {
                "voxels": len(comp),
                "centroid": cs.mean(0).round(3).tolist(),
                "bbox_min": cs.min(0).round(3).tolist(),
                "bbox_max": cs.max(0).round(3).tolist(),
                "mean_views": round(float(np.mean([voxels[k]["views"] for k in comp])), 1),
                "why": dict(sorted(why.items(), key=lambda kv: -kv[1])),
            }
        )
    regions.sort(key=lambda r: -r["voxels"])
    for i, r in enumerate(regions):
        r["id"] = f"W{i + 1:02d}"
    return regions


def camera_bounds(voxels: dict, centres: dict, up) -> dict:
    """Well-covered camera volume in the up-aligned frame (stage 6 game-camera limits).

    Horizontal: the 5-95th percentile box of the capture camera positions, clipped to the
    box of strong voxels. Vertical: from 0.1 m-equivalent above the strong-voxel floor
    (5th pct height) to the highest camera. All in SfM units, frame ``rotation``.
    """
    import numpy as np

    rot = up_frame(np.asarray(up))
    cams = np.array([rot @ c for c in centres.values()])
    strong = np.array([rot @ np.asarray(v["centre"]) for v in voxels.values() if not v["weak"]])
    if len(strong) == 0 or len(cams) == 0:
        return {}
    c_lo, c_hi = np.percentile(cams, 5, axis=0), np.percentile(cams, 95, axis=0)
    s_lo, s_hi = np.percentile(strong, 2, axis=0), np.percentile(strong, 98, axis=0)
    lo = np.maximum(c_lo, s_lo)
    hi = np.minimum(c_hi, s_hi)
    lo[1] = float(np.percentile(strong[:, 1], 5))
    hi[1] = float(cams[:, 1].max())
    return {
        "frame": "up-aligned (rows of rotation = x, up, z), SfM units",
        "rotation": rot.round(6).tolist(),
        "min": lo.round(4).tolist(),
        "max": hi.round(4).tolist(),
        "camera_box_min": c_lo.round(4).tolist(),
        "camera_box_max": c_hi.round(4).tolist(),
    }


def heatmap_png(cov: CoverageMap, path: Path, metric: str = "views", px: int = 12) -> Path:
    """Top-down heatmap (up-aligned x/z) of ``metric`` (min over each column = weakest
    surface seen from above), weak columns outlined red. Metrics only: no image content."""
    import numpy as np
    from PIL import Image, ImageDraw

    rot = up_frame(np.asarray(cov.up))
    pts = np.array([rot @ np.asarray(v["centre"]) for v in cov.voxels.values()])
    vals = [v[metric] or 0 for v in cov.voxels.values()]
    weak = [v["weak"] for v in cov.voxels.values()]
    ij = np.floor((pts[:, [0, 2]] - pts[:, [0, 2]].min(0)) / cov.voxel).astype(int)
    w, h = ij.max(0) + 1
    grid = np.full((h, w), np.nan)
    wk = np.zeros((h, w), bool)
    for (i, j), v, k in zip(ij, vals, weak, strict=True):
        grid[j, i] = v if np.isnan(grid[j, i]) else min(grid[j, i], v)
        wk[j, i] |= k
    vmax = max(np.nanpercentile(grid, 95), 1e-9)
    img = Image.new("RGB", (w * px, h * px), (20, 20, 20))
    d = ImageDraw.Draw(img)
    for j in range(h):
        for i in range(w):
            if np.isnan(grid[j, i]):
                continue
            t = float(min(grid[j, i] / vmax, 1.0))
            col = (int(255 * (1 - t)), int(200 * t + 30), int(80 * t))
            box = [i * px, j * px, (i + 1) * px - 1, (j + 1) * px - 1]
            d.rectangle(box, fill=col, outline=(255, 0, 0) if wk[j, i] else None)
    img.save(path)
    return path


def main(argv: list[str] | None = None) -> int:
    import argparse

    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--sparse", type=Path, required=True)
    p.add_argument("--frames", type=Path)
    p.add_argument("--out", type=Path, required=True, help="output dir (box-private)")
    p.add_argument("--grid", type=int, default=40)
    a = p.parse_args(argv)
    model = find_model_dir(a.sparse)
    if model is None or not read_colmap_cameras(model):
        raise SystemExit(f"no COLMAP model under {a.sparse}")
    cov = build_coverage(model, a.frames, grid=a.grid)
    a.out.mkdir(parents=True, exist_ok=True)
    (a.out / "coverage.json").write_text(json.dumps(cov.summary(), indent=2) + "\n")
    heatmap_png(cov, a.out / "coverage-views.png", "views")
    heatmap_png(cov, a.out / "coverage-spread.png", "spread_deg")
    if a.frames:
        heatmap_png(cov, a.out / "coverage-sharpness.png", "sharpness")
    s = cov.summary()
    print(json.dumps({k: s[k] for k in ("occupied_voxels", "weak_voxels", "weak_fraction")}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
