"""Traversal-graph export (M1-SCEN-03): scene_graph.json -> traversal_graph.json.

Places nodes on the classified surfaces — a stance on a walkable top (large surfaces
also get edge-midpoint stances, so a neighbour near any part of them has a close
jump-off point and a route can walk across them), a hang on a ledge/overhang, a climb
on a climbable face, a grapple anchor on a deep ledge. Then it adds edges:
- intra-surface locomotion (walking is free between stance nodes on one solid surface);
- one inter-surface crossing per (surface pair, target-node kind), at the true
  edge-to-edge gap, from the A node nearest B to the nearest B node of each kind — so a
  grapple still targets an anchor and a jump a stance.
Every edge's verb is one the source surface's Bible §4 class enables (AT-2); tool verbs
ride the same affordance mapping with their movement.json prerequisites (AT-4); and
every edge is accepted only if reachable under config/movement.json at the 85 % margin
(the same check the M1-SCEN-05 validator runs).

Standard library only; deterministic.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path

import affordances
import movement
from affordances import Context
from movement import MovementConfig

GENERATOR_NAME = "gj-traversal"
GENERATOR_VERSION = "0.1.0"

# One primary node kind per surface class; some classes also get a grapple anchor.
_KIND_BY_CLASS = {
    "walkable-hard": "stance",
    "walkable-soft": "stance",
    "walkable-narrow": "stance",
    "slope": "stance",
    "ledge": "hang",
    "overhang": "hang",
    "soft-hanging": "hang",
    "rung": "climb",
    "stud": "climb",
    "textured-vertical": "climb",
    "pole": "climb",
}
_ANCHOR_CLASSES = {"ledge", "overhang"}
_WALL_CLASSES = {"wall-smooth", "textured-vertical"}

# A walkable surface wider/longer than this (A) gets stance nodes near its edges as well
# as its centroid, so a neighbour near any part of it has a close jump-off point and a
# route can walk across it. Small surfaces keep a single centroid node.
_EDGE_NODE_MIN_SPAN = 3.0
_EDGE_INSET = 0.5


@dataclass
class _Node:
    id: str
    surface_id: str
    surface_class: str
    position: list[float]
    kind: str
    plantable: bool


def _horiz(a: list[float], b: list[float]) -> float:
    return ((a[0] - b[0]) ** 2 + (a[2] - b[2]) ** 2) ** 0.5


def _aabb_gap(a: dict, b: dict) -> float:
    """Horizontal edge-to-edge distance between two surface AABBs (0 if they overlap in
    x/z) — the true gap the avatar crosses, independent of where the nodes sit."""
    amin, amax = a["bounds"]["min"], a["bounds"]["max"]
    bmin, bmax = b["bounds"]["min"], b["bounds"]["max"]
    dx = max(0.0, amin[0] - bmax[0], bmin[0] - amax[0])
    dz = max(0.0, amin[2] - bmax[2], bmin[2] - amax[2])
    return (dx * dx + dz * dz) ** 0.5


def _extent(surface: dict) -> tuple[float, float]:
    b = surface["bounds"]
    return b["max"][0] - b["min"][0], b["max"][2] - b["min"][2]


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _stance_positions(s: dict) -> list[list[float]]:
    """Centroid plus edge-midpoint stance points on a large walkable surface."""
    b = s["bounds"]
    top = s["measurements"]["top_height_A"]
    cx, _, cz = s["centroid"]
    minx, maxx = b["min"][0], b["max"][0]
    minz, maxz = b["min"][2], b["max"][2]
    positions = [[cx, top, cz]]
    if maxx - minx > _EDGE_NODE_MIN_SPAN:
        positions.append([round(minx + _EDGE_INSET, 4), top, cz])
        positions.append([round(maxx - _EDGE_INSET, 4), top, cz])
    if maxz - minz > _EDGE_NODE_MIN_SPAN:
        positions.append([cx, top, round(minz + _EDGE_INSET, 4)])
        positions.append([cx, top, round(maxz - _EDGE_INSET, 4)])
    return positions


def _make_nodes(scene: dict) -> list[_Node]:
    nodes: list[_Node] = []
    n = 0
    for s in scene["surfaces"]:
        cls = s["class"]
        kind = _KIND_BY_CLASS.get(cls)
        top = s["measurements"]["top_height_A"]
        cx, cy, cz = s["centroid"]
        if kind == "stance":
            for pos in _stance_positions(s):
                n += 1
                nodes.append(_Node(f"node-{n}", s["id"], cls, pos, "stance", True))
        elif kind is not None:  # hang / climb — one node at the feature
            n += 1
            pos = [cx, top, cz] if kind == "hang" else [cx, cy, cz]
            nodes.append(_Node(f"node-{n}", s["id"], cls, pos, kind, False))
        if cls in _ANCHOR_CLASSES:
            n += 1
            nodes.append(_Node(f"node-{n}", s["id"], cls, [cx, top, cz], "anchor", False))
    return nodes


def _edge_dict(
    a: _Node, b: _Node, distance: float, rise: float, aff: affordances.Affordance
) -> dict:
    return {
        "from": a.id,
        "to": b.id,
        "verb": aff.verb,
        "tier": aff.tier,
        "distance_A": round(distance, 4),
        "rise_A": round(rise, 4),
        "margin_used": aff.margin_used,
        "cost": aff.cost,
        "prerequisites": aff.prerequisites,
    }


def build_traversal_graph(
    scene: dict,
    cfg: MovementConfig | None = None,
    config_path: Path | None = None,
    tools: frozenset | None = None,
) -> dict:
    """Return the traversal_graph document for ``scene`` (a scene_graph dict)."""
    cfg = cfg or movement.load(config_path)
    config_path = config_path or movement.DEFAULT_PATH
    tools = tools if tools is not None else frozenset({"grapple", "pole-vault"})

    nodes = _make_nodes(scene)
    if not nodes:
        raise ValueError("scene_graph has no traversable surfaces")
    surface_by_id = {s["id"]: s for s in scene["surfaces"]}

    # Walls available for wall-run, by their footprint, for the between-A-and-B test.
    walls = [
        s
        for s in scene["surfaces"]
        if s["class"] in _WALL_CLASSES and max(*_extent(s)) >= cfg.wallRun.minWallRunA
    ]

    max_reach = max(cfg.grapple.reachA, cfg.poleVault.maxGapA, cfg.jump.sprintDistance)
    max_rise = cfg.grapple.reachA + 1.0

    nodes_by_surface: dict[str, list[_Node]] = {}
    for nd in nodes:
        nodes_by_surface.setdefault(nd.surface_id, []).append(nd)

    centroid = {sid: surface_by_id[sid]["centroid"] for sid in nodes_by_surface}
    proposed: dict[tuple[str, str], dict] = {}

    # intra-surface locomotion: walking is free between stance nodes on one solid surface
    for group in nodes_by_surface.values():
        stances = [nd for nd in group if nd.kind == "stance"]
        for a in stances:
            for b in stances:
                if b is a:
                    continue
                distance = _horiz(a.position, b.position)
                rise = b.position[1] - a.position[1]
                ctx = Context(
                    from_kind="stance",
                    to_kind="stance",
                    to_class=b.surface_class,
                    same_surface=True,
                )
                aff = affordances.best_affordance(cfg, a.surface_class, distance, rise, ctx)
                if aff is not None:
                    proposed[(a.id, b.id)] = _edge_dict(a, b, distance, rise, aff)

    # inter-surface: one crossing per (surface pair, target-node kind). Distance is the
    # true edge-to-edge gap; endpoints are the node on A nearest B and, per kind, the
    # nearest B node (so a grapple still targets B's anchor, a jump its stance).
    for sa, ga in nodes_by_surface.items():
        run_up = min(max(*_extent(surface_by_id[sa])), 10.0)
        for sb, gb in nodes_by_surface.items():
            if sb == sa:
                continue
            gap = _aabb_gap(surface_by_id[sa], surface_by_id[sb])
            if gap > max_reach:
                continue
            a = min(ga, key=lambda na: _horiz(na.position, centroid[sb]))
            targets: dict[str, _Node] = {}
            for nb in gb:
                cur = targets.get(nb.kind)
                if cur is None or _horiz(a.position, nb.position) < _horiz(
                    a.position, cur.position
                ):
                    targets[nb.kind] = nb
            for b in targets.values():
                rise = b.position[1] - a.position[1]
                if abs(rise) > max_rise:
                    continue
                ctx = Context(
                    from_kind=a.kind,
                    to_kind=b.kind,
                    to_class=b.surface_class,
                    run_up_A=run_up,
                    wall_length_A=_wall_between(a.position, b.position, walls),
                    anchor_ledge_A=min(*_extent(surface_by_id[sb])) if b.kind == "anchor" else 0.0,
                    tool_available=tools,
                )
                aff = affordances.best_affordance(cfg, a.surface_class, gap, rise, ctx)
                if aff is not None:
                    proposed[(a.id, b.id)] = _edge_dict(a, b, gap, rise, aff)

    edges = []
    for i, ((fr, to), e) in enumerate(sorted(proposed.items()), start=1):
        e = dict(e)
        e["id"] = f"edge-{i}"
        e["commit"] = (to, fr) not in proposed  # no way back -> a commit point
        edges.append(
            {
                "id": e["id"],
                "from": e["from"],
                "to": e["to"],
                "verb": e["verb"],
                "tier": e["tier"],
                "distance_A": e["distance_A"],
                "rise_A": e["rise_A"],
                "margin_used": e["margin_used"],
                "cost": e["cost"],
                "commit": e["commit"],
                "prerequisites": e["prerequisites"],
            }
        )

    return {
        "schema_version": "1.0.0",
        "environment_id": scene["environment_id"],
        "generator": {"name": GENERATOR_NAME, "version": GENERATOR_VERSION},
        "movement": {"config_sha256": _sha256(config_path), "margin": movement.MARGIN},
        "nodes": [
            {
                "id": n.id,
                "surface_id": n.surface_id,
                "position": [round(p, 4) for p in n.position],
                "kind": n.kind,
                "plantable": n.plantable,
            }
            for n in nodes
        ],
        "edges": edges,
    }


def _wall_between(a: list[float], b: list[float], walls: list[dict]) -> float:
    """Length of the longest wall whose footprint lies within the A→B segment's
    horizontal bounding box (a coarse 'is there a wall to run along' test)."""
    lo_x, hi_x = min(a[0], b[0]), max(a[0], b[0])
    lo_z, hi_z = min(a[2], b[2]), max(a[2], b[2])
    best = 0.0
    for s in walls:
        bnd = s["bounds"]
        if bnd["min"][0] > hi_x or bnd["max"][0] < lo_x:
            continue
        if bnd["min"][2] > hi_z or bnd["max"][2] < lo_z:
            continue
        ex, ez = _extent(s)
        best = max(best, max(ex, ez))
    return best
