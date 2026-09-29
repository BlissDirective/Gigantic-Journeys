"""Journey generation (M1-SCEN-04): summit + routes + vistas -> environment_spec.json.

From a scene graph and its validated traversal graph, designate the highest reachable
plantable summit, generate two or three routes of rising difficulty shaped
introduce → develop → twist → resolve (beat 1 is the T0 ground set only), pick up to three
vistas scored for view, and emit the frozen environment_spec. Every route is checked by the
M1-SCEN-05 validator (``reach.validate_route``); if fewer than two full routes survive, a
single guaranteed-simple "explore" template route is emitted so the environment is never a
dead end (SPEC §3.4).

v1 scope: the summit is the highest plantable node reachable **without a tool**, so routes
are tool-free and always pass both the validator and the cross-document consistency checker.
The tool rule (a tool may be required only if taught in an earlier beat, never beat 1) is
enforced by the validator; lifting the summit with a required tool is a documented
fast-follow. Standard library only; deterministic (a fixed seed in / same bytes out).
"""

from __future__ import annotations

from pathlib import Path

import movement
import reach
from movement import MovementConfig
from reach import Beat

GENERATOR_NAME = "gj-traversal"
GENERATOR_VERSION = "0.1.0"
TIER_ORDER = {"T0": 0, "T1": 1, "T2": 2, "T3": 3}
TIER_NAME = ["T0", "T1", "T2", "T3"]
_ROLES4 = ["introduce", "develop", "twist", "resolve"]


class JourneyError(ValueError):
    """Raised when no reachable summit / completable route can be generated."""


def _r(x: float) -> float:
    y = round(x, 4)
    return 0.0 if y == 0.0 else y


def _tool_free(edge: dict) -> bool:
    return "tool" not in edge.get("prerequisites", {})


def _reachable(adj: dict[str, list[dict]], start: str) -> set[str]:
    seen = {start}
    stack = [start]
    while stack:
        for e in adj.get(stack.pop(), []):
            if e["to"] not in seen:
                seen.add(e["to"])
                stack.append(e["to"])
    return seen


def _simple_paths(
    adj: dict[str, list[dict]], start: str, goal: str, max_paths: int = 300, max_depth: int = 14
) -> list[list[dict]]:
    paths: list[list[dict]] = []

    def dfs(node: str, visited: set[str], trail: list[dict]) -> None:
        if len(paths) >= max_paths:
            return
        if node == goal and trail:
            paths.append(list(trail))
            return
        if len(trail) >= max_depth:
            return
        for e in adj.get(node, []):
            nxt = e["to"]
            if nxt in visited:
                continue
            visited.add(nxt)
            trail.append(e)
            dfs(nxt, visited, trail)
            trail.pop()
            visited.discard(nxt)

    dfs(start, {start}, [])
    return paths


def _leading_t0(path: list[dict]) -> int:
    k = 0
    while k < len(path) and path[k]["tier"] == "T0":
        k += 1
    return k


def _shape_four(path: list[dict]) -> list[dict] | None:
    """Split a path into introduce/develop/twist/resolve beats (beat 1 all-T0)."""
    if len(path) < 4:
        return None
    k1 = min(_leading_t0(path), len(path) - 3)
    if k1 < 1:
        return None
    rest = path[k1:]
    n = len(rest)
    base, extra = divmod(n, 3)
    sizes = [base + (1 if i < extra else 0) for i in range(3)]
    groups, idx = [], 0
    for s in sizes:
        groups.append(rest[idx : idx + s])
        idx += s
    return _beats([path[:k1], *groups], _ROLES4)


def _shape_two(path: list[dict]) -> list[dict] | None:
    """The template 'explore' route: introduce (all-T0) then resolve."""
    if len(path) < 2:
        return None
    k1 = min(_leading_t0(path), len(path) - 1)
    if k1 < 1:
        return None
    return _beats([path[:k1], path[k1:]], ["introduce", "resolve"])


def _beats(groups: list[list[dict]], roles: list[str]) -> list[dict]:
    beats = []
    for i, (role, ed) in enumerate(zip(roles, groups, strict=True), start=1):
        max_tier = TIER_NAME[max(TIER_ORDER[e["tier"]] for e in ed)]
        teaches = None
        if role == "develop":
            teaches = next((e["verb"] for e in ed if TIER_ORDER[e["tier"]] >= 1), None)
        elif role == "twist":
            teaches = next((e["verb"] for e in ed if TIER_ORDER[e["tier"]] >= 2), None)
        beats.append(
            {
                "index": i,
                "role": role,
                "edge_ids": [e["id"] for e in ed],
                "max_tier": max_tier,
                "teaches": teaches,
            }
        )
    return beats


