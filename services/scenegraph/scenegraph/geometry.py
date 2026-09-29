"""Small 3D vector helpers, standard library only.

Shared by the scene-graph stages (segmentation, classification, and the later
traversal-graph / reachability work). Vectors are plain 3-tuples of floats, the
same ``Vec3`` the mesh module uses, so nothing here needs numpy.
"""

from __future__ import annotations

import math

from .mesh import Vec3

_UP: Vec3 = (0.0, 1.0, 0.0)


def sub(a: Vec3, b: Vec3) -> Vec3:
    return (a[0] - b[0], a[1] - b[1], a[2] - b[2])


def add(a: Vec3, b: Vec3) -> Vec3:
    return (a[0] + b[0], a[1] + b[1], a[2] + b[2])


def scale(a: Vec3, s: float) -> Vec3:
    return (a[0] * s, a[1] * s, a[2] * s)


def dot(a: Vec3, b: Vec3) -> float:
    return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]


def cross(a: Vec3, b: Vec3) -> Vec3:
    return (
        a[1] * b[2] - a[2] * b[1],
        a[2] * b[0] - a[0] * b[2],
        a[0] * b[1] - a[1] * b[0],
    )


def length(a: Vec3) -> float:
    return math.sqrt(dot(a, a))


def normalize(a: Vec3) -> Vec3:
    n = length(a)
    if n == 0.0:
        return (0.0, 0.0, 0.0)
    return (a[0] / n, a[1] / n, a[2] / n)


def tri_normal(v0: Vec3, v1: Vec3, v2: Vec3) -> Vec3:
    """Unit normal from the triangle winding (right-hand rule). Zero for a
    degenerate triangle."""
    return normalize(cross(sub(v1, v0), sub(v2, v0)))


def tri_area(v0: Vec3, v1: Vec3, v2: Vec3) -> float:
    return 0.5 * length(cross(sub(v1, v0), sub(v2, v0)))


def tri_centroid(v0: Vec3, v1: Vec3, v2: Vec3) -> Vec3:
    return (
        (v0[0] + v1[0] + v2[0]) / 3.0,
        (v0[1] + v1[1] + v2[1]) / 3.0,
        (v0[2] + v1[2] + v2[2]) / 3.0,
    )


def angle_deg(a: Vec3, b: Vec3) -> float:
    """Angle between two vectors in degrees (0..180)."""
    na, nb = length(a), length(b)
    if na == 0.0 or nb == 0.0:
        return 0.0
    c = max(-1.0, min(1.0, dot(a, b) / (na * nb)))
    return math.degrees(math.acos(c))


def slope_deg(normal: Vec3) -> float:
    """Inclination of a surface from horizontal, in degrees: 0 = flat (normal
    straight up or down), 90 = vertical."""
    return 90.0 - abs(angle_deg(normal, _UP) - 90.0)
