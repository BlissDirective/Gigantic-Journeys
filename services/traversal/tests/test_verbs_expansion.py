"""M1-MOVE-02 (AUTH #021) expanded-verb set — Brain-B reachability coverage.

The expanded verbs (dive-roll, tic-tac, speed/kong/lazy-vault, wall-run) are modelled in the
shared affordance library and are members of the frozen traversal_graph schema (AUTH #037).
These tests prove the deterministic validator (M1-SCEN-05) accounts for each new transition —
a route may use it within the 0.85 margin when the geometry/prerequisites hold, and it is
rejected otherwise (M1-MOVE-02 AT-2). The Unity verb implementations + MoveClip tags
(AT-1/AT-3) are gj-gameplay.

Test geometry is derived from the live MovementConfig, so the checks follow the tuning
(e.g. the AUTH #043 more-real default) instead of hard-coded numbers.
"""

import json
from pathlib import Path

import affordances
import movement
import reach
from affordances import Context
from reach import Beat

CFG = movement.load()
REPO = Path(__file__).resolve().parents[3]
SCHEMA = json.loads(
    (REPO / "data" / "schemas" / "environment" / "traversal_graph.json").read_text(encoding="utf-8")
)

NEW_VERBS = ("dive-roll", "tic-tac", "speed-vault", "kong-vault", "lazy-vault", "wall-run")
VAULT_VARIANTS = ("speed-vault", "kong-vault", "lazy-vault")


def edge(eid, frm, to, verb, tier, d, rise, pre=None):
    return {
        "id": eid,
        "from": frm,
        "to": to,
        "verb": verb,
        "tier": tier,
        "distance_A": d,
        "rise_A": rise,
        "margin_used": 0.0,
        "cost": 1.0,
        "commit": False,
        "prerequisites": pre or {},
    }


# --- the new verbs are part of the frozen contract ---


def test_new_verbs_are_in_the_frozen_schema_enum():
    enum = set(SCHEMA["$defs"]["edge"]["properties"]["verb"]["enum"])
    assert set(NEW_VERBS) <= enum


def test_new_verb_tiers_match_the_frozen_schema():
    expected = {
        "dive-roll": "T1",
        "speed-vault": "T1",
        "kong-vault": "T1",
        "lazy-vault": "T1",
        "tic-tac": "T2",
        "wall-run": "T3",
    }
    for verb, tier in expected.items():
        assert affordances.VERB_TIER[verb] == tier, verb


def test_each_new_verb_is_enabled_for_some_class():
    for verb in NEW_VERBS:
        assert any(verb in verbs for verbs in affordances.CLASS_VERBS.values()), verb


# --- dive-roll (T1): committed forward dive, level or descending, never a climb ---


def test_dive_roll_feasible_level_and_rejected_climb_or_too_far():
    d = CFG.dive.distanceA * 0.5
    m = affordances.verb_margin(CFG, "dive-roll", d, 0.0, Context())
    assert m is not None and m <= movement.MARGIN
    climb = CFG.verticals.stepUp + 0.5
    assert affordances.verb_margin(CFG, "dive-roll", d, climb, Context()) is None
    too_far = CFG.dive.distanceA + 0.5
    assert affordances.verb_margin(CFG, "dive-roll", too_far, 0.0, Context()) is None


def test_dive_roll_edge_validates_and_records_min_speed():
    pre = affordances.prerequisites(CFG, "dive-roll", Context())
    assert set(pre) == {"min_speed_A_s"}
    _, ok, reason = reach.check_transition(
        CFG, edge("e", "a", "b", "dive-roll", "T1", CFG.dive.distanceA * 0.5, 0.0, pre)
    )
    assert ok, reason


# --- tic-tac (T2): wall rebound for height/redirect ---