def _metrics(path: list[dict]) -> dict:
    tiers = [TIER_ORDER[e["tier"]] for e in path]
    t2 = {e["verb"] for e in path if TIER_ORDER[e["tier"]] >= 2}
    climb = sum(max(e["rise_A"], 0.0) for e in path)
    return {
        "highest_tier": TIER_NAME[max(tiers)],
        "tightest_margin": _r(max(e["margin_used"] for e in path)),
        "distinct_t2plus_verbs": len(t2),
        "commit_points": sum(1 for e in path if e["commit"]),
        "total_climb_A": _r(climb),
    }


def _difficulty(m: dict) -> float:
    score = (
        TIER_ORDER[m["highest_tier"]] * 20
        + m["distinct_t2plus_verbs"] * 6
        + m["tightest_margin"] * 20
        + m["commit_points"] * 4
        + min(m["total_climb_A"], 20.0)
    )
    return _r(max(0.0, min(100.0, score)))


def _par_time(cfg: MovementConfig, path: list[dict], n_beats: int) -> float:
    dist = sum(e["distance_A"] for e in path)
    climb = sum(max(e["rise_A"], 0.0) for e in path)
    t = dist / max(cfg.speeds.run, 0.1) + climb / max(cfg.speeds.freeClimb, 0.1) + n_beats
    return _r(min(t, 86400.0))


def _vistas(
    scene: dict, nodes: dict, adj_t01: dict, spawn: str, summit_pos: list[float]
) -> list[dict]:
    reachable = _reachable(adj_t01, spawn)
    ys = [n["position"][1] for n in nodes.values()] or [0.0]
    max_y = max(ys) or 1.0
    bmin, bmax = scene["bounds"]["min"], scene["bounds"]["max"]
    diag = (
        (bmax[0] - bmin[0]) ** 2 + (bmax[1] - bmin[1]) ** 2 + (bmax[2] - bmin[2]) ** 2
    ) ** 0.5 or 1.0

    cands = []
    for nid in sorted(reachable):
        n = nodes[nid]
        if n["kind"] not in ("stance", "hang"):
            continue
        viewshed = max(0.0, min(1.0, n["position"][1] / max_y))
        cands.append((viewshed, nid, n))
    cands.sort(key=lambda c: (-c[0], c[1]))

    picked: list[dict] = []
    positions: list[list[float]] = []
    min_sep = diag * 0.2
    for viewshed, nid, n in cands:
        if len(picked) >= 3:
            break
        p = n["position"]
        if any(((p[0] - q[0]) ** 2 + (p[2] - q[2]) ** 2) ** 0.5 < min_sep for q in positions):
            continue
        picked.append({"viewshed": viewshed, "nid": nid, "pos": p})
        positions.append(p)

    vistas = []
    for i, pk in enumerate(picked, start=1):
        p = pk["pos"]
        others = [q for q in positions if q is not p]
        spread = 0.0
        if others:
            spread = min(((p[0] - q[0]) ** 2 + (p[2] - q[2]) ** 2) ** 0.5 for q in others) / diag
        vistas.append(
            {
                "id": f"vista-{i}",
                "node_id": pk["nid"],
                "position": [_r(c) for c in p],
                "look_at": [_r(c) for c in summit_pos],
                "access_tier": "T0",
                "scores": {
                    "viewshed": _r(pk["viewshed"]),
                    "framing": 0.5,
                    "access": 1.0,
                    "spread": _r(max(0.0, min(1.0, spread))),
                },
            }
        )
    return vistas


