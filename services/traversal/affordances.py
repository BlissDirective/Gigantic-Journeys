"""The affordance library (M1-SCEN-03): the one place that maps Bible §4 surface
classes to traversal verbs and scores each verb's reachability against
``config/movement.json``.

This module is imported by BOTH the traversal-graph export (``graph.py``, M1-SCEN-03)
and the reachability validator (``reach.py``, M1-SCEN-05), so the class→verb matrix,
the verb→tier table, and the per-verb reach model exist exactly once (M1-SCEN-03 AT-3;
M1-SCEN-05 AT-3 — no movement number is duplicated, every constant comes from
``movement.MovementConfig``). Tool verbs (grapple, pole-vault, wall-run) are ordinary
entries here with their movement.json prerequisites (M1-SCEN-03 AT-4).

Standard library only.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import movement
from movement import MovementConfig

# Verb -> difficulty tier (SPEC §3.4). Mirrors the traversal_graph schema's verb/tier
# allOf exactly; the schema is the freeze, this is the code that must agree with it.
VERB_TIER: dict[str, str] = {
    # T0
    "walk": "T0",
    "jog": "T0",
    "run": "T0",
    "step-up": "T0",
    "hop-over": "T0",
    "mantle": "T0",
    "standing-jump": "T0",
    "running-jump": "T0",
    "crouch": "T0",
    # T1
    "sprint-jump": "T1",
    "balance-walk": "T1",
    "vault": "T1",
    "speed-vault": "T1",
    "kong-vault": "T1",
    "lazy-vault": "T1",
    "precision-jump": "T1",
    "controlled-drop": "T1",
    "hang-drop": "T1",
    "slide": "T1",
    "dive-roll": "T1",
    # T2
    "ledge-shimmy": "T2",
    "climb-up": "T2",
    "rung-climb": "T2",
    "stud-climb": "T2",
    "free-climb": "T2",
    "pole-climb": "T2",
    "overhang-traverse": "T2",
    "ledge-to-ledge": "T2",
    "wall-push": "T2",
    "tic-tac": "T2",
    # T3
    "wall-run": "T3",
    "grapple-swing": "T3",
    "grapple-ascend": "T3",
    "grapple-rappel": "T3",
    "pole-vault": "T3",
}

# Traversal tool a verb needs (AUTH #021), mirrored from the schema.
TOOL_OF_VERB: dict[str, str] = {
    "grapple-swing": "grapple",
    "grapple-ascend": "grapple",
    "grapple-rappel": "grapple",
    "pole-vault": "pole-vault",
}

# Bible §4 class -> the verbs a transition *leaving* a surface of that class may use.
# The graph export only proposes a verb for an edge if it is enabled for the source
# surface's class (M1-SCEN-03 AT-2).
CLASS_VERBS: dict[str, tuple[str, ...]] = {
    "walkable-hard": (
        "walk",
        "jog",
        "run",
        "step-up",
        "hop-over",
        "mantle",
        "standing-jump",
        "running-jump",
        "sprint-jump",
        "precision-jump",
        "vault",
        "speed-vault",
        "kong-vault",
        "lazy-vault",
        "controlled-drop",
        "hang-drop",
        "dive-roll",
        "slide",
        "wall-run",
        "grapple-swing",
        "grapple-ascend",
        "pole-vault",
    ),
    "walkable-soft": (
        "walk",
        "jog",
        "run",
        "step-up",
        "hop-over",
        "mantle",
        "standing-jump",
        "running-jump",
        "sprint-jump",
        "precision-jump",
        "controlled-drop",
        "hang-drop",
        "dive-roll",
        "grapple-swing",
        "grapple-ascend",
    ),
    "walkable-narrow": (
        "balance-walk",
        "walk",
        "step-up",
        "standing-jump",
        "precision-jump",
        "controlled-drop",
        "hang-drop",
        "grapple-ascend",
    ),
    "ledge": (
        "ledge-shimmy",
        "ledge-to-ledge",
        "climb-up",
        "mantle",
        "hang-drop",
        "controlled-drop",
        "grapple-ascend",
        "grapple-rappel",
    ),
    "rung": ("rung-climb", "climb-up", "hang-drop"),
    "stud": ("stud-climb", "climb-up", "hang-drop"),
    "textured-vertical": (
        "free-climb",
        "climb-up",
        "wall-push",
        "tic-tac",
        "wall-run",
        "hang-drop",
    ),
    "pole": ("pole-climb", "controlled-drop"),
    "overhang": ("overhang-traverse", "hang-drop", "grapple-rappel"),
    "slope": ("slide", "run", "walk", "controlled-drop"),
    "wall-smooth": ("wall-run", "tic-tac", "wall-push"),
    "soft-hanging": ("free-climb", "overhang-traverse", "hang-drop"),
    "void": (),
    "hazard-none": (),
}

# Prerequisite keys each verb must record on its edge (mirrors the schema allOf).
REQUIRED_PREREQS: dict[str, tuple[str, ...]] = {
    "grapple-swing": ("tool", "anchor_ledge_A"),
    "grapple-ascend": ("tool", "anchor_ledge_A"),
    "grapple-rappel": ("tool", "anchor_ledge_A"),
    "pole-vault": ("tool", "min_speed_A_s", "plant_window_s"),
    "wall-run": ("min_speed_A_s", "wall_length_A"),
    "dive-roll": ("min_speed_A_s",),
}

TIER_COST = {"T0": 1.0, "T1": 2.5, "T2": 4.0, "T3": 7.0}

# Horizontal gap (A units) up to which two surfaces count as adjacent — you step
# across rather than jump. ``distance_A`` passed to a verb is the edge-to-edge gap.
WALK_GAP = 0.5


@dataclass(frozen=True)
class Context:
    """What a candidate transition knows beyond horizontal distance and rise."""

    from_kind: str = "stance"  # node kind the edge leaves
    to_kind: str = "stance"  # node kind the edge enters
    to_class: str = "walkable-hard"  # target surface class
    run_up_A: float = 0.0  # straight run-up available before take-off
    wall_length_A: float = 0.0  # length of a usable wall for wall-run/tic-tac
    anchor_ledge_A: float = 0.0  # depth of the grapple anchor ledge at the target
    tool_available: frozenset = field(default_factory=frozenset)  # {"grapple","pole-vault"}


def tier_of(verb: str) -> str:
    return VERB_TIER[verb]


def _both(a: float, b: float) -> float:
    """Binding fraction of two independent constraints."""
    return max(a, b)


def verb_margin(
    cfg: MovementConfig, verb: str, distance_A: float, rise_A: float, ctx: Context
) -> float | None:
    """Fraction of the movement.json maximum a transition needs by ``verb``, or None
    if the verb cannot geometrically apply to this transition. ``ok`` is decided by
    the caller (``<= movement.MARGIN``). Every bound comes from ``cfg``."""
    up = rise_A
    drop = -rise_A
    j = cfg.jump
    v = cfg.verticals
    near = distance_A <= cfg.reach.holdReach

    # --- locomotion: level, adjacent surfaces (small gap, no step) ---
    if verb in ("walk", "jog", "run", "balance-walk"):
        if distance_A <= WALK_GAP and abs(rise_A) <= v.stepUp:
            return 0.0
        return None

    # --- small vertical gains ---
    if verb == "step-up":
        return up / v.stepUp if 0.0 <= up and near else None
    if verb == "hop-over":
        return (
            _both(abs(rise_A) / v.hopOver, distance_A / (v.hopOver * 2))
            if abs(rise_A) <= v.hopOver
            else None
        )
    if verb == "mantle":
        return up / v.mantle if 0.0 <= up and near else None
    if verb in ("vault", "speed-vault", "kong-vault", "lazy-vault"):
        return up / v.vault if 0.0 <= up <= v.vault and distance_A <= v.vault * 2 else None

    # --- jumps --- (a jump may gain height or cross a gap and land a little lower; the
    # landing drop is bounded by landing tolerance. A descent with no gap to clear is a
    # drop, not a jump, and a big drop is a fall.)
    drop_term = drop / cfg.landing.hard if drop > 0.0 else 0.0
    no_gap_descent = distance_A <= WALK_GAP and rise_A < 0.0
    if verb == "standing-jump":
        if up > j.standingHeight or no_gap_descent:
            return None
        return max(max(up, 0.0) / j.standingHeight, distance_A / j.standingDistance, drop_term)
    if verb == "running-jump":
        if up > j.runningHeight or no_gap_descent:
            return None
        return max(max(up, 0.0) / j.runningHeight, distance_A / j.runningDistance, drop_term)
    if verb == "sprint-jump":
        if up > j.runningHeight or no_gap_descent:
            return None
        return max(max(up, 0.0) / j.runningHeight, distance_A / j.sprintDistance, drop_term)
    if verb == "precision-jump":
        # a short, accurate jump onto a small target; precisionDamping shrinks the reach
        if up > j.standingHeight or no_gap_descent:
            return None
        reach = j.standingDistance * (1.0 - j.precisionDamping)
        return max(max(up, 0.0) / j.standingHeight, distance_A / reach, drop_term)

    # --- drops ---
    if verb == "controlled-drop":
        return drop / cfg.landing.hard if drop > 0.0 else None
    if verb == "hang-drop":
        eff = drop - cfg.avatarHeightA  # hang first, then let go
        return eff / cfg.landing.roll if eff > 0.0 else None
    if verb == "slide":
        return drop / cfg.landing.hard if drop > 0.0 else None
    if verb == "dive-roll":  # a forward diving roll: level or descending, never a climb
        if up > v.stepUp or distance_A > cfg.dive.distanceA:
            return None
        return max(distance_A / cfg.dive.distanceA, drop / cfg.landing.roll)

    # --- climbs (source must be a climbable class, enforced by CLASS_VERBS) ---
    if verb == "climb-up":  # top out a ledge/face
        cap = cfg.reach.holdReach + cfg.avatarHeightA
        return up / cap if up >= 0.0 else None
    if verb in ("rung-climb", "stud-climb", "free-climb", "pole-climb", "overhang-traverse"):
        span = max(abs(rise_A), distance_A)
        return span / cfg.reach.holdReach if span > 0.0 else 0.0
    if verb == "ledge-shimmy":
        return distance_A / cfg.reach.ledgeToLedge
    if verb == "ledge-to-ledge":
        return distance_A / cfg.reach.ledgeToLedge if distance_A <= cfg.reach.ledgeToLedge else None
    if verb == "wall-push":
        return distance_A / cfg.reach.ledgeToLedge if distance_A <= cfg.reach.ledgeToLedge else None
    if verb == "tic-tac":
        return _both(
            max(up, 0.0) / cfg.ticTac.reboundHeightA, distance_A / cfg.ticTac.reboundDistanceA
        )

    # --- tools (T3) ---
    if verb == "wall-run":
        if ctx.wall_length_A < cfg.wallRun.minWallRunA:
            return None
        return distance_A / (cfg.wallRun.speed * cfg.wallRun.maxDurationSec)
    if verb in ("grapple-swing", "grapple-ascend", "grapple-rappel"):
        if ctx.anchor_ledge_A < cfg.grapple.anchorMinLedgeA:
            return None
        reach = cfg.grapple.reachA
        span = max(abs(rise_A), distance_A)
        if verb == "grapple-rappel" and up > 0.0:
            return None  # rappel only descends
        return span / reach
    if verb == "pole-vault":
        if distance_A > cfg.poleVault.maxGapA or up > cfg.poleVault.maxHeightA:
            return None
        return _both(distance_A / cfg.poleVault.maxGapA, max(up, 0.0) / cfg.poleVault.maxHeightA)

    return None


def prerequisites(cfg: MovementConfig, verb: str, ctx: Context) -> dict:
    """Build the edge's ``prerequisites`` object with exactly the keys the schema
    requires for the verb, filled from ``cfg`` and ``ctx``."""
    pre: dict = {}
    req = REQUIRED_PREREQS.get(verb, ())
    if "tool" in req:
        pre["tool"] = TOOL_OF_VERB[verb]
    if "anchor_ledge_A" in req:
        pre["anchor_ledge_A"] = round(ctx.anchor_ledge_A, 4)
    if "min_speed_A_s" in req:
        speed = (
            cfg.wallRun.minEntrySpeed
            if verb == "wall-run"
            else (cfg.poleVault.minRunSpeed if verb == "pole-vault" else cfg.dive.minSpeed)
        )
        pre["min_speed_A_s"] = round(speed, 4)
    if "plant_window_s" in req:
        pre["plant_window_s"] = round(cfg.poleVault.plantWindowSec, 4)
    if "wall_length_A" in req:
        pre["wall_length_A"] = round(ctx.wall_length_A, 4)
    # running/sprint jumps record the run-up they used even though the schema does not
    # require it (it is optional there).
    if verb in ("running-jump", "sprint-jump") and ctx.run_up_A > 0.0:
        pre["run_up_A"] = round(ctx.run_up_A, 4)
    return pre


def cost(verb: str, distance_A: float, rise_A: float) -> float:
    return round(TIER_COST[VERB_TIER[verb]] + 0.4 * distance_A + 0.6 * abs(rise_A), 4)


def tool_ok(verb: str, ctx: Context) -> bool:
    """A tool verb is only usable if its tool is available in the context."""
    tool = TOOL_OF_VERB.get(verb)
    return tool is None or tool in ctx.tool_available


@dataclass(frozen=True)
class Affordance:
    verb: str
    tier: str
    margin_used: float
    cost: float
    prerequisites: dict


def best_affordance(
    cfg: MovementConfig,
    from_class: str,
    distance_A: float,
    rise_A: float,
    ctx: Context,
) -> Affordance | None:
    """The cheapest feasible verb enabled for ``from_class`` on this transition, or
    None. Feasible = geometrically applicable, margin ≤ 0.85, tool available."""
    best: Affordance | None = None
    for verb in CLASS_VERBS.get(from_class, ()):
        if not tool_ok(verb, ctx):
            continue
        m = verb_margin(cfg, verb, distance_A, rise_A, ctx)
        if m is None or m > movement.MARGIN:
            continue
        aff = Affordance(
            verb=verb,
            tier=VERB_TIER[verb],
            margin_used=round(m, 4),
            cost=cost(verb, distance_A, rise_A),
            prerequisites=prerequisites(cfg, verb, ctx),
        )
        key = (aff.tier, aff.margin_used, aff.cost)
        if best is None or key < (best.tier, best.margin_used, best.cost):
            best = aff
    return best
