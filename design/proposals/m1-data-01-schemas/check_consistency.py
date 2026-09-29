"""Cross-document checks JSON Schema cannot express (M1-DATA-01 proposal).

Given one environment's scene_graph, traversal_graph and environment_spec, return a list of
problems (empty = consistent). This is the reference the M1-SCEN-05 validator and the Unity
loader (M1-GAME-01) agree on; it does not re-run reachability (that is M1-SCEN-05).

Usage: python check_consistency.py scene_graph.json traversal_graph.json environment_spec.json
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

TIER_ORDER = {"T0": 0, "T1": 1, "T2": 2, "T3": 3}
TOOL_OF_VERB = {
    "grapple-swing": "grapple",
    "grapple-ascend": "grapple",
    "grapple-rappel": "grapple",
    "pole-vault": "pole-vault",
    "wall-run": "wall-run",
}


def _dupes(ids: list[str]) -> set[str]:
    seen: set[str] = set()
    return {i for i in ids if i in seen or seen.add(i)}


def check(scene: dict, graph: dict, spec: dict) -> list[str]:
    problems: list[str] = []
    env_ids = {scene["environment_id"], graph["environment_id"], spec["environment_id"]}
    if len(env_ids) != 1:
        problems.append(f"environment_id differs across documents: {sorted(env_ids)}")
    if scene["scale"]["multiplier"] != spec["scale_multiplier"]:
        problems.append("scale_multiplier differs from scene_graph.scale.multiplier")
    if scene["capture_mode"] != spec["capture_mode"]:
        problems.append("capture_mode differs between scene_graph and environment_spec")
    sha = graph["movement"]["config_sha256"]
    if spec["generation"]["validator"]["movement_config_sha256"] != sha:
        problems.append(
            "environment_spec validated against a different movement.json than the traversal graph"
        )

    surfaces = {s["id"]: s for s in scene["surfaces"]}
    nodes = {n["id"]: n for n in graph["nodes"]}
    edges = {e["id"]: e for e in graph["edges"]}
    for label, ids in (
        ("surface", [s["id"] for s in scene["surfaces"]]),
        ("node", [n["id"] for n in graph["nodes"]]),
        ("edge", [e["id"] for e in graph["edges"]]),
        ("route", [r["id"] for r in spec["routes"]]),
        ("vista", [v["id"] for v in spec["vistas"]]),
    ):
        for d in sorted(_dupes(ids)):
            problems.append(f"duplicate {label} id {d}")

    if scene["spawn"]["surface_id"] not in surfaces:
        problems.append(f"spawn surface {scene['spawn']['surface_id']} not in scene_graph")
    for n in graph["nodes"]:
        s = surfaces.get(n["surface_id"])
        if s is None:
            problems.append(f"{n['id']}: surface {n['surface_id']} not in scene_graph")
        elif s["class"] == "void":
            problems.append(f"{n['id']}: stands on a void surface")
    for e in graph["edges"]:
        for end in ("from", "to"):
            if e[end] not in nodes:
                problems.append(f"{e['id']}: {end} node {e[end]} not in traversal_graph")

    for key in ("spawn", "summit"):
        if spec[key]["node_id"] not in nodes:
            problems.append(f"{key} node {spec[key]['node_id']} not in traversal_graph")
    summit = nodes.get(spec["summit"]["node_id"])
    if summit is not None and not summit["plantable"]:
        problems.append("summit node is not plantable")

    ranks = sorted(r["rank"] for r in spec["routes"])
    if ranks != list(range(1, len(ranks) + 1)):
        problems.append(f"route ranks must be 1..{len(ranks)}, got {ranks}")
    for route in sorted(spec["routes"], key=lambda r: r["rank"]):
        problems.extend(_check_route(route, edges, spec))
    by_rank = sorted(spec["routes"], key=lambda r: r["rank"])
    for a, b in zip(by_rank, by_rank[1:], strict=False):
        if a["global_difficulty"] > b["global_difficulty"]:
            problems.append(
                f"{b['id']}: ranked harder than {a['id']} but has a lower global_difficulty"
            )

    for v in spec["vistas"]:
        if v["node_id"] not in nodes:
            problems.append(f"{v['id']}: node {v['node_id']} not in traversal_graph")
    return problems


def _check_route(route: dict, edges: dict, spec: dict) -> list[str]:
    rid = route["id"]
    problems: list[str] = []
    path: list[dict] = []
    for beat in route["beats"]:
        beat_edges = [edges.get(e) for e in beat["edge_ids"]]
        if any(e is None for e in beat_edges):
            missing = [i for i, e in zip(beat["edge_ids"], beat_edges, strict=True) if e is None]
            problems.append(f"{rid} beat {beat['index']}: unknown edges {missing}")
            return problems
        top = max(TIER_ORDER[e["tier"]] for e in beat_edges)
        if TIER_ORDER[beat["max_tier"]] != top:
            problems.append(
                f"{rid} beat {beat['index']}: max_tier {beat['max_tier']} but edges reach T{top}"
            )
        if beat["teaches"] is not None and beat["teaches"] not in {e["verb"] for e in beat_edges}:
            problems.append(
                f"{rid} beat {beat['index']}: teaches {beat['teaches']} but never uses it"
            )
        path.extend(beat_edges)
    if [b["index"] for b in route["beats"]] != list(range(1, len(route["beats"]) + 1)):
        problems.append(f"{rid}: beat indexes must be consecutive from 1")
    if path[0]["from"] != spec["spawn"]["node_id"]:
        problems.append(f"{rid}: does not start at the spawn node")
    if path[-1]["to"] != spec["summit"]["node_id"]:
        problems.append(f"{rid}: does not end at the summit node")
    for a, b in zip(path, path[1:], strict=False):
        if a["to"] != b["from"]:
            problems.append(f"{rid}: path breaks between {a['id']} and {b['id']}")
    if max(TIER_ORDER[e["tier"]] for e in path) != TIER_ORDER[route["highest_tier"]]:
        problems.append(f"{rid}: highest_tier does not match its edges")
    if abs(max(e["margin_used"] for e in path) - route["tightest_margin"]) > 1e-9:
        problems.append(f"{rid}: tightest_margin does not match its edges")
    t2 = {e["verb"] for e in path if TIER_ORDER[e["tier"]] >= 2}
    if len(t2) != route["distinct_t2plus_verbs"]:
        problems.append(
            f"{rid}: distinct_t2plus_verbs {route['distinct_t2plus_verbs']} but path has {len(t2)}"
        )
    if sum(1 for e in path if e["commit"]) != route["commit_points"]:
        problems.append(f"{rid}: commit_points does not match its edges")
    tools = {TOOL_OF_VERB[e["verb"]] for e in path if e["verb"] in TOOL_OF_VERB}
    tool = route["required_tool"]
    if tool is None and tools and route["rank"] == 1:
        problems.append(
            f"{rid}: the easiest route uses a tool ({sorted(tools)}) "
            "without declaring required_tool"
        )
    if tool is not None:
        if tool not in tools:
            problems.append(f"{rid}: required_tool {tool} is never used")
        taught = [
            b["index"]
            for b in route["beats"]
            if b["teaches"] and TOOL_OF_VERB.get(b["teaches"]) == tool
        ]
        first_use = (
            min(
                b["index"]
                for b in route["beats"]
                for e in b["edge_ids"]
                if TOOL_OF_VERB.get(edges[e]["verb"]) == tool
            )
            if tool in tools
            else None
        )
        if not taught or (first_use is not None and min(taught) > first_use) or 1 in taught:
            problems.append(
                f"{rid}: required_tool {tool} must be taught in beat 2+ before it is required"
            )
    return problems


def main(argv: list[str]) -> int:
    if len(argv) != 3:
        print(__doc__)
        return 2
    docs = [json.loads(Path(p).read_text(encoding="utf-8")) for p in argv]
    problems = check(*docs)
    for p in problems:
        print(f"inconsistent: {p}")
    print("consistent" if not problems else f"{len(problems)} problem(s)")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