def test_tic_tac_feasible_within_rebound_and_over_rejected():
    up = CFG.ticTac.reboundHeightA * 0.5
    d = CFG.ticTac.reboundDistanceA * 0.5
    m = affordances.verb_margin(CFG, "tic-tac", d, up, Context())
    assert m is not None and m <= movement.MARGIN
    over = affordances.verb_margin(CFG, "tic-tac", d, CFG.ticTac.reboundHeightA * 2, Context())
    assert over is not None and over > movement.MARGIN


def test_tic_tac_is_a_wall_verb():
    assert "tic-tac" in affordances.CLASS_VERBS["wall-smooth"]
    assert "tic-tac" in affordances.CLASS_VERBS["textured-vertical"]


# --- vault variants (T1): modelled identically to vault; the animator picks the style ---


def test_vault_variants_share_the_vault_envelope_and_tier():
    up = CFG.verticals.vault * 0.5
    d = CFG.verticals.vault * 0.5
    base = affordances.verb_margin(CFG, "vault", d, up, Context())
    assert base is not None
    for verb in VAULT_VARIANTS:
        m = affordances.verb_margin(CFG, verb, d, up, Context())
        assert m is not None and m <= movement.MARGIN, verb
        assert m == base, verb
        assert affordances.VERB_TIER[verb] == "T1"
        assert verb in affordances.CLASS_VERBS["walkable-hard"]


def test_vault_variant_rejected_above_vault_height():
    too_high = CFG.verticals.vault + 0.5
    for verb in VAULT_VARIANTS:
        assert affordances.verb_margin(CFG, verb, 0.2, too_high, Context()) is None, verb


def test_vault_variant_edges_validate():
    up = CFG.verticals.vault * 0.5
    for verb in VAULT_VARIANTS:
        _, ok, reason = reach.check_transition(CFG, edge("e", "a", "b", verb, "T1", up, up))
        assert ok, f"{verb}: {reason}"


# --- wall-run (T3): short run across a flat vertical of at least minWallRunA ---


def test_wall_run_needs_a_long_enough_wall():
    short = Context(wall_length_A=CFG.wallRun.minWallRunA - 1.0)
    long_wall = Context(wall_length_A=CFG.wallRun.minWallRunA + 0.5)
    assert affordances.verb_margin(CFG, "wall-run", 2.0, 0.0, short) is None
    m = affordances.verb_margin(CFG, "wall-run", 2.0, 0.0, long_wall)
    assert m is not None and m <= movement.MARGIN


def test_wall_run_edge_validates_with_prereqs_and_rejects_short_wall():
    ctx = Context(wall_length_A=CFG.wallRun.minWallRunA + 0.5)
    pre = affordances.prerequisites(CFG, "wall-run", ctx)
    assert set(pre) == {"min_speed_A_s", "wall_length_A"}
    _, ok, reason = reach.check_transition(
        CFG, edge("e", "a", "b", "wall-run", "T3", 2.0, 0.0, pre)
    )
    assert ok, reason
    short_pre = {
        "min_speed_A_s": CFG.wallRun.minEntrySpeed,
        "wall_length_A": CFG.wallRun.minWallRunA - 1.0,
    }
    _, ok_short, _ = reach.check_transition(
        CFG, edge("e", "a", "b", "wall-run", "T3", 2.0, 0.0, short_pre)
    )
    assert not ok_short


# --- AT-2: a generated route may actually use a new verb within the margin ---


def test_route_validator_accepts_a_dive_roll_after_a_t0_beat():
    pre = affordances.prerequisites(CFG, "dive-roll", Context())
    g = {
        "nodes": [],
        "edges": [
            edge("e1", "n1", "n2", "walk", "T0", 0.2, 0.0),
            edge("e2", "n2", "n3", "dive-roll", "T1", CFG.dive.distanceA * 0.5, 0.0, pre),
        ],
    }
    res = reach.validate_route(g, [Beat(1, ("e1",)), Beat(2, ("e2",))], cfg=CFG)
    assert res.ok, res.problems
