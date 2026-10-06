"""Depth + normal regularisation references (DN-Splatter, Apache-2.0 method).

capture-render-quality-v1 (external-synthesis-builds.md). These are the deterministic,
GPU-free reference implementations of the losses that make a short, sparse handheld
capture reconstruct clean walls/floors instead of floaters and warped planes. The CUDA
trainer (Splatfacto/gsplat, Operator) mirrors this math against the rendered depth/normals;
having a tested stdlib reference pins the contract and lets us unit-test the behaviour
(aligned inputs -> lower loss) with no GPU.

Grids are row-major ``list[list[float]]`` (depth/image, HxW) or ``list[list[tuple3]]``
(normals). ``mask`` is an optional HxW boolean grid; pixels with non-positive ground-truth
depth are always skipped. Standard library only.

- ``edge_aware_log_l1``: log-L1 of sensor depth (ARKit/LiDAR), down-weighted where the
  RGB image gradient is high (depth discontinuities fall on image edges) -- the key trick
  for noisy phone depth.
- ``pearson_depth_loss``: scale-invariant (correlation) loss for a monocular-depth prior,
  which is only correct up to scale.
- ``normal_consistency`` / ``normal_tv``: align predicted normals to a prior and keep them
  locally smooth (flat walls/floors).
"""

from __future__ import annotations

import math
from collections.abc import Sequence

Grid = Sequence[Sequence[float]]
NormalGrid = Sequence[Sequence[tuple[float, float, float]]]
Mask = Sequence[Sequence[bool]] | None


def _dims(grid: Grid) -> tuple[int, int]:
    h = len(grid)
    if h == 0 or len(grid[0]) == 0:
        raise ValueError("grid must be non-empty")
    w = len(grid[0])
    if any(len(row) != w for row in grid):
        raise ValueError("grid must be rectangular")
    return h, w


def _valid(i: int, j: int, gt: Grid, mask: Mask) -> bool:
    if gt[i][j] <= 0.0:
        return False
    return not (mask is not None and not mask[i][j])


def image_gradient_mag(image: Grid) -> list[list[float]]:
    """Forward-difference gradient magnitude of a single-channel image (edge map)."""
    h, w = _dims(image)
    out = [[0.0] * w for _ in range(h)]
    for i in range(h):
        for j in range(w):
            gx = image[i][j + 1] - image[i][j] if j + 1 < w else 0.0
            gy = image[i + 1][j] - image[i][j] if i + 1 < h else 0.0
            out[i][j] = math.hypot(gx, gy)
    return out


def edge_aware_log_l1(
    pred: Grid, gt: Grid, image: Grid, mask: Mask = None, *, edge_weight: float = 1.0
) -> float:
    """Image-edge-aware log-L1 between predicted and sensor depth. 0.0 if nothing valid."""
    h, w = _dims(gt)
    if _dims(pred) != (h, w) or _dims(image) != (h, w):
        raise ValueError("pred, gt, image must share dimensions")
    grad = image_gradient_mag(image)
    total = 0.0
    n = 0
    for i in range(h):
        for j in range(w):
            if not _valid(i, j, gt, mask) or pred[i][j] <= 0.0:
                continue
            wgt = math.exp(-edge_weight * grad[i][j])
            total += wgt * abs(math.log1p(pred[i][j]) - math.log1p(gt[i][j]))
            n += 1
    return total / n if n else 0.0


def pearson_depth_loss(pred: Grid, gt: Grid, mask: Mask = None) -> float:
    """1 - Pearson correlation over valid pixels (scale-invariant). 0.0 if degenerate."""
    h, w = _dims(gt)
    if _dims(pred) != (h, w):
        raise ValueError("pred and gt must share dimensions")
    ps: list[float] = []
    gs: list[float] = []
    for i in range(h):
        for j in range(w):
            if _valid(i, j, gt, mask):
                ps.append(pred[i][j])
                gs.append(gt[i][j])
    n = len(ps)
    if n < 2:
        return 0.0
    mp = sum(ps) / n
    mg = sum(gs) / n
    cov = sum((p - mp) * (g - mg) for p, g in zip(ps, gs, strict=True))
    vp = sum((p - mp) ** 2 for p in ps)
    vg = sum((g - mg) ** 2 for g in gs)
    if vp <= 0.0 or vg <= 0.0:
        return 0.0
    corr = cov / math.sqrt(vp * vg)
    return 1.0 - max(-1.0, min(1.0, corr))


def _unit(n: tuple[float, float, float]) -> tuple[float, float, float]:
    m = math.sqrt(n[0] * n[0] + n[1] * n[1] + n[2] * n[2])
    return (n[0] / m, n[1] / m, n[2] / m) if m > 0 else (0.0, 0.0, 0.0)


def normal_consistency(pred: NormalGrid, ref: NormalGrid, mask: Mask = None) -> float:
    """1 - mean cosine similarity between predicted and reference normals. 0.0 if empty."""
    h = len(pred)
    w = len(pred[0]) if h else 0
    total = 0.0
    n = 0
    for i in range(h):
        for j in range(w):
            if mask is not None and not mask[i][j]:
                continue
            a = _unit(pred[i][j])
            b = _unit(ref[i][j])
            total += a[0] * b[0] + a[1] * b[1] + a[2] * b[2]
            n += 1
    return 1.0 - (total / n) if n else 0.0


def normal_tv(normals: NormalGrid, mask: Mask = None) -> float:
    """Total-variation smoothness of a normal map (mean neighbour L2). 0.0 if empty."""
    h = len(normals)
    w = len(normals[0]) if h else 0
    total = 0.0
    n = 0

    def ok(i: int, j: int) -> bool:
        return mask is None or mask[i][j]

    for i in range(h):
        for j in range(w):
            if not ok(i, j):
                continue
            a = normals[i][j]
            for di, dj in ((0, 1), (1, 0)):
                ni, nj = i + di, j + dj
                if ni < h and nj < w and ok(ni, nj):
                    b = normals[ni][nj]
                    total += math.sqrt((a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2 + (a[2] - b[2]) ** 2)
                    n += 1
    return total / n if n else 0.0
