"""Anticipation-planner tests (#2) — AUTH #043. Consumes the frozen desk-tabletop fixtures."""

import json
from pathlib import Path

import affordances
import anticipation
import pytest

REPO = Path(__file__).resolve().parents[3]
FIX = REPO / "data" / "schemas" / "environment" / "fixtures" / "valid"


def _graph():
    return json.loads((FIX / "traversal_graph.desk-tabletop.json").read_text(encoding="utf-8"))


def _spec():
    return json.loads((FIX / "environment_spec.desk-tabletop.json").read_text(encoding="utf-8"))


def test_every_tier_verb_has_a_category():
    # the planner must classify every verb the frozen tier table defines
    assert anticipation._unmapped_verbs() == set()


def test_edge_ids_of_route_flattens_beats_in_order():
    route = _spec()["routes"][0]
    assert anticipation.edge_ids_of_route(route) == [
        "edge-1",
        "edge-2",
        "edge-3",
        "edge-4",
        "edge-5",
    ]


def test_plan_skips_locomotion_and_hints_contact_verbs():
    graph, route = _graph(), _spec()["routes"][0]
    hints = anticipation.plan_anticipation(graph, anticipation.edge_ids_of_route(route))
    # edge-1 walk is locomotion → skipped; the four contact verbs are hinted
    assert [h.edge_id for h in hints] == ["edge-2", "edge-3", "edge-4", "edge-5"]
    assert [h.category for h in hints] == ["climb", "jump", "climb", "climb"]


def test_hint_contact_point_and_surface_come_from_target_node():
    graph, route = _graph(), _spec()["routes"][0]
    by_edge = {
        h.edge_id: h
        for h in anticipation.plan_anticipation(graph, anticipation.edge_ids_of_route(route))
    }
    # edge-2 lands on node-3 (surface-2, [-6, 1.2, 0])
    assert by_edge["edge-2"].contact_point == (-6.0, 1.2, 0.0)
    assert by_edge["edge-2"].reach_target == (-6.0, 1.2, 0.0)
    assert by_edge["edge-2"].surface_id == "surface-2"


def test_gaze_leads_to_next_hold_then_falls_back_to_own_contact():
    graph, route = _graph(), _spec()["routes"][0]
    by_edge = {
        h.edge_id: h
        for h in anticipation.plan_anticipation(graph, anticipation.edge_ids_of_route(route))
    }
    # edge-2 looks ahead to edge-3's target node-4 ([-4, 2, 0])
    assert by_edge["edge-2"].look_at == (-4.0, 2.0, 0.0)
    # the last edge has nothing ahead → gazes at its own contact (node-6)
    assert by_edge["edge-5"].look_at == by_edge["edge-5"].contact_point == (0.0, 5.0, 2.5)


def test_hand_and_foot_flags():
    graph, route = _graph(), _spec()["routes"][0]
    by_edge = {
        h.edge_id: h
        for h in anticipation.plan_anticipation(graph, anticipation.edge_ids_of_route(route))
    }
    assert by_edge["edge-2"].needs_hand is True  # climb pre-reaches a hand
    assert by_edge["edge-3"].needs_hand is False  # jump does not
    assert by_edge["edge-3"].plant_foot == "left"  # first plant foot
    assert by_edge["edge-2"].plant_foot == "none"  # climbs do not pick a take-off foot


def test_lead_time_from_params_per_category():
    graph, route = _graph(), _spec()["routes"][0]
    p = anticipation.DEFAULT_ANTICIPATION
    by_edge = {
        h.edge_id: h
        for h in anticipation.plan_anticipation(graph, anticipation.edge_ids_of_route(route))
    }
    assert by_edge["edge-2"].lead_time_s == pytest.approx(p.leadTimeSec["climb"])
    assert by_edge["edge-3"].lead_time_s == pytest.approx(p.leadTimeSec["jump"])


def test_deterministic():
    graph, route = _graph(), _spec()["routes"][0]
    eids = anticipation.edge_ids_of_route(route)
    assert anticipation.plan_anticipation(graph, eids) == anticipation.plan_anticipation(
        graph, eids
    )


def test_route_2_has_one_jump_and_three_climbs():
    graph, route = _graph(), _spec()["routes"][1]
    hints = anticipation.plan_anticipation(graph, anticipation.edge_ids_of_route(route))
    # edge-1 walk skipped; edge-2 mantle, edge-6 running-jump, edge-11 stud-climb, edge-12 climb-up
    assert [h.category for h in hints] == ["climb", "jump", "climb", "climb"]


def test_unknown_edge_raises():
    with pytest.raises(anticipation.AnticipationError):
        anticipation.plan_anticipation(_graph(), ["edge-404"])


def test_non_chaining_route_raises():
    # edge-1 ends at node-2; edge-3 starts at node-3 → not a chain
    with pytest.raises(anticipation.AnticipationError):
        anticipation.plan_anticipation(_graph(), ["edge-1", "edge-3"])


def test_plant_foot_alternates_across_jumps():
    # a synthetic chain of two jumps off one node pair would alternate left/right
    graph = {
        "nodes": [
            {
                "id": "a",
                "surface_id": "s",
                "position": [0, 0, 0],
                "kind": "stance",
                "plantable": False,
            },
            {
                "id": "b",
                "surface_id": "s",
                "position": [1, 0, 0],
                "kind": "stance",
                "plantable": False,
            },
            {
                "id": "c",
                "surface_id": "s",
                "position": [2, 0, 0],
                "kind": "stance",
                "plantable": False,
            },
        ],
        "edges": [
            {"id": "e1", "from": "a", "to": "b", "verb": "standing-jump", "tier": "T0"},
            {"id": "e2", "from": "b", "to": "c", "verb": "standing-jump", "tier": "T0"},
        ],
    }
    feet = [h.plant_foot for h in anticipation.plan_anticipation(graph, ["e1", "e2"])]
    assert feet == ["left", "right"]


def test_affordances_import_available():
    # sanity: the tier table the coverage guard depends on is importable
    assert "running-jump" in affordances.VERB_TIER
