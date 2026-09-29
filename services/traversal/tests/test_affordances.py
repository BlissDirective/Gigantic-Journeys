"""M1-SCEN-03/05 affordance library: verb/tier table, class matrix, reach model."""

import json
from pathlib import Path

import affordances
import movement
from affordances import Context

REPO = Path(__file__).resolve().parents[3]
SCHEMA = REPO / "data" / "schemas" / "environment" / "traversal_graph.json"
CFG = movement.load()


def _schema_verb_tiers() -> dict[str, str]:
    """Recover the verb→tier mapping the frozen schema encodes in its allOf."""
    schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
    out: dict[str, str] = {}
    for clause in schema["$defs"]["edge"]["allOf"]:
        then = clause.get("then", {}).get("properties", {})
        tier = then.get("tier", {}).get("const")
        verbs = clause.get("if", {}).get("properties", {}).get("verb", {}).get("enum")
        if tier and verbs:
            for v in verbs:
                out[v] = tier
    return out


def test_verb_tier_table_matches_frozen_schema():
    assert affordances.VERB_TIER == _schema_verb_tiers()


def test_class_matrix_only_uses_known_verbs():
    known = set(affordances.VERB_TIER)
    for cls, verbs in affordances.CLASS_VERBS.items():
        assert set(verbs) <= known, cls
        assert len(set(verbs)) == len(verbs), f"{cls} has duplicate verbs"


def test_void_enables_nothing():
    assert affordances.CLASS_VERBS["void"] == ()


def test_walk_only_across_a_small_level_gap():
    assert affordances.verb_margin(CFG, "walk", 0.2, 0.0, Context()) == 0.0
    assert affordances.verb_margin(CFG, "walk", 3.0, 0.0, Context()) is None  # too far to step
    assert affordances.verb_margin(CFG, "walk", 0.2, 1.0, Context()) is None  # not level


def test_jump_rejects_no_gap_descent_but_allows_gap_crossing():
    # straight down with no gap is a drop, not a jump
    assert affordances.verb_margin(CFG, "standing-jump", 0.0, -1.5, Context()) is None
    # crossing a real gap is a jump
    assert affordances.verb_margin(CFG, "standing-jump", 1.0, 0.0, Context()) is not None


def test_dive_roll_never_climbs():
    assert affordances.verb_margin(CFG, "dive-roll", 1.0, 2.0, Context()) is None
    assert affordances.verb_margin(CFG, "dive-roll", 1.0, 0.0, Context()) is not None


def test_grapple_needs_anchor_ledge():
    no_anchor = Context(anchor_ledge_A=0.0, tool_available=frozenset({"grapple"}))
    ok = Context(anchor_ledge_A=1.0, tool_available=frozenset({"grapple"}))
    assert affordances.verb_margin(CFG, "grapple-ascend", 2.0, 3.0, no_anchor) is None
    assert affordances.verb_margin(CFG, "grapple-ascend", 2.0, 3.0, ok) is not None


def test_best_affordance_prefers_lowest_tier():
    # a small step up: mantle (T0) should win over any higher-tier option
    aff = affordances.best_affordance(CFG, "walkable-hard", 0.2, 0.3, Context())
    assert aff is not None
    assert aff.tier == "T0"


def test_best_affordance_tool_gating():
    # a +3 A gain at 2 A gap from a walkable needs the grapple; without the tool, none
    far_anchor = Context(to_kind="anchor", anchor_ledge_A=1.0, tool_available=frozenset())
    assert affordances.best_affordance(CFG, "walkable-hard", 2.0, 3.0, far_anchor) is None
    with_tool = Context(to_kind="anchor", anchor_ledge_A=1.0, tool_available=frozenset({"grapple"}))
    aff = affordances.best_affordance(CFG, "walkable-hard", 2.0, 3.0, with_tool)
    assert aff is not None and aff.prerequisites.get("tool") == "grapple"


def test_prerequisites_match_required_keys():
    ctx = Context(wall_length_A=4.0, anchor_ledge_A=1.0, run_up_A=2.0)
    assert set(affordances.prerequisites(CFG, "wall-run", ctx)) == {
        "min_speed_A_s",
        "wall_length_A",
    }
    assert set(affordances.prerequisites(CFG, "pole-vault", ctx)) == {
        "tool",
        "min_speed_A_s",
        "plant_window_s",
    }
    assert set(affordances.prerequisites(CFG, "grapple-ascend", ctx)) == {"tool", "anchor_ledge_A"}
