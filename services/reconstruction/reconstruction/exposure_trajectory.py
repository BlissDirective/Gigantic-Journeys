"""In-exposure camera trajectory for motion-blur-aware training (BAD-Gaussians method).

capture-render-quality-v1 (external-synthesis-builds.md). BAD-Gaussians (Apache-2.0,
Nerfstudio-native) models the motion blur in a handheld frame as the integral of the
scene over the continuous camera trajectory *during that frame's exposure*: it renders a
set of virtual sharp sub-frame views along the trajectory and averages them, and
bundle-adjusts the trajectory jointly with the splats. That turns inevitable handheld
blur into usable (and pose-refining) supervision.

This module is the deterministic, GPU-free core of that idea: given the camera pose(s)
over an exposure, produce the ``num_samples`` sub-frame poses to render, plus the
averaging weights. The CUDA trainer (Operator) renders + averages; ARKit gives the
per-frame pose these trajectories hang off. Poses are ``(quat (w,x,y,z), translation)``.

Standard library only; deterministic.
"""

from __future__ import annotations

import math

Quat = tuple[float, float, float, float]
Vec3 = tuple[float, float, float]
Pose = tuple[Quat, Vec3]


def normalize_quat(q: Quat) -> Quat:
    n = math.sqrt(q[0] * q[0] + q[1] * q[1] + q[2] * q[2] + q[3] * q[3])
    if n == 0.0:
        return (1.0, 0.0, 0.0, 0.0)
    return (q[0] / n, q[1] / n, q[2] / n, q[3] / n)


def _dot(a: Quat, b: Quat) -> float:
    return a[0] * b[0] + a[1] * b[1] + a[2] * b[2] + a[3] * b[3]


def slerp(q0: Quat, q1: Quat, t: float) -> Quat:
    """Spherical linear interpolation between unit quaternions; shortest arc."""
    q0 = normalize_quat(q0)
    q1 = normalize_quat(q1)
    d = _dot(q0, q1)
    if d < 0.0:  # take the shorter path
        q1 = (-q1[0], -q1[1], -q1[2], -q1[3])
        d = -d
    if d > 0.9995:  # nearly parallel -> normalized lerp (avoids division blow-up)
        out = tuple(a + t * (b - a) for a, b in zip(q0, q1, strict=True))
        return normalize_quat(out)  # type: ignore[arg-type]
    theta = math.acos(max(-1.0, min(1.0, d)))
    s = math.sin(theta)
    w0 = math.sin((1.0 - t) * theta) / s
    w1 = math.sin(t * theta) / s
    return (
        w0 * q0[0] + w1 * q1[0],
        w0 * q0[1] + w1 * q1[1],
        w0 * q0[2] + w1 * q1[2],
        w0 * q0[3] + w1 * q1[3],
    )


def _lerp3(a: Vec3, b: Vec3, t: float) -> Vec3:
    return (a[0] + t * (b[0] - a[0]), a[1] + t * (b[1] - a[1]), a[2] + t * (b[2] - a[2]))


def interpolate_pose(p0: Pose, p1: Pose, t: float) -> Pose:
    """Interpolate a single pose at ``t`` in [0, 1] (slerp rotation, lerp translation)."""
    return (slerp(p0[0], p1[0], t), _lerp3(p0[1], p1[1], t))


def sample_linear(start: Pose, end: Pose, num_samples: int) -> list[Pose]:
    """Linear in-exposure model: ``num_samples`` poses from start (t=0) to end (t=1).

    ``num_samples == 1`` returns the mid-exposure pose (t=0.5).
    """
    if num_samples < 1:
        raise ValueError("num_samples must be >= 1")
    if num_samples == 1:
        return [interpolate_pose(start, end, 0.5)]
    return [interpolate_pose(start, end, k / (num_samples - 1)) for k in range(num_samples)]


def sample_cubic_bspline(controls: list[Pose], num_samples: int) -> list[Pose]:
    """Smooth in-exposure trajectory over 4 control poses (uniform cubic B-spline).

    Translations use the uniform cubic B-spline basis over the central segment; rotations
    use a normalized-lerp blend of the four control quaternions with the same basis (a
    documented approximation of a rotation spline -- smooth and unit, good enough to
    synthesise sub-frame blur). Returns ``num_samples`` poses.
    """
    if len(controls) != 4:
        raise ValueError("cubic B-spline needs exactly 4 control poses")
    if num_samples < 1:
        raise ValueError("num_samples must be >= 1")
    out: list[Pose] = []
    denom = 1 if num_samples == 1 else num_samples - 1
    for k in range(num_samples):
        u = 0.5 if num_samples == 1 else k / denom
        u2, u3 = u * u, u * u * u
        # Uniform cubic B-spline basis for the central segment.
        b0 = (1 - 3 * u + 3 * u2 - u3) / 6.0
        b1 = (4 - 6 * u2 + 3 * u3) / 6.0
        b2 = (1 + 3 * u + 3 * u2 - 3 * u3) / 6.0
        b3 = u3 / 6.0
        w = (b0, b1, b2, b3)
        tx = sum(w[m] * controls[m][1][0] for m in range(4))
        ty = sum(w[m] * controls[m][1][1] for m in range(4))
        tz = sum(w[m] * controls[m][1][2] for m in range(4))
        q = [0.0, 0.0, 0.0, 0.0]
        ref = normalize_quat(controls[1][0])
        for m in range(4):
            cq = normalize_quat(controls[m][0])
            if _dot(cq, ref) < 0.0:  # hemisphere-align before blending
                cq = (-cq[0], -cq[1], -cq[2], -cq[3])
            for c in range(4):
                q[c] += w[m] * cq[c]
        out.append((normalize_quat((q[0], q[1], q[2], q[3])), (tx, ty, tz)))
    return out


def exposure_weights(num_samples: int) -> list[float]:
    """Uniform averaging weights for the sub-frame renders (they sum to 1)."""
    if num_samples < 1:
        raise ValueError("num_samples must be >= 1")
    return [1.0 / num_samples] * num_samples
