"""Prune floaters and oversized splats from a nerfstudio / INRIA splat PLY for display.

Box/operator tool (needs numpy; CI tests skip without it). Implements
:class:`reconstruction.splat_ops.DisplayPrune` vectorised; the per-splat shape rule is the
same as :func:`reconstruction.splat_ops.display_shape_keep`, which the unit tests pin.

    python -m tools.prune_splat_ply in.ply out.ply [--budget 380000] [--stats stats.json]

Writes a PLY with the same header layout and only the kept vertices, plus a JSON summary
of what each rule removed (stdout, and ``--stats`` if given).
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict, fields
from pathlib import Path

from reconstruction.splat_ops import DisplayPrune

PLY_TYPES = {"float": "<f4", "double": "<f8", "uchar": "u1", "int": "<i4", "uint": "<u4"}


def read_ply(path: Path):
    import numpy as np

    raw = path.read_bytes()
    end = raw.index(b"end_header\n") + len(b"end_header\n")
    header = raw[:end].decode("ascii")
    lines = header.splitlines()
    if "format binary_little_endian 1.0" not in lines:
        raise ValueError("only binary_little_endian PLY is supported")
    count = 0
    props: list[tuple[str, str]] = []
    in_vertex = False
    for line in lines:
        parts = line.split()
        if parts[:2] == ["element", "vertex"]:
            count, in_vertex = int(parts[2]), True
        elif parts and parts[0] == "element":
            in_vertex = False
        elif parts and parts[0] == "property" and in_vertex:
            props.append((parts[2], PLY_TYPES[parts[1]]))
    data = np.frombuffer(raw, dtype=np.dtype(props), count=count, offset=end)
    return header, data


def write_ply(path: Path, header: str, data) -> None:
    import re

    new_header = re.sub(r"element vertex \d+", f"element vertex {len(data)}", header, count=1)
    with path.open("wb") as f:
        f.write(new_header.encode("ascii"))
        f.write(data.tobytes())


def prune(data, rules: DisplayPrune):
    """Returns (kept_indices, stats) for a structured PLY vertex array."""
    import numpy as np

    n = len(data)
    xyz = np.stack([data["x"], data["y"], data["z"]], axis=1).astype(np.float64)
    scales = np.stack([data["scale_0"], data["scale_1"], data["scale_2"]], axis=1)
    opacity = data["opacity"].astype(np.float64)
    big = scales.max(axis=1)
    small = scales.min(axis=1)
    stats: dict[str, object] = {"input": int(n), "rules": asdict(rules)}

    keep = np.isfinite(xyz).all(axis=1) & np.isfinite(scales).all(axis=1)
    keep &= np.isfinite(opacity)
    stats["non_finite"] = int(n - keep.sum())

    m = keep & (opacity >= rules.min_opacity_logit)
    stats["faint"] = int(keep.sum() - m.sum())
    keep = m

    cap = float(np.percentile(big[keep], rules.max_scale_percentile))
    m = keep & (big <= cap)
    stats["giant"] = int(keep.sum() - m.sum())
    stats["max_scale_cap_m"] = float(np.exp(cap))
    keep = m

    floor = float(np.percentile(big[keep], rules.needle_scale_percentile))
    needle = (np.exp(big - small) > rules.max_anisotropy) & (big > floor)
    m = keep & ~needle
    stats["needle"] = int(keep.sum() - m.sum())
    keep = m

    p = rules.bounds_percentile
    lo = np.percentile(xyz[keep], p, axis=0)
    hi = np.percentile(xyz[keep], 100.0 - p, axis=0)
    pad = (hi - lo) * rules.bounds_margin
    lo, hi = lo - pad, hi + pad
    m = keep & (xyz >= lo).all(axis=1) & (xyz <= hi).all(axis=1)
    stats["outside_bounds"] = int(keep.sum() - m.sum())
    stats["bounds"] = [lo.tolist(), hi.tolist()]
    keep = m

    g = rules.density_grid
    cell = np.clip(((xyz - lo) / (hi - lo) * g).astype(np.int64), 0, g - 1)
    flat = (cell[:, 0] * g + cell[:, 1]) * g + cell[:, 2]
    counts = np.bincount(flat[keep], minlength=g * g * g).reshape(g, g, g)
    padded = np.pad(counts, 1)
    neigh = np.zeros_like(counts)
    for dx in (0, 1, 2):
        for dy in (0, 1, 2):
            for dz in (0, 1, 2):
                neigh += padded[dx : dx + g, dy : dy + g, dz : dz + g]
    support = neigh[cell[:, 0], cell[:, 1], cell[:, 2]]
    m = keep & (support >= rules.min_neighbourhood)
    stats["isolated"] = int(keep.sum() - m.sum())
    keep = m

    idx = np.nonzero(keep)[0]
    if len(idx) > rules.budget:
        # Display budget: keep the most opaque splats. (The training cap's importance()
        # favours large splats, which are exactly the blur and streaks this removes.)
        order = np.lexsort((idx, -opacity[idx]))[: rules.budget]
        stats["over_budget"] = int(len(idx) - rules.budget)
        idx = np.sort(idx[order])
    else:
        stats["over_budget"] = 0
    stats["output"] = int(len(idx))
    return idx, stats


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("src", type=Path)
    ap.add_argument("dst", type=Path)
    ap.add_argument("--stats", type=Path)
    for f in fields(DisplayPrune):
        ap.add_argument("--" + f.name.replace("_", "-"), type=type(f.default), default=f.default)
    args = ap.parse_args(argv)
    rules = DisplayPrune(**{f.name: getattr(args, f.name) for f in fields(DisplayPrune)})
    header, data = read_ply(args.src)
    idx, stats = prune(data, rules)
    write_ply(args.dst, header, data[idx])
    text = json.dumps(stats, indent=2)
    print(text)
    if args.stats:
        args.stats.write_text(text + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
