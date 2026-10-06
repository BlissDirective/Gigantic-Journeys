"""Compression budget planner for on-device delivery (SOG / .spz).

capture-render-quality-v1 (external-synthesis-builds.md). To land a dense room inside the
~150 MB iPhone budget we quantise + compress the splat: Self-Organizing Gaussians (PlayCanvas
splat-transform, MIT) sorts Gaussians into 2D attribute grids and image-codes them, and the
.spz container (Niantic, MIT) bit-packs them. Both are commercial-safe code the Operator
integrates; this module is the GPU-free *planner* that chooses parameters (SH degree + a
codec factor) to hit a byte target and reports whether it fits. Deterministic, stdlib only.
"""

from __future__ import annotations

from dataclasses import dataclass

# Quantised geometry per splat: position + scale (3+3 at ~2 B) + rotation (4 at ~1 B) +
# opacity (~1 B). A deliberately conservative constant; the real encoder measures exactly.
GEOMETRY_BYTES = 16.0
# View-dependent colour: (degree+1)^2 SH coeffs x 3 channels at ~1 B/coeff after quantisation.
_SH_COEFFS = {0: 1, 1: 4, 2: 9, 3: 16}
# Self-Organizing-Gaussians image coding compresses the quantised grid further. SOG/PlayCanvas
# report ~20-40x over raw float 3DGS; relative to the *quantised* bytes here, ~0.5 is a safe,
# conservative additional factor.
DEFAULT_CODEC_FACTOR = 0.5


def sh_bytes(sh_degree: int) -> float:
    if sh_degree not in _SH_COEFFS:
        raise ValueError("sh_degree must be 0, 1, 2 or 3")
    return _SH_COEFFS[sh_degree] * 3.0


@dataclass(frozen=True)
class CompressionPlan:
    sh_degree: int
    bytes_per_splat: float
    estimated_bytes: int
    fits: bool
    codec_factor: float


def estimate_bytes(
    splat_count: int, sh_degree: int, *, codec_factor: float = DEFAULT_CODEC_FACTOR
) -> int:
    """Estimated delivered bytes for a splat at a given SH degree + codec factor."""
    if splat_count < 0:
        raise ValueError("splat_count must be >= 0")
    if not 0.0 < codec_factor <= 1.0:
        raise ValueError("codec_factor must be in (0, 1]")
    per = (GEOMETRY_BYTES + sh_bytes(sh_degree)) * codec_factor
    return int(round(splat_count * per))


def plan_compression(
    splat_count: int,
    target_bytes: int,
    *,
    max_sh_degree: int = 3,
    codec_factor: float = DEFAULT_CODEC_FACTOR,
) -> CompressionPlan:
    """Pick the highest SH degree <= ``max_sh_degree`` whose estimate fits ``target_bytes``.

    If even degree 0 overflows, returns that smallest plan with ``fits=False`` (the caller
    then has to cut the splat count -- e.g. a tighter training budget or more pruning).
    """
    if target_bytes <= 0:
        raise ValueError("target_bytes must be positive")
    for d in range(max_sh_degree, -1, -1):
        est = estimate_bytes(splat_count, d, codec_factor=codec_factor)
        if est <= target_bytes:
            per = (GEOMETRY_BYTES + sh_bytes(d)) * codec_factor
            return CompressionPlan(d, per, est, True, codec_factor)
    per0 = (GEOMETRY_BYTES + sh_bytes(0)) * codec_factor
    return CompressionPlan(
        0, per0, estimate_bytes(splat_count, 0, codec_factor=codec_factor), False, codec_factor
    )
