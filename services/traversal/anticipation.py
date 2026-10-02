"""#2 Anticipation planner (AUTH #043) — Brain-B reference.

Given a frozen ``traversal_graph`` and a selected route (ordered edge ids), emit per-edge
**anticipation hints** the Unity procedural layer uses to *telegraph* the next move — pre-reach a
hand toward the upcoming hold, lead the gaze, and pick the plant foot BEFORE contact. This is what
makes traversal read as fluid; we get it cheaply because Brain B already knows the whole route.

Derived, not stored — this mirrors ``reach.py`` (a reference/validator), so **nothing is added to
the frozen v1.0.0 schemas** (AUTH #037). Unity may recompute at runtime from the same
``traversal_graph`` or consume these hints; either way the behaviour matches this reference. Surface
*normals* for #5 are derived at runtime from the collision mesh (the graph carries ``surface_id`` +
``position`` only), so a hint names the ``surface_id`` and leaves the normal to Brain A.

Standard library only.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field

import affordances
import movement

Vec3 = tuple[float, float, float]


class AnticipationError(ValueError):
    """Raised when a route references a missing edge or the edges do not chain."""


# verb → anticipation category. Only *contact* verbs are telegraphed; pure locomotion is not.
_CATEGORY: dict[str, str] = {
    # locomotion (no discrete contact to anticipate)
    "walk": "loco",
    "jog": "loco",
    "run": "loco",
    "crouch": "loco",
    "balance-walk": "loco",
    "step-up": "loco",
    # jumps (ballistic; plant foot matters)
    "standing-jump": "jump",
    "running-jump": "jump",
    "sprint-jump": "jump",
    "precision-jump": "jump",
    "ledge-to-ledge": "jump",
    "wall-push": "jump",
    "tic-tac": "jump",
    # vaults (plant a hand, preserve speed)
    "hop-over": "vault",
    "vault": "vault",
    "speed-vault": "vault",
    "kong-vault": "vault",
    "lazy-vault": "vault",
    "pole-vault": "vault",
    # climbs / tool-anchored traversal (pre-reach a hand to the hold/anchor)
    "mantle": "climb",
    "climb-up": "climb",
    "rung-climb": "climb",
    "stud-climb": "climb",
    "free-climb": "climb",
    "pole-climb": "climb",
    "overhang-traverse": "climb",
    "ledge-shimmy": "climb",
    "wall-run": "climb",
    "grapple-swing": "climb",
    "grapple-ascend": "climb",
    "grapple-rappel": "climb",
    # descents (lead with the gaze; no hand pre-reach)
    "controlled-drop": "land",
    "hang-drop": "land",
    "slide": "land",
    "dive-roll": "land",
}

# Categories that get an anticipation hint, and those that pre-reach a hand.
ANTICIPATED = ("jump", "vault", "climb", "land")
_HAND_CONTACT = ("climb", "vault")
_PLANT_FOOT = ("jump", "vault")


@dataclass(frozen=True)
class AnticipationParams:
    """``movement.json.anticipation`` block (#2); defaults mirror the shipped file.
    ``maxConcurrentReaches`` stays ≤ the Bible §2 two-IK-chain budget."""

    leadTimeSec: dict[str, float] = field(
        default_factory=lambda: {"jump": 0.35, "vault": 0.30, "climb": 0.40, "land": 0.25}
    )
    reachStartDistA: float = 1.2
    gazeLeadSec: float = 0.5
    maxConcurrentReaches: int = 2

    @classmethod
    def from_movement_config(cls, cfg: movement.MovementConfig | None = None) -> AnticipationParams:
        """Build from ``movement.json.anticipation`` (loads ``config/movement.json`` by default)."""
        a = asdict((cfg if cfg is not None else movement.load()).anticipation)
        a["maxConcurrentReaches"] = int(a["maxConcurrentReaches"])
        return cls(**a)


DEFAULT_ANTICIPATION = AnticipationParams()


@dataclass(frozen=True)
class AnticipationHint:
    """One telegraphed move: where the next contact is, where to pre-reach and look, how early to
    start, and which foot leads."""

    edge_id: str
    from_node: str
    to_node: str
    verb: str
    tier: str
    category: str
    contact_point: Vec3  # where the avatar contacts the target node
    reach_target: Vec3  # hand pre-reach target (== contact_point in v1)
    surface_id: str  # target surface; Brain A raycasts it for the #5 normal
    look_at: Vec3  # gaze target: the next hold ahead, else this contact
    lead_time_s: float
    needs_hand: bool
    plant_foot: str  # "left" | "right" | "none"


def edge_ids_of_route(route: dict) -> list[str]:
    """Flatten a route's ``beats[].edge_ids`` into one ordered list (environment_spec shape)."""
    return [eid for beat in route.get("beats", []) for eid in beat.get("edge_ids", [])]


def _vec3(position: list) -> Vec3:
    x, y, z = position
    return (float(x), float(y), float(z))


def plan_anticipation(
    graph: dict, edge_ids: list[str], p: AnticipationParams = DEFAULT_ANTICIPATION
) -> list[AnticipationHint]:
    """Emit anticipation hints for the contact verbs along ``edge_ids`` (a route's ordered edges).

    Deterministic. Pure-locomotion edges produce no hint; the gaze leads to the *next* hold
    (the following edge's target), else the current contact. Raises
    :class:`AnticipationError` on an unknown edge id or a route whose edges do not chain.
    """
    nodes = {n["id"]: n for n in graph["nodes"]}
    edges = {e["id"]: e for e in graph["edges"]}

    for eid in edge_ids:
        if eid not in edges:
            raise AnticipationError(f"edge {eid!r} is not in the traversal graph")
    for a, b in zip(edge_ids, edge_ids[1:], strict=False):
        if edges[a]["to"] != edges[b]["from"]:
            raise AnticipationError(
                f"edges do not chain: {a} ends at {edges[a]['to']!r} but {b} starts at "
                f"{edges[b]['from']!r}"
            )

    hints: list[AnticipationHint] = []
    plant_count = 0
    for i, eid in enumerate(edge_ids):
        e = edges[eid]
        category = _CATEGORY.get(e["verb"], "loco")
        if category not in ANTICIPATED:
            continue
        target = nodes[e["to"]]
        contact = _vec3(target["position"])
        look_at = contact
        for nxt in edge_ids[i + 1 :]:
            look_at = _vec3(nodes[edges[nxt]["to"]]["position"])
            break
        if category in _PLANT_FOOT:
            plant = "left" if plant_count % 2 == 0 else "right"
            plant_count += 1
        else:
            plant = "none"
        hints.append(
            AnticipationHint(
                edge_id=eid,
                from_node=e["from"],
                to_node=e["to"],
                verb=e["verb"],
                tier=e["tier"],
                category=category,
                contact_point=contact,
                reach_target=contact,
                surface_id=target["surface_id"],
                look_at=look_at,
                lead_time_s=float(p.leadTimeSec[category]),
                needs_hand=category in _HAND_CONTACT,
                plant_foot=plant,
            )
        )
    return hints


def _unmapped_verbs() -> set[str]:
    """Tier-table verbs with no anticipation category — must be empty (a test guard)."""
    return set(affordances.VERB_TIER) - set(_CATEGORY)


if __name__ == "__main__":
    import json
    import sys
    from pathlib import Path

    if len(sys.argv) not in (3, 4):
        print("usage: python -m anticipation <traversal_graph.json> <environment_spec.json> [rank]")
        raise SystemExit(2)
    graph_doc = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    spec_doc = json.loads(Path(sys.argv[2]).read_text(encoding="utf-8"))
    rank = int(sys.argv[3]) if len(sys.argv) == 4 else 1
    route = next((r for r in spec_doc["routes"] if r["rank"] == rank), spec_doc["routes"][0])
    out = [h.__dict__ for h in plan_anticipation(graph_doc, edge_ids_of_route(route))]
    print(json.dumps(out, indent=2))
