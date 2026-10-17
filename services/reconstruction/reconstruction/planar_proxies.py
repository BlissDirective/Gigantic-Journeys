"""Planar proxies for a room reconstruction (bedroom cleanup stage 3, CPU prep).

M1-PIPE-02 bedroom cleanup. Detect the room's big planes from the SfM points (floor,
ceiling, walls) with RANSAC in the up-aligned frame (``coverage_map.up_frame``), fit a
rectangle to each plane's inliers, and bake a texture for it from the sharpest frames that
observe it (perspective warp of the rectangle into each frame, median of the top-k
sharpest so a passing blur or occluder does not win). Unity composites these textured
quads behind the splats (splats on top) to fill holes and steady flat surfaces.

Door / window frames are rectangles *inside* a wall plane; detecting them needs the
texture (edge/line evidence), so ``wall_openings`` is a stage-3 GPU-day follow-up and is
not implemented here.

numpy + Pillow (lazy imports). Runs on the box CPU; outputs stay box-private.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path

from .coverage_map import (
    camera_centres_and_up,
    laplacian_variance,
    quat_to_rot,
    read_images_with_ids,
    read_points_with_tracks,
    up_frame,
)
from .prior_alignment import find_model_dir, read_colmap_cameras


@dataclass
class Plane:
    label: str  # floor | ceiling (above every camera) | wall
    normal: list[float]  # world, unit, pointing into the room (toward the cameras)
    offset: float  # n . x + d = 0
    corners: list[list[float]]  # 4 world corners, CCW seen from the room
    inliers: int
    images: list[int]  # image ids that observe its inliers, sharpest first
    fill: float = 1.0  # share of the rectangle's 16x16 cells holding inliers

    def to_json(self) -> dict:
        return asdict(self)


def ransac_plane(pts, iters: int, tol: float, rng, axis=None, max_angle_deg: float = 10.0):
    """Best plane (n, d, inlier mask). ``axis`` (unit) constrains n: ``("par", a)`` keeps
    n within ``max_angle_deg`` of a; ``("perp", a)`` keeps n perpendicular to a."""
    import numpy as np

    best = (None, None, np.zeros(len(pts), bool))
    if len(pts) < 3:
        return best
    cos_tol = np.cos(np.radians(max_angle_deg))
    sin_tol = np.sin(np.radians(max_angle_deg))
    for _ in range(iters):
        s = pts[rng.choice(len(pts), 3, replace=False)]
        n = np.cross(s[1] - s[0], s[2] - s[0])
        nn = np.linalg.norm(n)
        if nn < 1e-12:
            continue
        n /= nn
        if axis is not None:
            kind, a = axis
            c = abs(float(n @ a))
            if (kind == "par" and c < cos_tol) or (kind == "perp" and c > sin_tol):
                continue
        d = -float(n @ s[0])
        mask = np.abs(pts @ n + d) < tol
        if mask.sum() > best[2].sum():
            best = (n, d, mask)
    n, d, mask = best
    if n is not None and mask.sum() >= 3:  # least-squares refit on inliers
        q = pts[mask]
        c = q.mean(0)
        _u, _s, vt = np.linalg.svd(q - c, full_matrices=False)
        n2 = vt[-1]
        if n2 @ n < 0:
            n2 = -n2
        ok = True
        if axis is not None:
            kind, a = axis
            c2 = abs(float(n2 @ a))
            ok = c2 >= cos_tol if kind == "par" else c2 <= sin_tol
        if ok:  # the refit must still satisfy the orientation constraint
            n, d = n2, -float(n2 @ c)
            mask = np.abs(pts @ n + d) < tol
    return n, d, mask


def plane_rectangle(pts, n, up):
    """4 corners (world) of the 2-98 pct rectangle of ``pts`` in the plane, axes chosen
    so walls stay upright (one in-plane axis = up projected) and floors align to x."""
    import numpy as np

    u = up - (up @ n) * n
    if np.linalg.norm(u) < 1e-6:  # horizontal plane: use world-ish x
        u = np.cross(n, [0.0, 0.0, 1.0] if abs(n[2]) < 0.9 else [1.0, 0.0, 0.0])
    u /= np.linalg.norm(u)
    v = np.cross(n, u)
    c = pts.mean(0)
    a, b = (pts - c) @ u, (pts - c) @ v
    a0, a1 = np.percentile(a, [2, 98])
    b0, b1 = np.percentile(b, [2, 98])
    return [(c + x * u + y * v).tolist() for x, y in ((a0, b0), (a1, b0), (a1, b1), (a0, b1))]


def rectangle_fill(pts, corners, cells: int = 16) -> float:
    """Share of the rectangle's ``cells`` x ``cells`` grid with at least one inlier: a real
    wall/floor fills its rectangle; a RANSAC plane threaded through clutter does not."""
    import numpy as np

    c = np.asarray(corners)
    o, eu, ev = c[0], c[1] - c[0], c[3] - c[0]
    lu, lv = np.linalg.norm(eu), np.linalg.norm(ev)
    if lu < 1e-9 or lv < 1e-9:
        return 0.0
    a = (pts - o) @ (eu / lu) / lu
    b = (pts - o) @ (ev / lv) / lv
    m = (a >= 0) & (a < 1) & (b >= 0) & (b < 1)
    ia, ib = (a[m] * cells).astype(int).tolist(), (b[m] * cells).astype(int).tolist()
    occ = set(zip(ia, ib, strict=True))
    return len(occ) / (cells * cells)


def detect_planes(
    model_dir: Path,
    max_walls: int = 6,
    tol_frac: float = 0.01,
    min_inlier_frac: float = 0.02,
    iters: int = 2000,
    seed: int = 0,
    sharpness: dict[int, float] | None = None,
) -> list[Plane]:
    import numpy as np

    images = read_images_with_ids(model_dir)
    xyz_l, tracks = read_points_with_tracks(model_dir)
    centres, up = camera_centres_and_up(images)
    xyz = np.asarray(xyz_l)
    lo, hi = np.percentile(xyz, 1, axis=0), np.percentile(xyz, 99, axis=0)
    idx = np.nonzero(np.all((xyz >= lo) & (xyz <= hi), axis=1))[0]
    tol = tol_frac * float(np.linalg.norm(hi - lo))
    rng = np.random.default_rng(seed)
    rot = up_frame(up)
    cam_mean = np.mean(list(centres.values()), axis=0)
    heights = (xyz[idx] @ rot.T)[:, 1]
    planes: list[Plane] = []
    remaining = idx.copy()
    min_in = max(10, int(min_inlier_frac * len(idx)))

    def add(label, n, d, mask, pool):
        sel = pool[mask]
        if n @ cam_mean + d < 0:  # face the room (cameras)
            n, d = -n, -d
        seen: dict[int, int] = {}
        for i in sel:
            for v in tracks[i]:
                seen[v] = seen.get(v, 0) + 1
        ims = sorted(seen, key=lambda v: (-(sharpness or {}).get(v, 0.0), -seen[v]))
        corners = plane_rectangle(xyz[sel], n, up)
        fill = round(rectangle_fill(xyz[sel], corners), 3)
        planes.append(Plane(label, n.tolist(), d, corners, int(len(sel)), ims, fill))
        return pool[~mask]

    cam_h = float(np.max([(rot @ c)[1] for c in centres.values()]))
    for label, band in (("floor", heights < np.percentile(heights, 30)),
                        ("ceiling", heights > max(np.percentile(heights, 85), cam_h))):  # fmt: skip
        pool = idx[band]
        n, d, mask = ransac_plane(xyz[pool], iters, tol, rng, ("par", up))
        if n is not None and mask.sum() >= min_in:
            add(label, n, d, mask, pool)
            remaining = np.setdiff1d(remaining, pool[mask])
    for _ in range(max_walls):
        n, d, mask = ransac_plane(xyz[remaining], iters, tol, rng, ("perp", up))
        if n is None or mask.sum() < min_in:
            break
        remaining = add("wall", n, d, mask, remaining)
    return planes


def project(k, r, t, pts):
    """Pinhole projection (no distortion) of world points -> pixel (u, v), depth."""
    import numpy as np

    pc = (r @ np.asarray(pts).T).T + t
    uv = (k @ pc.T).T
    return uv[:, :2] / uv[:, 2:3], pc[:, 2]


def intrinsics(cam: dict):
    import numpy as np

    p = cam["params"]
    if cam["model"] in ("SIMPLE_PINHOLE", "SIMPLE_RADIAL", "RADIAL"):
        f, cx, cy = p[0], p[1], p[2]
        fx = fy = f
    else:
        fx, fy, cx, cy = p[:4]
    return np.array([[fx, 0, cx], [0, fy, cy], [0, 0, 1.0]])


def bake_texture(
    plane: Plane,
    model_dir: Path,
    frames_dir: Path,
    size=(512, 512),
    top_k=5,
    max_incidence_deg: float = 60.0,
    max_candidates: int = 40,
    min_valid: int = 1,
):
    """Mosaic texture: per texel, median of up to ``top_k`` of the sharpest frontal frames
    (within ``max_incidence_deg`` of the normal, all corners in front of the camera) in
    which that texel lands inside the frame. Partial views are fine; texels no frame saw
    stay transparent (alpha 0) for the splats / generative repair (stage 4) to cover.
    Returns an RGBA PIL image, or None if no frame qualifies."""
    import numpy as np
    from PIL import Image

    from .prior_alignment import read_colmap_images

    cams = read_colmap_cameras(model_dir)
    imgs = read_images_with_ids(model_dir)
    cam_of = {name: cid for name, (cid, _q, _t) in read_colmap_images(model_dir).items()}
    w, h = size
    centre = np.mean(np.asarray(plane.corners), axis=0)
    normal = np.asarray(plane.normal)
    cos_max = np.cos(np.radians(max_incidence_deg))
    layers, masks = [], []
    for iid in plane.images[:max_candidates]:
        if len(layers) >= top_k * 3 or iid not in imgs:
            break
        name, q, t = imgs[iid]
        r = quat_to_rot(q)
        to_cam = -r.T @ np.asarray(t) - centre
        if to_cam @ normal < cos_max * np.linalg.norm(to_cam):
            continue  # grazing view: the texture would smear
        cam = cams[cam_of[name]]
        uv, z = project(intrinsics(cam), r, np.asarray(t), plane.corners)
        if (z <= 0).any() or not (frames_dir / name).exists():
            continue
        # corner 0 -> texture bottom-left: matches the Unity quad UVs (SplatRoomLoader)
        coeffs = perspective_coeffs([(0, h), (w, h), (w, 0), (0, 0)], uv.tolist())
        with Image.open(frames_dir / name) as im:
            rgb = im.convert("RGB")
        ones = Image.new("L", rgb.size, 255)
        warped = np.asarray(rgb.transform(size, Image.PERSPECTIVE, coeffs, Image.BILINEAR))
        valid = np.asarray(ones.transform(size, Image.PERSPECTIVE, coeffs, Image.NEAREST)) > 0
        if valid.mean() < 0.05:
            continue
        layers.append(warped.astype(np.float32))
        masks.append(valid)
    if not layers:
        return None
    stack = np.stack(layers)
    m = np.stack(masks)
    m &= np.cumsum(m, axis=0) <= top_k  # first top_k valid (sharpest) frames per texel
    stack[~m] = np.nan
    with np.errstate(all="ignore"):
        import warnings

        with warnings.catch_warnings():
            warnings.simplefilter("ignore", RuntimeWarning)
            rgb = np.nanmedian(stack, axis=0)
    alpha = np.where(m.sum(0) >= min_valid, 255, 0).astype(np.uint8)
    rgb = np.nan_to_num(rgb).clip(0, 255).astype(np.uint8)
    return Image.fromarray(np.dstack([rgb, alpha]), "RGBA")


def perspective_coeffs(dst, src):
    """PIL PERSPECTIVE coefficients mapping output pixel ``dst[i]`` -> input ``src[i]``."""
    import numpy as np

    a, b = [], []
    for (x, y), (u, v) in zip(dst, src, strict=True):
        a.append([x, y, 1, 0, 0, 0, -u * x, -u * y])
        a.append([0, 0, 0, x, y, 1, -v * x, -v * y])
        b += [u, v]
    return np.linalg.solve(np.asarray(a, float), np.asarray(b, float)).tolist()


def main(argv: list[str] | None = None) -> int:
    import argparse

    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--sparse", type=Path, required=True)
    p.add_argument("--frames", type=Path)
    p.add_argument("--out", type=Path, required=True, help="output dir (box-private)")
    a = p.parse_args(argv)
    model = find_model_dir(a.sparse)
    if model is None:
        raise SystemExit(f"no COLMAP model under {a.sparse}")
    sharp = None
    if a.frames:
        sharp = {
            iid: laplacian_variance(a.frames / n)
            for iid, (n, _q, _t) in read_images_with_ids(model).items()
            if (a.frames / n).exists()
        }
    planes = detect_planes(model, sharpness=sharp)
    a.out.mkdir(parents=True, exist_ok=True)
    meta = []
    for i, pl in enumerate(planes):
        rec = pl.to_json() | {"id": f"P{i:02d}"}
        rec["images"] = rec["images"][:10]
        if a.frames:
            tex = bake_texture(pl, model, a.frames)
            if tex is not None:
                tex.save(a.out / f"P{i:02d}-{pl.label}.png")
                rec["texture"] = f"P{i:02d}-{pl.label}.png"
        meta.append(rec)
    (a.out / "planes.json").write_text(json.dumps(meta, indent=2) + "\n")
    print(json.dumps([(m["id"], m["label"], m["inliers"], "texture" in m) for m in meta]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
