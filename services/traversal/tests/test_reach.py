"""M1-SCEN-05 reachability validator: per-segment reach + beat/tool route rules (AT-2)."""

import movement
import reach
from reach import Beat

CFG = movement.load()


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


def graph(edges):
    return {"nodes": [], "edges": edges}


# --- per-transition reachability (85 % margin) ---


def test_gap_just_under_85pct_accepted_and_over_rejected():
    under = edge("e1", "n1", "n2", "standing-jump", "T0", 1.0, 0.0)  # 1.0/1.2 = 0.833
    over = edge("e2", "n1", "n2", "standing-jump", "T0", 1.05, 0.0)  # 1.05/1.2 = 0.875
    mu, ok_u, _ = reach.check_transition(CFG, under)
    mo, ok_o, _ = reach.check_transition(CFG, over)
    assert ok_u and mu <= movement.MARGIN
    assert not ok_o and mo > movement.MARGIN


def test_tier_mismatch_rejected():
    _, ok, reason = reach.check_transition(CFG, edge("e1", "n1", "n2", "walk", "T2", 0.2, 0.0))
    assert not ok and "tier" in reason


def test_inapplicable_verb_rejected():
    # dive-roll cannot climb
    _, ok, _ = reach.check_transition(CFG, edge("e1", "n1", "n2", "dive-roll", "T1", 1.0, 2.0))
    assert not ok


# --- route rules ---


def test_unreachable_summit_is_invalid():
    g = graph([edge("e1", "n1", "n2", "walk", "T0", 0.2, 0.0)])
    res = reach.validate_route(g, [Beat(1, ("e1",))], cfg=CFG, spawn_node="n1", summit_node="n9")
    assert not res.ok
    assert any("summit" in p for p in res.problems)


def test_reaches_summit_is_valid():
    g = graph([edge("e1", "n1", "n2", "walk", "T0", 0.2, 0.0)])
    res = reach.validate_route(g, [Beat(1, ("e1",))], cfg=CFG, spawn_node="n1", summit_node="n2")
    assert res.ok, res.problems


def test_beat1_must_be_T0():
    g = graph([edge("e1", "n1", "n2", "sprint-jump", "T1", 2.0, 0.0)])
    res = reach.validate_route(g, [Beat(1, ("e1",))], cfg=CFG)
    assert not res.ok
    assert any("T0" in p for p in res.problems)


def test_T1_allowed_after_a_T0_beat1():
    g = graph(
        [
            edge("e1", "n1", "n2", "walk", "T0", 0.2, 0.0),
            edge("e2", "n2", "n3", "sprint-jump", "T1", 2.0, 0.0),
        ]
    )
    res = reach.validate_route(g, [Beat(1, ("e1",)), Beat(2, ("e2",))], cfg=CFG)
    assert res.ok, res.problems


def test_tool_required_but_never_taught_rejected():
    g = graph(
        [
            edge("e1", "n1", "n2", "walk", "T0", 0.2, 0.0),
            edge(
                "e2",
                "n2",
                "n3",
                "grapple-ascend",
                "T3",
                2.0,
                3.0,
                {"tool": "grapple", "anchor_ledge_A": 0.4},
            ),
        ]
    )
    res = reach.validate_route(g, [Beat(1, ("e1",)), Beat(2, ("e2",))], cfg=CFG)
    assert not res.ok
    assert any("tool grapple" in p and "never taught" in p for p in res.problems)


def test_tool_used_before_taught_rejected():
    g = graph(
        [
            edge(
                "e1",
                "n1",
                "n2",
                "grapple-ascend",
                "T3",
                2.0,
                3.0,
                {"tool": "grapple", "anchor_ledge_A": 0.4},
            ),
            edge("e2", "n2", "n3", "mantle", "T0", 0.2, 1.0),
        ]
    )
    # beat 2 teaches grapple, but the tool is used in beat 1 -> invalid (also beat-1 T0)
    beats = [Beat(1, ("e1",)), Beat(2, ("e2",), teaches="grapple-swing")]
    res = reach.validate_route(g, beats, cfg=CFG)
    assert not res.ok


def test_tool_taught_in_earlier_beat_is_valid():
    g = graph(
        [
            edge("e1", "n1", "n2", "walk", "T0", 0.2, 0.0),
            edge("e2", "n2", "n3", "mantle", "T0", 0.2, 1.0),
            edge(
                "e3",
                "n3",
                "n4",
                "grapple-ascend",
                "T3",
                2.0,
                3.0,
                {"tool": "grapple", "anchor_ledge_A": 0.4},
            ),
        ]
    )
    beats = [Beat(1, ("e1",)), Beat(2, ("e2",), teaches="grapple-swing"), Beat(3, ("e3",))]
    res = reach.validate_route(g, beats, cfg=CFG)
    assert res.ok, res.problems


def test_tool_taught_in_beat1_flagged():
    g = graph([edge("e1", "n1", "n2", "walk", "T0", 0.2, 0.0)])
    res = reach.validate_route(g, [Beat(1, ("e1",), teaches="grapple-swing")], cfg=CFG)
    assert not res.ok
    assert any("beat 1" in p for p in res.problems)


def test_broken_chain_rejected():
    g = graph(
        [
            edge("e1", "n1", "n2", "walk", "T0", 0.2, 0.0),
            edge("e2", "n8", "n9", "walk", "T0", 0.2, 0.0),  # does not start at n2
        ]
    )
    res = reach.validate_route(g, [Beat(1, ("e1", "e2"))], cfg=CFG)
    assert not res.ok
    assert any("path breaks" in p for p in res.problems)


def test_deterministic():
    g = graph([edge("e1", "n1", "n2", "walk", "T0", 0.2, 0.0)])
    a = reach.validate_route(g, [Beat(1, ("e1",))], cfg=CFG, summit_node="n2")
    b = reach.validate_route(g, [Beat(1, ("e1",))], cfg=CFG, summit_node="n2")
    assert (a.ok, a.problems, [s.margin_used for s in a.segments]) == (
        b.ok,
        b.problems,
        [s.margin_used for s in b.segments],
    )
