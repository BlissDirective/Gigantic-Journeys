"""M3-MOVE-01 traversal tools (AUTH #021): grapple + pole-vault reference, and AT-3 — the
reachability validator accepts grapple/pole transitions within the movement.json limits."""

import movement
import reach
import tools_ref
from reach import Beat

CFG = movement.load()


def _edge(eid, frm, to, verb, tier, d, rise, pre=None):
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


# --- the dataclass defaults are the shipped movement.json values ---


def test_defaults_match_movement_json():
    assert tools_ref.GrappleParams() == tools_ref.GrappleParams.from_movement_config(CFG)
    assert tools_ref.PoleVaultParams() == tools_ref.PoleVaultParams.from_movement_config(CFG)


# --- grapple reference ---


def test_grapple_reach_and_anchor_and_aim():
    g = tools_ref.DEFAULT_GRAPPLE
    assert tools_ref.grapple_in_reach(g.reachA - 1.0, 0.0, g)
    assert not tools_ref.grapple_in_reach(g.reachA + 1.0, 0.0, g)
    assert tools_ref.anchor_eligible(g.anchorMinLedgeA, g)
    assert not tools_ref.anchor_eligible(g.anchorMinLedgeA - 0.01, g)
    assert tools_ref.aim_assisted(g.snapAssistA, g)
    assert not tools_ref.aim_assisted(g.snapAssistA + 0.01, g)


def test_grapple_mode_selection():
    assert tools_ref.grapple_mode(0.0, 3.0) == "ascend"
    assert tools_ref.grapple_mode(0.0, -3.0) == "rappel"
    assert tools_ref.grapple_mode(4.0, 0.0) == "swing"
    assert tools_ref.grapple_mode(4.0, 1.0) == "swing"


def test_grapple_timeline_is_the_full_state_machine():
    tl = tools_ref.grapple_timeline(4.0, 0.0)
    phases = [p["phase"] for p in tl]
    assert phases == ["aim", "deploy", "swing", "unhook", "reel", "coil"]
    by = {p["phase"]: p["duration_s"] for p in tl}
    assert by["deploy"] == tools_ref.DEFAULT_GRAPPLE.deploySec
    assert by["reel"] == tools_ref.DEFAULT_GRAPPLE.reelSec
    # mechanical time = deploy + travel + reel
    total = sum(p["duration_s"] for p in tl)
    assert abs(total - tools_ref.grapple_traversal_time(4.0, 0.0)) < 1e-6


def test_rappel_is_quicker_than_ascend_for_the_same_span():
    # rappelSpeed (1.0) > ascendSpeed (0.7), so dropping is faster than climbing the same distance
    up = tools_ref.grapple_traversal_time(0.0, 3.0)
    down = tools_ref.grapple_traversal_time(0.0, -3.0)
    assert down < up


# --- pole-vault reference ---


def test_pole_vault_feasibility():
    pv = tools_ref.DEFAULT_POLE_VAULT
    assert tools_ref.pole_vault_feasible(pv.maxGapA - 0.5, 0.0, pv.minRunSpeed, pv)
    assert tools_ref.pole_vault_feasible(0.0, pv.maxHeightA - 0.5, pv.minRunSpeed, pv)
    assert not tools_ref.pole_vault_feasible(pv.maxGapA + 0.5, 0.0, pv.minRunSpeed, pv)  # too far
    assert not tools_ref.pole_vault_feasible(
        0.0, pv.maxHeightA + 0.5, pv.minRunSpeed, pv
    )  # too high
    assert not tools_ref.pole_vault_feasible(1.0, 0.0, pv.minRunSpeed - 0.5, pv)  # too slow


# --- AT-3: the validator includes grapple + pole transitions (taught earlier) ---


def test_validator_accepts_a_grapple_swing_across_a_void():
    g = {
        "nodes": [],
        "edges": [
            _edge("e1", "n1", "n2", "walk", "T0", 0.2, 0.0),
            _edge("e2", "n2", "n3", "mantle", "T0", 0.2, 0.4),
            _edge(
                "e3",
                "n3",
                "n4",
                "grapple-swing",
                "T3",
                4.0,
                0.0,
                {"tool": "grapple", "anchor_ledge_A": 1.0},
            ),
        ],
    }
    beats = [Beat(1, ("e1",)), Beat(2, ("e2",), teaches="grapple-swing"), Beat(3, ("e3",))]
    res = reach.validate_route(g, beats, cfg=CFG, summit_node="n4")
    assert res.ok, res.problems
    assert tools_ref.grapple_in_reach(4.0, 0.0)  # the void is within the twine


def test_validator_accepts_a_pole_vault_over_a_gap():
    g = {
        "nodes": [],
        "edges": [
            _edge("e1", "n1", "n2", "walk", "T0", 0.2, 0.0),
            _edge("e2", "n2", "n3", "run", "T0", 0.5, 0.0),
            _edge(
                "e3",
                "n3",
                "n4",
                "pole-vault",
                "T3",
                2.5,
                0.0,
                {"tool": "pole-vault", "min_speed_A_s": 2.4, "plant_window_s": 0.25},
            ),
        ],
    }
    beats = [Beat(1, ("e1",)), Beat(2, ("e2",), teaches="pole-vault"), Beat(3, ("e3",))]
    res = reach.validate_route(g, beats, cfg=CFG, summit_node="n4")
    assert res.ok, res.problems
    assert tools_ref.pole_vault_feasible(2.5, 0.0, 2.4)


def test_tool_used_before_taught_is_rejected():
    g = {
        "nodes": [],
        "edges": [
            _edge(
                "e1",
                "n1",
                "n2",
                "grapple-swing",
                "T3",
                4.0,
                0.0,
                {"tool": "grapple", "anchor_ledge_A": 1.0},
            ),
        ],
    }
    res = reach.validate_route(g, [Beat(1, ("e1",))], cfg=CFG)
    assert not res.ok  # a tool is never beat 1 / never used before taught
