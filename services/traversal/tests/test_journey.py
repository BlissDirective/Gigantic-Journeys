"""M1-SCEN-04 journey generation: summit + routes + vistas -> environment_spec.

Built and validated against the frozen environment_spec schema, the cross-document
consistency checker, and the M1-SCEN-05 validator (which journey runs internally).
Uses crafted reachable traversal graphs; richer node placement from real geometry is a
fast-follow in M1-SCEN-03.
"""

import importlib.util
import json
from pathlib import Path

import journey
import movement
import pytest
from jsonschema import Draft202012Validator

REPO = Path(__file__).resolve().parents[3]
ENV = REPO / "data" / "schemas" / "environment"
SPEC_SCHEMA = json.loads((ENV / "environment_spec.json").read_text(encoding="utf-8"))
ENV_ID = "3c2b1a09-8f7e-4d6c-b5a4-938271605f4e"
CFG = movement.load()
SHA = __import__("hashlib").sha256(movement.DEFAULT_PATH.read_bytes()).hexdigest()


def _load_check_consistency():
    path = ENV / "check_consistency.py"
    spec = importlib.util.spec_from_file_location("check_consistency", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


CC = _load_check_consistency()


def node(nid, sid, pos, kind="stance", plantable=True):
    return {
        "id": nid,
        "surface_id": sid,
        "position": list(pos),
        "kind": kind,
        "plantable": plantable,
    }


def edge(eid, frm, to, verb, tier, d, rise, margin):
    return {
        "id": eid,
        "from": frm,
        "to": to,
        "verb": verb,
        "tier": tier,
        "distance_A": d,
        "rise_A": rise,
        "margin_used": margin,
        "cost": 1.0 + d,
        "commit": True,
        "prerequisites": {},
    }


def graph(nodes, edges):
    return {
        "schema_version": "1.0.0",
        "environment_id": ENV_ID,
        "generator": {"name": "gj-traversal", "version": "0.1.0"},
        "movement": {"config_sha256": SHA, "margin": 0.85},
        "nodes": nodes,
        "edges": edges,
    }


def surface(sid, cls, centroid, top):
    return {
        "id": sid,
        "class": cls,
        "confidence": 0.9,
        "material": "unknown",
        "centroid": list(centroid),
        "normal": [0, 1, 0],
        "bounds": {
            "min": [centroid[0] - 1, top - 0.1, centroid[2] - 1],
            "max": [centroid[0] + 1, top + 0.1, centroid[2] + 1],
        },
        "area_A2": 4.0,
        "measurements": {"top_height_A": top},
        "mesh": {"submesh": 0, "triangle_start": 0, "triangle_count": 1},
    }


def scene(surfaces, spawn_sid="surface-1"):
    return {
        "schema_version": "1.0.0",
        "environment_id": ENV_ID,
        "generator": {"name": "gj-scenegraph", "version": "0.2.0"},
        "capture_mode": "tabletop",
        "scale": {"multiplier": 12, "method": "default", "metres_per_A": 0.1458},
        "frame": {"units": "A", "up": "+y", "handedness": "left"},
        "bounds": {"min": [-20, 0, -20], "max": [20, 20, 20]},
        "floor_height_A": 0.0,
        "spawn": {"position": [0, 0, 0], "facing_deg": 90, "surface_id": spawn_sid},
        "surfaces": surfaces,
    }


def _validate(doc):
    return sorted(Draft202012Validator(SPEC_SCHEMA).iter_errors(doc), key=str)


# A staircase with two distinct spawn->summit paths (4 mantles each), spread in x/z.
def staircase():
    surfaces = [
        surface("surface-1", "walkable-hard", (0, 0, 0), 0.0),
        surface("surface-2", "walkable-hard", (3, 1, 0), 1.0),
        surface("surface-3", "walkable-hard", (6, 2, 0), 2.0),
        surface("surface-4", "walkable-hard", (9, 3, 0), 3.0),
        surface("surface-5", "walkable-hard", (12, 4, 6), 4.0),
        surface("surface-6", "walkable-hard", (3, 1, 6), 1.0),
        surface("surface-7", "walkable-hard", (6, 2, 6), 2.0),
        surface("surface-8", "walkable-hard", (9, 3, 6), 3.0),
    ]
    nodes = [
        node("node-1", "surface-1", (0, 0, 0)),
        node("node-2", "surface-2", (3, 1, 0)),
        node("node-3", "surface-3", (6, 2, 0)),
        node("node-4", "surface-4", (9, 3, 0)),
        node("node-5", "surface-5", (12, 4, 6)),
        node("node-6", "surface-6", (3, 1, 6)),
        node("node-7", "surface-7", (6, 2, 6)),
        node("node-8", "surface-8", (9, 3, 6)),
    ]
    m = 0.7143  # mantle 1.0/1.4
    edges = [
        edge("edge-1", "node-1", "node-2", "mantle", "T0", 0.5, 1.0, m),
        edge("edge-2", "node-2", "node-3", "mantle", "T0", 0.5, 1.0, m),
        edge("edge-3", "node-3", "node-4", "mantle", "T0", 0.5, 1.0, m),
        edge("edge-4", "node-4", "node-5", "mantle", "T0", 0.5, 1.0, m),
        edge("edge-5", "node-1", "node-6", "mantle", "T0", 0.5, 1.0, m),
        edge("edge-6", "node-6", "node-7", "mantle", "T0", 0.5, 1.0, m),
        edge("edge-7", "node-7", "node-8", "mantle", "T0", 0.5, 1.0, m),
        edge("edge-8", "node-8", "node-5", "mantle", "T0", 0.5, 1.0, m),
    ]
    return scene(surfaces), graph(nodes, edges)


def test_staircase_generates_valid_spec():
    sc, gr = staircase()
    spec = journey.generate_environment_spec(sc, gr)
    assert not _validate(spec), [e.message for e in _validate(spec)]
    assert spec["summit"]["node_id"] == "node-5"  # highest
    assert spec["summit"]["true_peak"] is True
    assert len(spec["routes"]) >= 2
    # rising difficulty by rank, and beat 1 is T0-only for every route
    gds = [r["global_difficulty"] for r in spec["routes"]]
    assert gds == sorted(gds)
    for r in spec["routes"]:
        assert r["rank"] >= 1
        assert r["beats"][0]["max_tier"] == "T0"
        assert r["beats"][0]["role"] == "introduce"
        assert r["beats"][0]["teaches"] is None
        assert r["required_tool"] is None


def test_staircase_passes_cross_document_checker():
    sc, gr = staircase()
    spec = journey.generate_environment_spec(sc, gr)
    problems = CC.check(sc, gr, spec)
    assert problems == [], problems


def test_deterministic():
    sc, gr = staircase()
    assert journey.generate_environment_spec(sc, gr) == journey.generate_environment_spec(sc, gr)


def test_vistas_are_low_access_and_scored():
    sc, gr = staircase()
    spec = journey.generate_environment_spec(sc, gr)
    assert 0 <= len(spec["vistas"]) <= 3
    for v in spec["vistas"]:
        assert v["access_tier"] in ("T0", "T1")
        assert set(v["scores"]) == {"viewshed", "framing", "access", "spread"}


# A short single path -> the template 'explore' fallback (2 beats, one route).
def fallback_env():
    surfaces = [
        surface("surface-1", "walkable-hard", (0, 0, 0), 0.0),
        surface("surface-2", "walkable-hard", (3, 1, 0), 1.0),
        surface("surface-3", "walkable-hard", (6, 2, 0), 2.0),
    ]
    nodes = [
        node("node-1", "surface-1", (0, 0, 0)),
        node("node-2", "surface-2", (3, 1, 0)),
        node("node-3", "surface-3", (6, 2, 0)),
    ]
    m = 0.7143
    edges = [
        edge("edge-1", "node-1", "node-2", "mantle", "T0", 0.5, 1.0, m),
        edge("edge-2", "node-2", "node-3", "mantle", "T0", 0.5, 1.0, m),
    ]
    return scene(surfaces), graph(nodes, edges)


def test_template_fallback_single_explore_route():
    sc, gr = fallback_env()
    spec = journey.generate_environment_spec(sc, gr)
    assert not _validate(spec)
    assert spec["generation"]["template_fallback"] is True
    assert len(spec["routes"]) == 1
    assert spec["routes"][0]["template_fallback"] is True
    assert len(spec["routes"][0]["beats"]) == 2  # introduce -> resolve
    assert CC.check(sc, gr, spec) == []


def test_no_reachable_summit_raises():
    # spawn isolated: the only plantable node is the spawn itself
    surfaces = [surface("surface-1", "walkable-hard", (0, 0, 0), 0.0)]
    nodes = [node("node-1", "surface-1", (0, 0, 0))]
    with pytest.raises(journey.JourneyError):
        journey.generate_environment_spec(scene(surfaces), graph(nodes, []))
