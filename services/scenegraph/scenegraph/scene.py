"""Build the frozen ``scene_graph.json`` from a cleaned collision mesh (M1-SCEN-02).

Pipeline: scale the reconstruction mesh (real metres, +y up from ARKit gravity) into
A units, move it into the environment-local frame (floor at y=0, centred in x/z),
segment it into planar patches, classify + measure each, run the vision-pass port for
material/semantic labels, compute headroom, and emit the schema-shaped document plus
a reordered collision mesh whose triangles are grouped one contiguous run per surface
(the ``surface.mesh`` triangle ranges point into it).

Pure standard library; deterministic. Scale comes from the capture bundle's metric
scale (SPEC §3.3), passed in ``meta``; it is not guessed here.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from . import geometry as g
from .classify import GeometricStub, SceneConfig, VisionLabeler, classify_patch, measure_patch
from .confidence import gate_surface
from .mesh import Mesh, Vec3
from .segment import Patch, segment_planar

GENERATOR_NAME = "gj-scenegraph"
GENERATOR_VERSION = "0.2.0"
AVATAR_METRES = 1.75  # real human height the 1:12 avatar is scaled from (SPEC §3.2)
DEFAULT_MULTIPLIER = 12.0  # 1:12 (SPEC §3.3 default)
_ROUND = 4


@dataclass(frozen=True)
class CaptureMeta:
    """The non-geometric inputs from the capture bundle / environments row."""

    environment_id: str
    capture_mode: str  # "room" | "tabletop"
    scale_multiplier: float = DEFAULT_MULTIPLIER
    scale_method: str = "default"  # default | inferred-furniture | inferred-studs | inferred-other

    def __post_init__(self) -> None:
        if self.capture_mode not in ("room", "tabletop"):
            raise ValueError("capture_mode must be 'room' or 'tabletop'")
        if not 0.0 < self.scale_multiplier <= 1000.0:
            raise ValueError("scale_multiplier must be in (0, 1000]")
        if self.scale_method not in (
            "default",
            "inferred-furniture",
            "inferred-studs",
            "inferred-other",
        ):
            raise ValueError(f"bad scale_method {self.scale_method!r}")


def _r(x: float) -> float:
    # Round and normalise -0.0 to 0.0 for stable JSON.
    y = round(x, _ROUND)
    return 0.0 if y == 0.0 else y


def _vec(v: Vec3) -> list[float]:
    return [_r(v[0]), _r(v[1]), _r(v[2])]


def _unit(v: Vec3) -> list[float]:
    # Clamp each component to [-1, 1] so rounding never violates the unit3 schema.
    return [max(-1.0, min(1.0, _r(c))) for c in v]


def _scaled_mesh(mesh: Mesh, multiplier: float) -> Mesh:
    s = multiplier / AVATAR_METRES  # metres -> A
    return Mesh([(x * s, y * s, z * s) for (x, y, z) in mesh.vertices], list(mesh.triangles))


def _translated_mesh(mesh: Mesh, offset: Vec3) -> Mesh:
    ox, oy, oz = offset
    return Mesh(
        [(x - ox, y - oy, z - oz) for (x, y, z) in mesh.vertices],
        list(mesh.triangles),
    )


def _mesh_bounds(mesh: Mesh) -> tuple[Vec3, Vec3]:
    xs = [v[0] for v in mesh.vertices]
    ys = [v[1] for v in mesh.vertices]
    zs = [v[2] for v in mesh.vertices]
    return (min(xs), min(ys), min(zs)), (max(xs), max(ys), max(zs))


def _patch_top(patch: Patch) -> float:
    return patch.bounds()[1][1]


def _patch_bottom(patch: Patch) -> float:
    return patch.bounds()[0][1]


def _headroom(patch: Patch, patches: list[Patch], cfg: SceneConfig) -> float:
    """Clear height above a walkable patch: gap up to the nearest patch that overlaps
    it in x/z and sits above it. ``open_headroom_A`` when nothing is above."""
    (minx, _, minz), (maxx, _, maxz) = patch.bounds()
    top = _patch_top(patch)
    best = cfg.open_headroom_A
    for q in patches:
        if q is patch:
            continue
        (qminx, _, qminz), (qmaxx, _, qmaxz) = q.bounds()
        if qmaxx < minx or qminx > maxx or qmaxz < minz or qminz > maxz:
            continue  # no x/z overlap
        gap = _patch_bottom(q) - top
        if gap > 1e-6:
            best = min(best, gap)
    return round(min(best, cfg.open_headroom_A), _ROUND)


def build_scene_graph(
    mesh: Mesh,
    meta: CaptureMeta,
    cfg: SceneConfig | None = None,
    labeler: VisionLabeler | None = None,
) -> tuple[dict, Mesh]:
    """Return (scene_graph document, reordered collision mesh)."""
    cfg = cfg or SceneConfig()
    labeler = labeler or GeometricStub()

    scaled = _scaled_mesh(mesh, meta.scale_multiplier)
    patches = segment_planar(scaled)
    if not patches:
        raise ValueError("no surfaces found in mesh")

    # Floor = the largest up-facing patch; its top defines y=0. Centre x/z on bounds.
    up_patches = [p for p in patches if p.normal[1] > 0.0]
    floor_patch = max(up_patches or patches, key=lambda p: p.area)
    floor_y = _patch_top(floor_patch)
    (bminx, _, bminz), (bmaxx, _, bmaxz) = _mesh_bounds(scaled)
    offset: Vec3 = ((bminx + bmaxx) / 2.0, floor_y, (bminz + bmaxz) / 2.0)

    # Shift the mesh + patches into the local frame. Translation leaves normals and
    # areas unchanged and moves centroids by -offset, so we reuse the one segmentation
    # rather than re-running it (surfaces then pair 1:1 with patches by construction).
    local = _translated_mesh(scaled, offset)
    local_patches = [
        Patch(
            tri_indices=p.tri_indices,
            normal=p.normal,
            centroid=g.sub(p.centroid, offset),
            area=p.area,
            _mesh=local,
        )
        for p in patches
    ]

    surfaces: list[dict] = []
    reordered_tris = []
    for i, patch in enumerate(local_patches, start=1):
        cls, conf = classify_patch(patch, 0.0, cfg)
        label = labeler.label(patch, cls, conf)
        final_class = label.class_override or cls
        final_conf = label.confidence if label.confidence is not None else conf
        # Gate low-confidence geometry to void/unknown (confidence.py) before measuring,
        # so an untrusted surface never carries walkable measurements or a material.
        gate = gate_surface(
            final_class, final_conf, label.material, label.semantic, floor=cfg.confidence_floor
        )
        final_class = gate.cls
        measurements = measure_patch(patch, 0.0, final_class, cfg)
        if final_class in ("walkable-hard", "walkable-narrow", "walkable-soft", "ledge", "stud"):
            measurements["headroom_A"] = _headroom(patch, local_patches, cfg)

        (mnx, mny, mnz), (mxx, mxy, mxz) = patch.bounds()
        start = len(reordered_tris)
        reordered_tris.extend(local.triangles[t] for t in patch.tri_indices)

        surface = {
            "id": f"surface-{i}",
            "class": final_class,
            "confidence": round(max(0.0, min(1.0, final_conf)), 4),
            "material": gate.material,
            "centroid": _vec(patch.centroid),
            "normal": _unit(patch.normal),
            "bounds": {"min": [_r(mnx), _r(mny), _r(mnz)], "max": [_r(mxx), _r(mxy), _r(mxz)]},
            "area_A2": round(patch.area, _ROUND),
            "measurements": measurements,
            "mesh": {
                "submesh": 0,
                "triangle_start": start,
                "triangle_count": patch.triangle_count,
            },
        }
        if gate.semantic is not None:
            surface["semantic"] = gate.semantic
        surfaces.append(surface)

    collision = Mesh(list(local.vertices), reordered_tris)

    # Spawn on the largest low walkable surface (the floor if it is walkable).
    walkables = [
        (s, p)
        for s, p in zip(surfaces, local_patches, strict=True)
        if s["class"] in ("walkable-hard", "walkable-narrow", "walkable-soft")
    ]
    spawn_surface, spawn_patch = (
        min(walkables, key=lambda sp: (sp[0]["measurements"]["top_height_A"], -sp[1].area))
        if walkables
        else (surfaces[0], local_patches[0])
    )
    sx, _, sz = spawn_patch.centroid
    top = spawn_surface["measurements"]["top_height_A"]
    facing = (math.degrees(math.atan2(-sx, -sz)) + 360.0) % 360.0  # face the local origin

    (lbminx, lbminy, lbminz), (lbmaxx, lbmaxy, lbmaxz) = _mesh_bounds(local)
    doc = {
        "schema_version": "1.0.0",
        "environment_id": meta.environment_id,
        "generator": {"name": GENERATOR_NAME, "version": GENERATOR_VERSION},
        "capture_mode": meta.capture_mode,
        "scale": {
            "multiplier": _r(meta.scale_multiplier),
            "method": meta.scale_method,
            "metres_per_A": round(AVATAR_METRES / meta.scale_multiplier, 6),
        },
        "frame": {"units": "A", "up": "+y", "handedness": "left"},
        "bounds": {
            "min": [_r(lbminx), _r(lbminy), _r(lbminz)],
            "max": [_r(lbmaxx), _r(lbmaxy), _r(lbmaxz)],
        },
        "floor_height_A": 0.0,
        "spawn": {
            "position": [_r(sx), _r(top), _r(sz)],
            "facing_deg": round(facing, 2),
            "surface_id": spawn_surface["id"],
        },
        "surfaces": surfaces,
    }
    return doc, collision
