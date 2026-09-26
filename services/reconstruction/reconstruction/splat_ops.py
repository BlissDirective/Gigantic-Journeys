"""Pure-Python splat math shared by the in-container scripts and the tests.

Standard library only (CI installs nothing): the container scripts
(``ns_train_capped``, ``ns_finish``, ``mesh``) apply the same rules with
torch / numpy for speed, and the unit tests pin the rules here.

Splat parameters follow nerfstudio / INRIA PLY conventions: ``opacity`` is a
logit (``sigmoid`` gives alpha) and ``scale_*`` are natural-log axis lengths.
"""

from __future__ import annotations

import math
from collections.abc import Sequence
from dataclasses import dataclass

from .models import ReconstructionError

# Env var naming a JSON file where ns_train_capped reports the growth limit's
# effect (budget, refine steps it limited, peak splat count).
STATS_ENV = "GJ_GROWTH_STATS"


def sigmoid(x: float) -> float:
    if x >= 0:
        return 1.0 / (1.0 + math.exp(-x))
    z = math.exp(x)
    return z / (1.0 + z)


def importance(opacity_logit: float, log_scales: Sequence[float]) -> float:
    """How much a splat contributes to renders: alpha x its largest cross-section.

    ``sigmoid(opacity) * exp(s1 + s2)`` for the two largest log-scales (the
    area of the ellipse the splat shows face-on). Faint or tiny splats score
    low and are pruned first when a scene is over the splat budget.
    """
    s = sorted(log_scales, reverse=True)
    return sigmoid(opacity_logit) * math.exp(s[0] + s[1])


def cap_keep_indices(scores: Sequence[float], budget: int) -> list[int]:
    """Indices (ascending) of the ``budget`` highest-scoring splats.

    The hard splat cap: at most ``budget`` survive. Ties break toward the lower
    index so the choice is deterministic. Under budget, everything is kept.
    """
    if budget <= 0:
        raise ReconstructionError("budget must be positive")
    if len(scores) <= budget:
        return list(range(len(scores)))
    order = sorted(range(len(scores)), key=lambda i: (-scores[i], i))
    return sorted(order[:budget])


def growth_headroom(count: int, budget: int) -> int:
    """How many splats densification may still add before hitting ``budget``."""
    return max(0, budget - count)


def percentile(values: Sequence[float], q: float) -> float:
    """Linear-interpolated percentile (numpy's default method), q in [0, 100]."""
    if not values:
        raise ReconstructionError("percentile of an empty sequence")
    if not 0.0 <= q <= 100.0:
        raise ReconstructionError(f"percentile q out of range: {q}")
    s = sorted(values)
    pos = (len(s) - 1) * q / 100.0
    lo = math.floor(pos)
    hi = min(lo + 1, len(s) - 1)
    return s[lo] + (s[hi] - s[lo]) * (pos - lo)


@dataclass(frozen=True)
class MeshFilter:
    """Splat -> collision-mesh cleaning rules (applied before Poisson).

    Stray far-away / faint / huge splats made the Poisson mesh balloon (3.8 to
    46 MB on one config), so only confident surface splats inside a robust
    scene box are meshed:

    - ``min_opacity``: drop splats with alpha below this (floaters, haze).
    - ``bounds_percentile``: the scene box is the [p, 100-p] percentile range of
      the surviving centers per axis, grown by ``bounds_margin`` of its size on
      each side; everything outside is cropped (before and after Poisson).
      With ``bounds_mode="dense"`` (default) the percentiles are taken only over centers
      in *dense* cells (a ``bounds_grid``-cell grid over the percentile box;
      a cell is dense when it holds at least ``dense_cell_fraction`` of the
      mean occupied-cell count), so thin clouds of floaters cannot stretch it.
    - ``max_scale_fraction``: drop splats whose largest axis exceeds this
      fraction of the scene box diagonal (sky / background blobs).
    - ``outlier_neighbors`` / ``outlier_std``: Open3D statistical outlier
      removal on the remaining centers.
    - ``voxel_fraction``: voxel-downsample to this fraction of the diagonal, so
      Poisson sees a density that does not depend on the splat count.
    - ``poisson_depth`` / ``density_quantile``: Poisson octree depth, and the
      low-support vertices (bottom quantile of Poisson density) removed.
    - ``target_triangles``: quadric decimation target (low-poly physics mesh).
    - ``min_cluster_fraction``: connected pieces smaller than this share of the
      triangles are dropped.
    """

    min_opacity: float = 0.5
    bounds_mode: str = "dense"
    bounds_percentile: float = 1.0
    bounds_margin: float = 0.05
    bounds_grid: int = 64
    dense_cell_fraction: float = 0.5
    max_scale_fraction: float = 0.02
    outlier_neighbors: int = 20
    outlier_std: float = 2.0
    voxel_fraction: float = 1 / 512
    poisson_depth: int = 9
    density_quantile: float = 0.05
    target_triangles: int = 100_000
    min_cluster_fraction: float = 0.01

    def __post_init__(self) -> None:
        if not 0.0 <= self.min_opacity < 1.0:
            raise ReconstructionError("min_opacity must be in [0, 1)")
        if not 0.0 <= self.bounds_percentile < 50.0:
            raise ReconstructionError("bounds_percentile must be in [0, 50)")
        if self.target_triangles <= 0:
            raise ReconstructionError("target_triangles must be positive")
        if self.bounds_mode not in ("percentile", "dense"):
            raise ReconstructionError(f"unknown bounds_mode: {self.bounds_mode!r}")

    @property
    def min_opacity_logit(self) -> float:
        """``min_opacity`` as a logit, for comparing raw PLY ``opacity`` values."""
        if self.min_opacity <= 0.0:
            return -math.inf
        return math.log(self.min_opacity / (1.0 - self.min_opacity))


def robust_bounds(
    points: Sequence[Sequence[float]], percentile_: float, margin: float
) -> tuple[tuple[float, float, float], tuple[float, float, float]]:
    """Per-axis [p, 100-p] percentile box of ``points``, grown by ``margin`` x size."""
    if not points:
        raise ReconstructionError("robust_bounds of no points")
    lo: list[float] = []
    hi: list[float] = []
    for axis in range(3):
        col = [p[axis] for p in points]
        a = percentile(col, percentile_)
        b = percentile(col, 100.0 - percentile_)
        pad = (b - a) * margin
        lo.append(a - pad)
        hi.append(b + pad)
    return (lo[0], lo[1], lo[2]), (hi[0], hi[1], hi[2])


def inside(point: Sequence[float], bounds) -> bool:
    lo, hi = bounds
    return all(lo[i] <= point[i] <= hi[i] for i in range(3))
