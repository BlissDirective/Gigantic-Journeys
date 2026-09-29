"""M1-SCEN-03 traversal-graph export: schema, AT-2 (verb enabled for class), AT-4 (tools)."""

import json
from pathlib import Path

import affordances
import graph
from jsonschema import Draft202012Validator

REPO = Path(__file__).resolve().parents[3]
ENV = REPO / "data" / "schemas" / "environment"
SCHEMA = json.loads((ENV / "traversal_graph.json").read_text(encoding="utf-8"))
DESK = json.loads(
    (ENV / "fixtures" / "valid" / "scene_graph.desk-tabletop.json").read_text("utf-8")
)
ENV_ID = "3c2b1a09-8f7e-4d6c-b5a4-938271605f4e"


def _validate(doc):
    return sorted(Draft202012Validator(SCHEMA).iter_errors(doc), key=str)


def surface(sid, cls, centroid, bounds, top, extra=None):
    m = {"top_height_A": top}
    if extra:
        m.update(extra)
    return {
        "id": sid,
        "class": cls,
        "confidence": 0.9,
        "material": "unknown",
        "centroid": list(centroid),
        "normal": [0, 1, 0],
        "bounds": {"min": list(bounds[0]), "max": list(bounds[1])},
        "area_A2": 1.0,
        "measurements": m,
        "mesh": {"submesh": 0, "triangle_start": 0, "triangle_count": 1},
    }


def scene(surfaces):
    return {
        "schema_version": "1.0.0",
        "environment_id": ENV_ID,
        "generator": {"name": "gj-scenegraph", "version": "0.2.0"},
        "capture_mode": "tabletop",
        "scale": {"multiplier": 12, "method": "default", "metres_per_A": 0.1458},
        "frame": {"units": "A", "up": "+y", "handedness": "left"},
        "bounds": {"min": [-50, -50, -50], "max": [50, 50, 50]},
        "floor_height_A": 0.0,
        "spawn": {"position": [0, 0, 0], "facing_deg": 0, "surface_id": surfaces[0]["id"]},
        "surfaces": surfaces,
    }


def test_desk_fixture_builds_schema_valid_graph():
    doc = graph.build_traversal_graph(DESK)
    assert not _validate(doc)
    assert len(doc["nodes"]) >= 1
    assert doc["movement"]["margin"] == 0.85
    assert len(doc["movement"]["config_sha256"]) == 64


def test_at2_every_edge_verb_enabled_for_source_class():
    doc = graph.build_traversal_graph(DESK)
    node_surface = {n["id"]: n["surface_id"] for n in doc["nodes"]}
    surface_class = {s["id"]: s["class"] for s in DESK["surfaces"]}
    for e in doc["edges"]:
        cls = surface_class[node_surface[e["from"]]]
        assert e["verb"] in affordances.CLASS_VERBS[cls], (e["id"], e["verb"], cls)


def test_edge_tier_matches_verb():
    doc = graph.build_traversal_graph(DESK)
    for e in doc["edges"]:
        assert e["tier"] == affordances.VERB_TIER[e["verb"]]


def test_all_margins_within_85pct():
    doc = graph.build_traversal_graph(DESK)
    assert all(e["margin_used"] <= 0.85 for e in doc["edges"])


def test_deterministic():
    assert graph.build_traversal_graph(DESK) == graph.build_traversal_graph(DESK)


def test_at4_grapple_edge_appears_with_prerequisites():
    # a floor and a high ledge only reachable by grapple (too high/near for a jump)
    s = scene(
        [
            surface("surface-1", "walkable-hard", (0, 0, 0), ((-1, -0.1, -1), (1, 0.1, 1)), 0.0),
            surface(
                "surface-2",
                "ledge",
                (0, 4, 3),
                ((-1, 3.95, 2.5), (1, 4.05, 3.5)),
                4.0,
                {"edge_length_A": 2.0},
            ),
        ]
    )
    doc = graph.build_traversal_graph(s)
    assert not _validate(doc)
    grapple = [e for e in doc["edges"] if e["verb"].startswith("grapple")]
    assert grapple, "expected a grapple edge to the ledge anchor"
    for e in grapple:
        assert e["prerequisites"]["tool"] == "grapple"
        assert e["prerequisites"]["anchor_ledge_A"] >= 0.1


