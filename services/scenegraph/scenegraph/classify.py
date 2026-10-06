"""Geometric surface classification + measurement (M1-SCEN-02, step 2).

Every planar patch is given a Bible §4 class and its A-unit measurements from
geometry alone — orientation (up / vertical / down / sloped) and size. This is the
deterministic, GPU-free core.

The finer classes that depend on material or a repeating pattern — walkable-soft,
ledge, rung, stud, textured-vertical, pole, soft-hanging — and every material and
semantic label come from a **vision pass**. SPEC §3.3 requires that pass to run on
our own infrastructure (never sending a user's scan off-site), so it is self-hosted
GPU work and is deferred behind the ``VisionLabeler`` port below; the default
``GeometricStub`` labels material ``unknown`` and keeps the geometric class. The
coarse geometric graph is still a valid input to the traversal stage (M1-SCEN-03),
because traversal edges come from the height relationships between walkable surfaces,
not from the fine class.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from . import geometry as g
from .segment import Patch


@dataclass(frozen=True)
class SceneConfig:
    # Slope (degrees from horizontal) at or below which a patch is "flat" — a
    # walkable top if it faces up, an overhang if it faces down.
    walkable_max_slope_deg: float = 35.0
    # Slope at or above which a patch is a vertical face (wall family).
    wall_min_slope_deg: float = 60.0
    # A walkable top narrower than this (A units) is walkable-narrow (schema note:
    # walkable-narrow < 0.5 A).
    narrow_width_A: float = 0.5
    # Clear height below which a walkable surface is crouch-only (Bible; schema note
    # crouchHeadroomA 1.1). Recorded, not a class.
    crouch_headroom_A: float = 1.1
    # An up-facing patch whose top sits more than this far below the floor is a void
    # (a drop-off), not a walkable surface.
    void_drop_A: float = 1.5
    # Headroom reported when nothing is above a surface (open sky / open room).
    open_headroom_A: float = 50.0
    # Default classifier confidence for a geometry-decided class.
    geom_confidence: float = 0.7
    # Surfaces the vision/reconstruction pass trusts less than this are demoted to
    # void/unknown (confidence.gate_surface). 0.0 disables the gate (default); the
    # self-hosted vision pass, which emits per-surface confidence, sets it.
    confidence_floor: float = 0.0

    def __post_init__(self) -> None:
        if not 0.0 <= self.walkable_max_slope_deg < self.wall_min_slope_deg <= 90.0:
            raise ValueError("need 0 <= walkable_max_slope < wall_min_slope <= 90")
        if not 0.0 <= self.confidence_floor <= 1.0:
            raise ValueError("confidence_floor must be in [0, 1]")


@dataclass(frozen=True)
class VisionLabel:
    """What a vision pass adds to a patch. The stub returns the defaults."""

    material: str = "unknown"
    semantic: str | None = None
    class_override: str | None = None
    confidence: float | None = None


class VisionLabeler(Protocol):
    """Port for the material/semantic vision pass (SPEC §3.3, self-hosted)."""

    def label(self, patch: Patch, geom_class: str, confidence: float) -> VisionLabel: ...


class GeometricStub:
    """No vision model: material ``unknown``, no semantic, keep the geometric class.

    The real adapter runs a self-hosted vision model on the reconstruction's own
    renders (never off-site) and is Operator/GPU-gated; it plugs in here without
    changing the geometric core.
    """

    def label(self, patch: Patch, geom_class: str, confidence: float) -> VisionLabel:
        return VisionLabel()


def _extent(patch: Patch) -> tuple[float, float, float, float, float, float]:
    (minx, miny, minz), (maxx, maxy, maxz) = patch.bounds()
    return minx, miny, minz, maxx, maxy, maxz


def classify_patch(patch: Patch, floor_y: float, cfg: SceneConfig) -> tuple[str, float]:
    """Return (Bible §4 class, confidence) from geometry alone."""
    minx, _, minz, maxx, maxy, maxz = _extent(patch)
    slope = g.slope_deg(patch.normal)
    top_height = maxy - floor_y
    facing_up = patch.normal[1] > 0.0

    if slope <= cfg.walkable_max_slope_deg and facing_up:
        if top_height < -cfg.void_drop_A:
            return "void", 0.9
        width = min(maxx - minx, maxz - minz)
        if width < cfg.narrow_width_A:
            return "walkable-narrow", cfg.geom_confidence - 0.05
        return "walkable-hard", cfg.geom_confidence
    if slope <= cfg.walkable_max_slope_deg and not facing_up:
        return "overhang", cfg.geom_confidence
    if slope >= cfg.wall_min_slope_deg:
        return "wall-smooth", cfg.geom_confidence
    return "slope", cfg.geom_confidence


def measure_patch(patch: Patch, floor_y: float, cls: str, cfg: SceneConfig) -> dict:
    """A-unit measurements for a patch; only the fields relevant to the class are
    present (``top_height_A`` is always required by the schema)."""
    minx, _, minz, maxx, maxy, maxz = _extent(patch)
    x_ext, z_ext = maxx - minx, maxz - minz
    m: dict[str, float] = {"top_height_A": round(maxy - floor_y, 4)}

    if cls in ("walkable-hard", "walkable-narrow", "ledge", "stud", "walkable-soft"):
        m["width_A"] = round(min(x_ext, z_ext), 4)
    if cls in ("walkable-narrow", "ledge"):
        m["edge_length_A"] = round(max(x_ext, z_ext), 4)
    if cls in ("wall-smooth", "textured-vertical"):
        # Usable face length along the ground and the face's rise.
        m["edge_length_A"] = round(max(x_ext, z_ext), 4)
    if cls == "slope":
        m["slope_deg"] = round(g.slope_deg(patch.normal), 2)
    return m
