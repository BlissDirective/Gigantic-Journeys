"""M1-PIPE-02 phase 1: find the badly reconstructed regions of a splat room (CPU only).

Box/operator tool (needs numpy and Pillow; CI tests skip without them).

    python -m tools.weak_regions <colmap sparse dir> <trained splat.ply> <splat-room.json> \
        [--shipped <pruned display splat.ply>] \
        [--renders <eval renders dir> --frames <frames dir>] \
        [--png map.png] [--json summary.json]

Run it on the full trained splat: the display prune (``prune_splat_ply.py``) removes the giant
and faint splats, so the shipped splat hides exactly the statistics that flag a weak region;
``--shipped`` adds the share of each cell's splats that the prune removed as a further signal.

The room is cut into floor cells (``--cell`` metres, in the Unity room frame that
``splat-room.json`` places the splat in). Per cell:

1. **View coverage.** How many training cameras see the cell's column, at three heights
   (0.3 / 1.0 / 2.0 m, within ``--max-view`` metres; the frustum test of ``room_limits.py``),
   and how spread out their viewing directions are (1 - |mean unit view vector|; 0 = all from
   one side, which leaves the far side of objects unseen).
2. **Splat statistics** (the splats whose centres fall in the column): count; opacity; the
   share of *giant* splats (largest axis > ``--giant`` m), *needles* (largest/smallest axis >
   ``--needle`` and larger than 5 cm; the trainer's scale regularisation caps the ratio at 10),
   *faint* splats (opacity < 0.15) and *isolated* splats
   (fewer than 4 splats in the surrounding 3 x 3 x 3 block of 15 cm voxels); and the spread
   (standard deviation) of log largest-axis size.
3. **Render-versus-source error** (when ``--renders`` and ``--frames`` are given): the
   trainer's held-out eval renders (source | render side by side) are matched to their source
   frame, colour-matched per channel (so exposure is not counted as error), and the absolute
   error is sampled where the cell's sample points project into each held-out view. There is
   no depth test, so a cell hidden behind a wall in a view still samples it; the per-cell value
   is the median over views, which damps that.

A weakness score in [0, 1] combines low coverage (40%), splat anomalies (30%) and held-out
error (30%; re-weighted onto the other two where no held-out view sees the cell). Writes the
JSON summary (grid, top regions, per-zone aggregates) and a four-panel top-down map.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from tools import room_limits as rl
from tools.prune_splat_ply import read_ply

HEIGHTS = (0.3, 1.0, 2.0)


def _np():
    import numpy as np

    return np


def splat_world(data, room: dict):
    """Centres (N,3) in the room frame, largest/smallest axis (m) and opacity."""
    np = _np()
    xyz = np.stack([data["x"], data["y"], data["z"]], 1).astype(float)
    pos = rl.to_room(xyz, room)
    s = float(np.abs(np.array(room["scale"], dtype=float)).mean())
    sc = np.exp(np.stack([data["scale_0"], data["scale_1"], data["scale_2"]], 1).astype(float)) * s
    opacity = 1.0 / (1.0 + np.exp(-data["opacity"].astype(float)))
    return pos, sc.max(1), sc.min(1), opacity


def isolated_mask(pos, voxel: float = 0.15, min_neighbours: int = 4):
    """True for splats with fewer than ``min_neighbours`` splats in their 3x3x3 voxel block."""
    np = _np()
    keys = np.floor(pos / voxel).astype(np.int64)
    keys -= keys.min(0)
    dims = keys.max(0) + 3
    flat = lambda k: (k[:, 0] * dims[1] + k[:, 1]) * dims[2] + k[:, 2]  # noqa: E731
    ids = flat(keys + 1)
    uniq, counts = np.unique(ids, return_counts=True)
    total = np.zeros(len(pos), dtype=np.int64)
    for dx in (-1, 0, 1):
        for dy in (-1, 0, 1):
            for dz in (-1, 0, 1):
                nid = flat(keys + 1 + np.array([dx, dy, dz]))
                j = np.searchsorted(uniq, nid)
                j = np.clip(j, 0, len(uniq) - 1)
                total += np.where(uniq[j] == nid, counts[j], 0)
    return total < min_neighbours


def room_to_colmap(points, room: dict, world, scale):
    """Inverse of ``to_room`` then of the nerfstudio dataparser transform."""
    np = _np()
    r = rl.unity_rot(room["rotation"])
    s = np.array(room["scale"], dtype=float)
    ply = (r.T @ (np.asarray(points) - np.array(room["position"], dtype=float)).T).T / s
    h = np.c_[ply / scale, np.ones(len(ply))]
    return (np.linalg.inv(world) @ h.T).T[:, :3]


def eval_error_maps(renders: Path, frames: Path, block: int = 16):
    """{frame name: (block-averaged colour-matched abs error map, render width, height)}."""
    np = _np()
    from PIL import Image

    names = sorted(p.name for p in frames.glob("*.jpg"))

    def small(im):
        return np.asarray(im.convert("L").resize((80, 45)), dtype=float)

    lib = np.stack([small(Image.open(frames / n)) for n in names])
    out = {}
    for path in sorted(renders.glob("*.png")):
        im = Image.open(path).convert("RGB")
        w, h = im.size
        gt = np.asarray(im.crop((0, 0, w // 2, h)), dtype=float) / 255
        pr = np.asarray(im.crop((w // 2, 0, 2 * (w // 2), h)), dtype=float) / 255
        name = names[int(((lib - small(im.crop((0, 0, w // 2, h)))) ** 2).mean((1, 2)).argmin())]
        q = np.empty_like(pr)
        for c in range(3):
            a = np.stack([pr[..., c].ravel(), np.ones(pr[..., c].size)], 1)
            k = np.linalg.lstsq(a, gt[..., c].ravel(), rcond=None)[0]
            q[..., c] = pr[..., c] * k[0] + k[1]
        err = np.abs(gt - q).mean(2)
        hh, ww = (err.shape[0] // block) * block, (err.shape[1] // block) * block
        blk = err[:hh, :ww].reshape(hh // block, block, ww // block, block).mean((1, 3))
        out[name] = (blk, w // 2, h)
    return out


def analyse(sparse: Path, ply: Path, room: dict, args) -> dict:
    np = _np()
    images = rl.read_images_bin(sparse / "images.bin")
    cw, ch, fx, fy = rl.read_camera_bin(sparse / "cameras.bin")
    centres_ply, fwd_ply, world, scale = rl.nerfstudio_cameras(images)
    cams = rl.to_room(centres_ply, room)
    fwd = rl.dirs_to_room(fwd_ply, room)
    tw, th = cw / 2 / fx, ch / 2 / fy

    _header, data = read_ply(ply)
    pos, big, small_axis, opacity = splat_world(data, room)
    keep = (pos[:, 1] > -0.5) & (pos[:, 1] < args.top)
    pos, big, small_axis, opacity = pos[keep], big[keep], small_axis[keep], opacity[keep]
    iso = isolated_mask(pos)
    giant = big > args.giant
    needle = (big / np.maximum(small_axis, 1e-6) > args.needle) & (big > 0.05)
    faint = opacity < 0.15
    if args.shipped:
        _h2, shipped = read_ply(args.shipped)
        spos = splat_world(shipped, room)[0]
        spos = spos[(spos[:, 1] > -0.5) & (spos[:, 1] < args.top)]
    else:
        spos = None

    cell = args.cell
    lo = np.floor(np.percentile(pos[:, [0, 2]], 1, axis=0) / cell) * cell
    hi = np.ceil(np.percentile(pos[:, [0, 2]], 99, axis=0) / cell) * cell
    xs = np.arange(lo[0], hi[0], cell)
    zs = np.arange(lo[1], hi[1], cell)
    nz, nx = len(zs), len(xs)
    ci = np.clip(((pos[:, 0] - lo[0]) / cell).astype(int), 0, nx - 1)
    ri = np.clip(((pos[:, 2] - lo[1]) / cell).astype(int), 0, nz - 1)
    inside = (pos[:, 0] >= lo[0]) & (pos[:, 0] < hi[0]) & (pos[:, 2] >= lo[1]) & (pos[:, 2] < hi[1])
    cid = (ri * nx + ci)[inside]

    def per_cell(values):
        s = np.bincount(cid, weights=values[inside].astype(float), minlength=nz * nx)
        return s.reshape(nz, nx)

    count = per_cell(np.ones(len(pos)))
    nonzero = np.maximum(count, 1)
    pruned = np.zeros((nz, nx))
    if spos is not None:
        sc_ = np.clip(((spos[:, 0] - lo[0]) / cell).astype(int), 0, nx - 1)
        sr_ = np.clip(((spos[:, 2] - lo[1]) / cell).astype(int), 0, nz - 1)
        sin = (
            (spos[:, 0] >= lo[0])
            & (spos[:, 0] < hi[0])
            & (spos[:, 2] >= lo[1])
            & (spos[:, 2] < hi[1])
        )
        kept = np.bincount((sr_ * nx + sc_)[sin], minlength=nz * nx).reshape(nz, nx)
        pruned = np.clip(1.0 - kept / nonzero, 0, 1)
    stats = {
        "giant": per_cell(giant) / nonzero,
        "needle": per_cell(needle) / nonzero,
        "faint": per_cell(faint) / nonzero,
        "isolated": per_cell(iso) / nonzero,
        "opacity": per_cell(opacity) / nonzero,
        "pruned": pruned,
    }
    logb = np.log(np.maximum(big, 1e-6))
    mean_l = per_cell(logb) / nonzero
    stats["log_size_std"] = np.sqrt(np.maximum(per_cell(logb**2) / nonzero - mean_l**2, 0))

    views = np.zeros((nz, nx))
    spread = np.zeros((nz, nx))
    for i, z in enumerate(zs + cell / 2):
        for j, x in enumerate(xs + cell / 2):
            vs, dirs = [], []
            for hgt in HEIGHTS:
                p = np.array([x, hgt, z])
                m = rl._seen_mask(p, cams, fwd, tw, th, args.max_view)
                vs.append(int(m.sum()))
                if m.any():
                    d = p - cams[m]
                    dirs.append(d / np.linalg.norm(d, axis=1, keepdims=True))
            views[i, j] = float(np.mean(vs))
            if dirs:
                d = np.concatenate(dirs)
                spread[i, j] = 1.0 - float(np.linalg.norm(d.mean(0)))

    err = np.full((nz, nx), np.nan)
    n_eval = 0
    if args.renders and args.frames:
        maps = eval_error_maps(args.renders, args.frames)
        n_eval = len(maps)
        by_name = {r[3]: r for r in images}
        samples = [[[] for _ in range(nx)] for _ in range(nz)]
        grid = np.array(
            [[x, hgt, z] for z in zs + cell / 2 for x in xs + cell / 2 for hgt in HEIGHTS]
        )
        col = room_to_colmap(grid, room, world, scale)
        for name, (blk, rw, rh) in maps.items():
            if name not in by_name:
                continue
            _iid, q, t, _ = by_name[name]
            pc = (rl.qvec_to_rot(q) @ col.T).T + np.array(t)
            zc = pc[:, 2]
            # distance cut in room metres (COLMAP units differ)
            cam_room = rl.to_room(
                ((world @ np.r_[-(rl.qvec_to_rot(q).T @ np.array(t)), 1.0])[:3] * scale)[None], room
            )[0]
            dist = np.linalg.norm(grid - cam_room, axis=1)
            u = fx * pc[:, 0] / np.maximum(zc, 1e-9) + cw / 2
            v = fy * pc[:, 1] / np.maximum(zc, 1e-9) + ch / 2
            u, v = u * rw / cw, v * rh / ch
            ok = (
                (zc > 0)
                & (dist < args.max_view)
                & (dist > 0.3)
                & (u >= 0)
                & (u < rw)
                & (v >= 0)
                & (v < rh)
            )
            by, bx = blk.shape
            for k in np.nonzero(ok)[0]:
                cell_k = k // len(HEIGHTS)
                i, j = divmod(cell_k, nx)
                samples[i][j].append(
                    float(blk[min(by - 1, int(v[k] * by / rh)), min(bx - 1, int(u[k] * bx / rw))])
                )
        for i in range(nz):
            for j in range(nx):
                if samples[i][j]:
                    err[i, j] = float(np.median(samples[i][j]))

    occupied = count >= args.min_splats
    cov_term = 1.0 - np.clip(views / args.good_views, 0, 1)
    cov_term = np.clip(cov_term + 0.25 * (1.0 - np.clip(spread / 0.3, 0, 1)) * (views > 0), 0, 1)
    raw_anomaly = (
        stats["giant"]
        + 0.5 * stats["needle"]
        + stats["faint"]
        + stats["isolated"]
        + 0.5 * stats["pruned"]
    )
    # Relative to this room: the 90th percentile of occupied cells maps to 1.
    ref = raw_anomaly[occupied]
    anomaly_ref = float(np.percentile(ref, 90)) if ref.size else 1.0
    anomaly_floor = float(np.percentile(ref, 10)) if ref.size else 0.0
    anomaly = np.clip((raw_anomaly - anomaly_floor) / max(anomaly_ref - anomaly_floor, 1e-6), 0, 1)
    finite = err[np.isfinite(err) & occupied]
    err_ref = float(np.percentile(finite, 90)) if finite.size else 1.0
    err_term = np.clip(err / max(err_ref, 1e-6), 0, 1)
    score = np.where(
        np.isfinite(err_term),
        0.4 * cov_term + 0.3 * anomaly + 0.3 * np.nan_to_num(err_term),
        (0.4 * cov_term + 0.3 * anomaly) / 0.7,
    )
    score = np.where(occupied, score, np.nan)

    walk_lo, walk_hi = np.array(room["walkMin"]), np.array(room["walkMax"])
    cx, cz = np.meshgrid(xs + cell / 2, zs + cell / 2)
    in_walk = (cx >= walk_lo[0]) & (cx <= walk_hi[0]) & (cz >= walk_lo[1]) & (cz <= walk_hi[1])
    if room.get("cameraMin"):
        bmin, bmax = np.array(room["cameraMin"]), np.array(room["cameraMax"])
        in_box = (cx >= bmin[0]) & (cx <= bmax[0]) & (cz >= bmin[2]) & (cz <= bmax[2])
    else:
        in_box = in_walk
    # What the player sees: cells within --visible m of the camera box.
    near = np.zeros_like(in_box)
    if room.get("cameraMin"):
        dx = np.maximum(np.maximum(bmin[0] - cx, cx - bmax[0]), 0)
        dz = np.maximum(np.maximum(bmin[2] - cz, cz - bmax[2]), 0)
        near = np.hypot(dx, dz) <= args.visible

    weak = occupied & (score >= args.weak)

    def zone(mask) -> dict:
        m = mask & occupied
        if not m.any():
            return {"cells": 0}
        e = err[m & np.isfinite(err)]
        return {
            "cells": int(m.sum()),
            "splats": int(count[m].sum()),
            "weak_cells": int((m & weak).sum()),
            "weak_share": round(float((m & weak).sum() / m.sum()), 3),
            "median_views": round(float(np.median(views[m])), 1),
            "giant_share": round(float((stats["giant"][m] * count[m]).sum() / count[m].sum()), 4),
            "needle_share": round(float((stats["needle"][m] * count[m]).sum() / count[m].sum()), 4),
            "faint_share": round(float((stats["faint"][m] * count[m]).sum() / count[m].sum()), 4),
            "isolated_share": round(
                float((stats["isolated"][m] * count[m]).sum() / count[m].sum()), 4
            ),
            "pruned_share": round(float((stats["pruned"][m] * count[m]).sum() / count[m].sum()), 4),
            "median_heldout_abs_err": round(float(np.median(e)), 4) if e.size else None,
        }

    # Splats in the floor band, which the Owner calls smeared.
    floor_band = pos[:, 1] < 0.4
    floor = {
        "splats": int(floor_band.sum()),
        "giant_share": round(float(giant[floor_band].mean()), 4),
        "needle_share": round(float(needle[floor_band].mean()), 4),
        "faint_share": round(float(faint[floor_band].mean()), 4),
        "vs_rest_faint_share": round(float(faint[~floor_band].mean()), 4),
        "vs_rest_giant_share": round(float(giant[~floor_band].mean()), 4),
        "vs_rest_needle_share": round(float(needle[~floor_band].mean()), 4),
    }

    # Ties (unseen cells all score 1) break toward cells with more splats: more visible garbage.
    rank = np.nan_to_num(score, nan=-1) + 1e-4 * np.log1p(count)
    order = np.argsort(-rank.ravel())

    def ranked(zone_mask) -> list:
        out = []
        for flat_i in order:
            i, j = divmod(int(flat_i), nx)
            if count[i, j] < args.rank_min_splats or not zone_mask[i, j]:
                continue
            out.append(
                {
                    "x": round(float(xs[j] + cell / 2), 2),
                    "z": round(float(zs[i] + cell / 2), 2),
                    "score": round(float(score[i, j]), 3),
                    "views": round(float(views[i, j]), 1),
                    "view_spread": round(float(spread[i, j]), 3),
                    "splats": int(count[i, j]),
                    "giant": round(float(stats["giant"][i, j]), 3),
                    "needle": round(float(stats["needle"][i, j]), 3),
                    "faint": round(float(stats["faint"][i, j]), 3),
                    "isolated": round(float(stats["isolated"][i, j]), 3),
                    "pruned": round(float(stats["pruned"][i, j]), 3),
                    "heldout_err": None
                    if not np.isfinite(err[i, j])
                    else round(float(err[i, j]), 4),
                    "in_camera_box": bool(in_box[i, j]),
                }
            )
            if len(out) >= args.top_n:
                break
        return out

    result = {
        "tool": "services/reconstruction/tools/weak_regions.py",
        "splat": ply.name,
        "shipped": args.shipped.name if args.shipped else None,
        "splats_analysed": int(len(pos)),
        "cell_m": cell,
        "grid": {"x0": float(lo[0]), "z0": float(lo[1]), "nx": nx, "nz": nz},
        "training_cameras": len(images),
        "heldout_views": n_eval,
        "params": {
            "max_view_m": args.max_view,
            "good_views": args.good_views,
            "giant_m": args.giant,
            "needle_ratio": args.needle,
            "weak_score": args.weak,
            "visible_m": args.visible,
            "heldout_err_p90": round(err_ref, 4),
            "anomaly_p10_p90": [round(anomaly_floor, 4), round(anomaly_ref, 4)],
        },
        "zones": {
            "walk_area": zone(in_walk),
            "camera_box": zone(in_box),
            "visible_from_box": zone(near & ~in_box),
            "whole_room": zone(np.ones_like(in_box)),
        },
        "floor_band_below_0_4m": floor,
        "top_regions_in_camera_box": ranked(in_box),
        "top_regions_visible_from_box": ranked(near & ~in_box),
    }
    arrays = {
        "views": views,
        "anomaly": anomaly,
        "err": err,
        "score": score,
        "xs": xs,
        "zs": zs,
        "cams": cams,
        "fwd": fwd,
    }
    return result, arrays


def draw_map(path: Path, result: dict, arrays: dict, room: dict) -> None:
    np = _np()
    from PIL import Image, ImageDraw

    xs, zs = arrays["xs"], arrays["zs"]
    cell = result["cell_m"]
    px = max(6, int(360 / max(len(xs), len(zs))))
    w, h = len(xs) * px, len(zs) * px
    pad, title = 10, 22

    def cmap(v, lo, hi, invert=False):
        t = np.clip((v - lo) / max(hi - lo, 1e-9), 0, 1)
        if invert:
            t = 1 - t
        # dark blue (good) -> yellow -> red (weak)
        r = np.clip(2 * t, 0, 1)
        g = np.clip(2 - 2 * t, 0, 1) * np.clip(2 * t + 0.2, 0, 1)
        b = np.clip(0.6 - t, 0, 1)
        return (np.stack([r, g, b], -1) * 255).astype(np.uint8)

    panels = [
        ("training views (0-16)", cmap(arrays["views"], 0, 16, invert=True)),
        ("splat anomalies", cmap(arrays["anomaly"], 0, 1)),
        ("held-out error (p90 = red)", cmap(arrays["err"], 0, result["params"]["heldout_err_p90"])),
        ("weakness score", cmap(arrays["score"], 0, 1)),
    ]
    sheet = Image.new("RGB", (4 * (w + pad) + pad, h + title + pad + 30), (24, 24, 24))
    d = ImageDraw.Draw(sheet)

    def to_px(x, z):
        return (x - xs[0]) / cell * px, h - (z - zs[0]) / cell * px  # +z up

    for k, (name, rgb) in enumerate(panels):
        mask = ~np.isfinite(arrays["err"] if "error" in name else arrays["score"])
        rgb = rgb.copy()
        rgb[mask] = (50, 50, 50)
        img = Image.fromarray(rgb[::-1]).resize((w, h), Image.NEAREST)
        ox = pad + k * (w + pad)
        sheet.paste(img, (ox, title))
        d.text((ox, 4), name, fill=(255, 255, 255))
        dd = ImageDraw.Draw(sheet)

        def rect(a, b, colour, width=2, dd=dd, ox=ox):
            x0, y0 = to_px(a[0], a[1])
            x1, y1 = to_px(b[0], b[1])
            dd.rectangle(
                [ox + min(x0, x1), title + min(y0, y1), ox + max(x0, x1), title + max(y0, y1)],
                outline=colour,
                width=width,
            )

        rect(room["walkMin"], room["walkMax"], (255, 255, 255))
        if room.get("cameraMin"):
            rect(
                (room["cameraMin"][0], room["cameraMin"][2]),
                (room["cameraMax"][0], room["cameraMax"][2]),
                (0, 200, 255),
                1,
            )
        for o in room.get("occluders", []):
            c, s = o["center"], o["size"]
            rect(
                (c[0] - s[0] / 2, c[2] - s[2] / 2),
                (c[0] + s[0] / 2, c[2] + s[2] / 2),
                (200, 200, 200),
                3,
            )
        for c, f in zip(arrays["cams"], arrays["fwd"], strict=True):
            x, y = to_px(c[0], c[2])
            if 0 <= x < w and 0 <= y < h:
                x2, y2 = to_px(c[0] + 0.4 * f[0], c[2] + 0.4 * f[2])
                dd.line([ox + x, title + y, ox + x2, title + y2], fill=(255, 255, 255), width=1)
                dd.ellipse([ox + x - 1, title + y - 1, ox + x + 1, title + y + 1], fill=(0, 255, 0))
    d.text(
        (pad, h + title + 8),
        f"Top-down, +z (Round Table end) up, +x right, {cell} m cells. White box = walk area, "
        "cyan = camera box, grey bars = occluder walls, green ticks = training cameras.\n"
        "Blue = good, red = weak; grey = no splats (or no held-out view in the error panel).",
        fill=(220, 220, 220),
    )
    sheet.save(path)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("sparse", type=Path)
    ap.add_argument("ply", type=Path)
    ap.add_argument("room", type=Path)
    ap.add_argument("--renders", type=Path)
    ap.add_argument("--frames", type=Path)
    ap.add_argument("--cell", type=float, default=0.5)
    ap.add_argument("--max-view", type=float, default=10.0)
    ap.add_argument("--good-views", type=float, default=12.0)
    ap.add_argument(
        "--giant", type=float, default=0.25, help="largest axis (m) that counts as giant"
    )
    ap.add_argument("--needle", type=float, default=9.5)
    ap.add_argument("--anomaly-scale", type=float, default=0.6)
    ap.add_argument("--min-splats", type=int, default=20)
    ap.add_argument("--rank-min-splats", type=int, default=150)
    ap.add_argument("--shipped", type=Path)
    ap.add_argument("--top", type=float, default=6.0, help="ignore splats above this height (m)")
    ap.add_argument("--weak", type=float, default=0.5)
    ap.add_argument("--visible", type=float, default=4.0)
    ap.add_argument("--top-n", type=int, default=12)
    ap.add_argument("--png", type=Path)
    ap.add_argument("--json", type=Path)
    args = ap.parse_args(argv)
    room = json.loads(args.room.read_text())
    result, arrays = analyse(args.sparse, args.ply, room, args)
    text = json.dumps(result, indent=2)
    if args.json:
        args.json.write_text(text + "\n")
    if args.png:
        draw_map(args.png, result, arrays, room)
    print(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