def test_at4_wall_run_edge_appears_with_prerequisites():
    # two platforms 3.2 A apart (beyond sprint-jump, within wall-run) with a wall between
    s = scene(
        [
            surface(
                "surface-1", "walkable-hard", (-2.8, 0, 0), ((-4, -0.1, -2), (-1.6, 0.1, 2)), 0.0
            ),
            surface("surface-2", "walkable-hard", (2.8, 0, 0), ((1.6, -0.1, -2), (4, 0.1, 2)), 0.0),
            surface(
                "surface-3",
                "wall-smooth",
                (0, 1.5, 0),
                ((-0.3, 0, -2), (0.3, 3, 2)),
                3.0,
                {"edge_length_A": 4.0},
            ),
        ]
    )
    doc = graph.build_traversal_graph(s)
    assert not _validate(doc)
    wall = [e for e in doc["edges"] if e["verb"] == "wall-run"]
    assert wall, "expected a wall-run edge across the gap"
    for e in wall:
        assert e["prerequisites"]["wall_length_A"] >= 3.0
        assert e["prerequisites"]["min_speed_A_s"] > 0


def test_no_tools_option_drops_tool_edges():
    doc = graph.build_traversal_graph(DESK, tools=frozenset())
    assert not any(e["prerequisites"].get("tool") for e in doc["edges"])


def test_large_surface_gets_edge_nodes_and_intra_surface_walk():
    # a big floor (10x8) gets a centroid + 4 edge-midpoint stance nodes; a small
    # platform beside it keeps a single node
    s = scene(
        [
            surface("surface-1", "walkable-hard", (0, 0, 0), ((-5, -0.1, -4), (5, 0.1, 4)), 0.0),
            surface("surface-2", "walkable-hard", (6, 1, 0), ((5.2, 0.9, -1), (7, 1.1, 1)), 1.0),
        ]
    )
    doc = graph.build_traversal_graph(s)
    assert not _validate(doc)
    big = [n for n in doc["nodes"] if n["surface_id"] == "surface-1"]
    small = [n for n in doc["nodes"] if n["surface_id"] == "surface-2"]
    assert len(big) == 5 and len(small) == 1
    # intra-surface walk edges exist and cross more than a step gap (free on one surface)
    intra_ids = {n["id"] for n in big}
    intra = [
        e
        for e in doc["edges"]
        if e["from"] in intra_ids and e["to"] in intra_ids and e["verb"] == "walk"
    ]
    assert intra and max(e["distance_A"] for e in intra) > 1.0


def test_validator_accepts_intra_surface_walk_but_not_across_a_gap():
    import movement
    import reach

    cfg = movement.load()
    s = scene(
        [surface("surface-1", "walkable-hard", (0, 0, 0), ((-5, -0.1, -4), (5, 0.1, 4)), 0.0)]
    )
    doc = graph.build_traversal_graph(s)
    walk = next(e for e in doc["edges"] if e["verb"] == "walk" and e["distance_A"] > 1.0)
    # same-surface walk is free; the identical distance as a between-surface gap is too far to step
    assert reach.check_transition(cfg, walk, same_surface=True)[1]
    assert not reach.check_transition(cfg, walk, same_surface=False)[1]


def test_empty_scene_rejected():
    import pytest

    s = scene([surface("surface-1", "void", (0, 0, 0), ((-1, -1, -1), (1, 1, 1)), 0.0)])
    with pytest.raises(ValueError, match="no traversable"):
        graph.build_traversal_graph(s)
