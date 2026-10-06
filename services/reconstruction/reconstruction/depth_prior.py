"""Monocular depth prior integration: align a relative depth map to ARKit metric depth.

capture-render-quality-v1 (external-synthesis-builds.md). A relative monocular depth map
(Depth Anything V2 *Small*, Apache-2.0, ~30 fps on-device; or Metric3D v2, BSD code with
weights to verify) is only correct up to an unknown scale and shift. This module solves a
least-squares ``(scale, shift)`` against the ARKit/LiDAR metric depth over the valid
overlap, turning the prior into a metric depth map we can feed to the regularisers in
``depth_normal.py`` where real sensor depth is missing (textureless walls, far surfaces).

The ``DepthPrior`` port lets any model plug in; the model inference itself is GPU/Operator.
Deterministic, standard library only.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Protocol

Grid = Sequence[Sequence[float]]
Mask = Sequence[Sequence[bool]] | None


class DepthPrior(Protocol):
    """A monocular model that predicts a (relative or metric) depth map from an image."""

    name: str

    def predict(self, image: Grid) -> list[list[float]]: ...


def align_scale_shift(relative: Grid, metric: Grid, mask: Mask = None) -> tuple[float, float]:
    """Least-squares (scale, shift) so that ``scale*relative + shift ~= metric``.

    Fit over pixels that are valid (``mask`` true where given) and have positive metric
    depth. Raises if fewer than two valid pixels or the relative depth has no variance.
    """
    rs: list[float] = []
    ms: list[float] = []
    for i, row in enumerate(metric):
        for j, mval in enumerate(row):
            if mval <= 0.0 or (mask is not None and not mask[i][j]):
                continue
            rs.append(relative[i][j])
            ms.append(mval)
    n = len(rs)
    if n < 2:
        raise ValueError("need at least 2 valid pixels to align scale/shift")
    mr = sum(rs) / n
    mm = sum(ms) / n
    var = sum((r - mr) ** 2 for r in rs)
    if var <= 0.0:
        raise ValueError("relative depth has no variance; cannot solve scale")
    cov = sum((r - mr) * (m - mm) for r, m in zip(rs, ms, strict=True))
    scale = cov / var
    shift = mm - scale * mr
    return scale, shift


def apply_scale_shift(relative: Grid, scale: float, shift: float) -> list[list[float]]:
    """Return ``scale*relative + shift`` as a new grid."""
    return [[scale * v + shift for v in row] for row in relative]


def to_metric(relative: Grid, metric: Grid, mask: Mask = None) -> list[list[float]]:
    """Align ``relative`` to the ``metric`` reference and return the metric-scaled prior."""
    scale, shift = align_scale_shift(relative, metric, mask)
    return apply_scale_shift(relative, scale, shift)


class MockDepthPrior:
    """Deterministic stand-in for a real model: returns a fixed planar ramp. Test use only."""

    name = "mock"

    def predict(self, image: Grid) -> list[list[float]]:
        h = len(image)
        w = len(image[0]) if h else 0
        # A simple front-to-back ramp in [1, 2]; shape, not metric scale, is what matters.
        return [[1.0 + (i + j) / max(1, (h + w)) for j in range(w)] for i in range(h)]