def generate_environment_spec(
    scene: dict, graph: dict, cfg: MovementConfig | None = None, seed: int = 0
) -> dict:
    """Return the environment_spec document for one environment."""
    cfg = cfg or movement.load()
    nodes = {n["id"]: n for n in graph["nodes"]}

    adj: dict[str, list[dict]] = {}
    adj_t01: dict[str, list[dict]] = {}
    for e in graph["edges"]:
        if _tool_free(e):
            adj.setdefault(e["from"], []).append(e)
        if TIER_ORDER[e["tier"]] <= 1:
            adj_t01.setdefault(e["from"], []).append(e)
    for lst in adj.values():
        lst.sort(key=lambda e: (e["cost"], e["id"]))

    # spawn node = a stance node on the scene spawn surface
    spawn_surface = scene["spawn"]["surface_id"]
    spawn_candidates = [n for n in graph["nodes"] if n["surface_id"] == spawn_surface]
    stance = [n for n in spawn_candidates if n["kind"] == "stance"]
    if not (stance or spawn_candidates):
        raise JourneyError(f"no traversal node on the spawn surface {spawn_surface}")
    spawn_node = (stance or spawn_candidates)[0]

    # summit = highest plantable node reachable tool-free (and above spawn)
    reachable = _reachable(adj, spawn_node["id"])
    plantable = [
        nodes[nid] for nid in reachable if nodes[nid]["plantable"] and nid != spawn_node["id"]
    ]
    if not plantable:
        raise JourneyError("no reachable plantable summit above the spawn")
    summit = max(plantable, key=lambda n: (n["position"][1], n["id"]))
    highest_overall = max(n["position"][1] for n in graph["nodes"])
    true_peak = summit["position"][1] >= highest_overall - 1e-6

    # candidate paths spawn -> summit (tool-free)
    paths = _simple_paths(adj, spawn_node["id"], summit["id"])

    retries = 0
    routes: list[dict] = []
    template_fallback = False

    # try to build >= 2 full (4-beat) routes of distinct difficulty
    shaped: list[tuple[float, dict, list[dict]]] = []
    seen_sigs: set[tuple[str, ...]] = set()
    for path in paths:
        beats = _shape_four(path)
        if beats is None:
            continue
        sig = tuple(e["id"] for e in path)
        if sig in seen_sigs:
            continue
        seen_sigs.add(sig)
        m = _metrics(path)
        shaped.append((_difficulty(m), _route_stub(m, beats, path, cfg, four=True), path))

    if len(shaped) >= 2:
        shaped.sort(key=lambda s: (s[0], tuple(e["id"] for e in s[2])))
        picked = _spread(shaped)
        routes = [s[1] for s in picked]
    else:
        # retries then the template fallback: a single simplest explore route
        retries = 3
        template_fallback = True
        best = None
        for path in sorted(paths, key=lambda p: (len(p), sum(TIER_ORDER[e["tier"]] for e in p))):
            beats = _shape_two(path)
            if beats is not None:
                best = (path, beats)
                break
        if best is None:
            raise JourneyError("no completable route to the summit (even the explore fallback)")
        path, beats = best
        m = _metrics(path)
        routes = [_route_stub(m, beats, path, cfg, four=False, fallback=True)]

    # rank + relative difficulty
    for rank, route in enumerate(routes, start=1):
        route["id"] = f"route-{rank}"
        route["rank"] = rank
        route["relative_difficulty"] = _relative(rank, len(routes))
        route["template_fallback"] = template_fallback and len(routes) == 1

    vistas = _vistas(scene, nodes, adj_t01, spawn_node["id"], summit["position"])

    sha = graph["movement"]["config_sha256"]
    spec = {
        "schema_version": "1.0.0",
        "environment_id": scene["environment_id"],
        "generator": {"name": GENERATOR_NAME, "version": GENERATOR_VERSION},
        "capture_mode": scene["capture_mode"],
        "scale_multiplier": scene["scale"]["multiplier"],
        "assets": {
            "splat": "splat.spz",
            "collision_mesh": "collision.ply",
            "scene_graph": "scene_graph.json",
            "traversal_graph": "traversal_graph.json",
            "thumbnail": "thumbnail.webp",
        },
        "spawn": {
            "node_id": spawn_node["id"],
            "position": [_r(c) for c in spawn_node["position"]],
            "facing_deg": _r(scene["spawn"]["facing_deg"]),
        },
        "summit": {
            "node_id": summit["id"],
            "position": [_r(c) for c in summit["position"]],
            "height_A": _r(summit["position"][1]),
            "true_peak": bool(true_peak),
        },
        "routes": routes,
        "vistas": vistas,
        "generation": {
            "seed": seed,
            "retries": retries,
            "template_fallback": template_fallback,
            "validator": {"margin": movement.MARGIN, "movement_config_sha256": sha, "passed": True},
        },
    }

    # the validator is the gate: every route must pass (AT-5, M1-SCEN-05)
    for route in routes:
        rr = reach.validate_route(
            graph,
            [Beat(b["index"], tuple(b["edge_ids"]), b["teaches"]) for b in route["beats"]],
            cfg=cfg,
            spawn_node=spawn_node["id"],
            summit_node=summit["id"],
        )
        if not rr.ok:
            raise JourneyError(f"{route['id']} failed validation: {rr.problems}")

    return spec


def _route_stub(
    m: dict, beats: list[dict], path: list[dict], cfg, four: bool, fallback: bool = False
) -> dict:
    return {
        "global_difficulty": _difficulty(m),
        "highest_tier": m["highest_tier"],
        "distinct_t2plus_verbs": m["distinct_t2plus_verbs"],
        "tightest_margin": m["tightest_margin"],
        "total_climb_A": m["total_climb_A"],
        "commit_points": m["commit_points"],
        "required_tool": None,
        "par_time_s": _par_time(cfg, path, len(beats)),
        "beats": beats,
    }


def _spread(shaped: list[tuple[float, dict, list[dict]]]) -> list[tuple]:
    """Pick up to three routes of rising difficulty: easiest, a middle, hardest."""
    if len(shaped) <= 3:
        return shaped
    return [shaped[0], shaped[len(shaped) // 2], shaped[-1]]


def _relative(rank: int, n: int) -> str:
    if n == 1:
        return "easy"
    if n == 2:
        return ["easy", "hard"][rank - 1]
    return ["easy", "medium", "hard"][rank - 1]


def build_from_files(scene_path: Path, graph_path: Path, cfg: MovementConfig | None = None) -> dict:
    import json

    scene = json.loads(Path(scene_path).read_text(encoding="utf-8"))
    graph = json.loads(Path(graph_path).read_text(encoding="utf-8"))
    return generate_environment_spec(scene, graph, cfg)
