"""Deterministic reachability validator (M1-SCEN-05).

Every generated route must pass this. It re-checks each transition against
``config/movement.json`` at the 85 % margin (never trusting the margin the graph wrote)
and enforces the route rules: segments chain, beat 1 uses only the T0 verb set, and a
tool may be required only if an earlier beat (never beat 1) taught it. All movement
numbers come through ``movement.MovementConfig`` and the shared affordance library, so
no constant is duplicated (AT-3). Identical input yields identical output (AT-1).

Standard library only.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import affordances
import movement
from affordances import Context
from movement import MovementConfig

T0_VERBS = frozenset(v for v, t in affordances.VERB_TIER.items() if t == "T0")


@dataclass(frozen=True)
class Beat:
    """One beat of a proposed route: the edges taken and the verb it teaches."""

    index: int
    edge_ids: tuple[str, ...]
    teaches: str | None = None


@dataclass
class SegmentResult:
    edge_id: str
    verb: str
    tier: str
    margin_used: float
    ok: bool
    reason: str = ""


@dataclass
class RouteResult:
    ok: bool
    segments: list[SegmentResult] = field(default_factory=list)
    problems: list[str] = field(default_factory=list)


def _ctx_from_edge(edge: dict) -> Context:
    pre = edge.get("prerequisites", {})
    return Context(
        run_up_A=pre.get("run_up_A", 0.0),
        wall_length_A=pre.get("wall_length_A", 0.0),
        anchor_ledge_A=pre.get("anchor_ledge_A", 0.0),
        tool_available=frozenset({pre["tool"]}) if "tool" in pre else frozenset(),
    )


def check_transition(cfg: MovementConfig, edge: dict) -> tuple[float | None, bool, str]:
    """Recompute the edge's reachability from movement.json. Returns
    (margin, ok, reason). ok is False if the verb cannot apply or exceeds 85 %."""
    verb = edge["verb"]
    if affordances.VERB_TIER.get(verb) != edge["tier"]:
        return None, False, f"tier {edge['tier']} does not match verb {verb}"
    margin = affordances.verb_margin(
        cfg, verb, edge["distance_A"], edge["rise_A"], _ctx_from_edge(edge)
    )
    if margin is None:
        return None, False, f"{verb} cannot apply to this transition"
    if margin > movement.MARGIN:
        return margin, False, f"needs {margin:.2f} of max, over the {movement.MARGIN} margin"
    return margin, True, ""


def validate_edge(cfg: MovementConfig, edge: dict) -> SegmentResult:
    margin, ok, reason = check_transition(cfg, edge)
    return SegmentResult(
        edge_id=edge["id"],
        verb=edge["verb"],
        tier=edge["tier"],
        margin_used=round(margin, 4) if margin is not None else -1.0,
        ok=ok,
        reason=reason,
    )


def validate_route(
    graph: dict,
    beats: list[Beat],
    cfg: MovementConfig | None = None,
    spawn_node: str | None = None,
    summit_node: str | None = None,
    available_tools: frozenset = frozenset(),
) -> RouteResult:
    """Validate a proposed route (ordered beats of edge ids) against ``graph``."""
    cfg = cfg or movement.load()
    edges = {e["id"]: e for e in graph["edges"]}
    result = RouteResult(ok=True)

    # Which beat first teaches each tool (via a taught verb that needs one).
    tool_taught_at: dict[str, int] = {}
    for beat in beats:
        if beat.teaches and beat.teaches in affordances.TOOL_OF_VERB:
            tool = affordances.TOOL_OF_VERB[beat.teaches]
            tool_taught_at.setdefault(tool, beat.index)
            if beat.index == 1:
                result.ok = False
                result.problems.append(
                    f"beat 1 teaches tool verb {beat.teaches}; tools are never beat 1"
                )

    path: list[dict] = []
    for beat in beats:
        for eid in beat.edge_ids:
            edge = edges.get(eid)
            if edge is None:
                result.problems.append(f"beat {beat.index}: unknown edge {eid}")
                result.ok = False
                continue
            seg = validate_edge(cfg, edge)
            result.segments.append(seg)
            if not seg.ok:
                result.ok = False
                result.problems.append(f"beat {beat.index} {eid}: {seg.reason}")
            if beat.index == 1 and edge["verb"] not in T0_VERBS:
                result.ok = False
                result.problems.append(f"beat 1 {eid}: {edge['verb']} is not a T0 verb")
            tool = edge.get("prerequisites", {}).get("tool")
            if tool is not None and tool not in available_tools:
                taught = tool_taught_at.get(tool)
                if taught is None:
                    result.ok = False
                    result.problems.append(
                        f"beat {beat.index} {eid}: tool {tool} required but never taught"
                    )
                elif taught >= beat.index:
                    result.ok = False
                    result.problems.append(
                        f"beat {beat.index} {eid}: tool {tool} used before taught (beat {taught})"
                    )
            path.append(edge)

    # Segments must chain end-to-end.
    for a, b in zip(path, path[1:], strict=False):
        if a["to"] != b["from"]:
            result.ok = False
            result.problems.append(f"path breaks between {a['id']} and {b['id']}")

    if path:
        if spawn_node is not None and path[0]["from"] != spawn_node:
            result.ok = False
            result.problems.append(f"route does not start at spawn {spawn_node}")
        if summit_node is not None and path[-1]["to"] != summit_node:
            result.ok = False
            result.problems.append(f"route does not reach summit {summit_node}")
    elif summit_node is not None:
        result.ok = False
        result.problems.append("empty route cannot reach the summit")

    return result
