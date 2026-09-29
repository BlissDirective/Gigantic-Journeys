"""M1-SCEN-02 scene-graph build: schema conformance, classes, scale, spawn, mesh runs."""

import json
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator
from scenegraph import geometry as g
from scenegraph.classify import VisionLabel
from scenegraph.mesh import Mesh
from scenegraph.scene import AVATAR_METRES, CaptureMeta, build_scene_graph

REPO = Path(__file__).resolve().parents[3]
SCHEMA = REPO / "data" / "schemas" / "environment" / "scene_graph.json"
ENV_ID = "3c2b1a09-8f7e-4d6c-b5a4-938271605f4e"


def add_quad(V, T, corners, want):
    base = len(V)
    V.extend([(float(x), float(y), float(z)) for x, y, z in corners])
    a, b, c, d = base, base + 1, base + 2, base + 3
    tris = [(a, b, c), (a, c, d)]
    if g.dot(g.tri_normal(V[a], V[b], V[c]), want) < 0:
        tris = [(a, c, b), (a, d, c)]
    T.extend(tris)


def synthetic_room() -> Mesh:
    """A metric (metres, +y up) test scene: floor, ceiling, a +x wall, a raised
    platform, a narrow bridge, and a 45° ramp."""
    V: list = []
    T: list = []
    add_quad(V, T, [(-2, 0, -1.5), (2, 0, -1.5), (2, 0, 1.5), (-2, 0, 1.5)], (0, 1, 0))  # floor
    add_quad(
        V, T, [(-2, 2.5, -1.5), (2, 2.5, -1.5), (2, 2.5, 1.5), (-2, 2.5, 1.5)], (0, -1, 0)
    )  # ceil
    add_quad(V, T, [(2, 0, -1.5), (2, 2.5, -1.5), (2, 2.5, 1.5), (2, 0, 1.5)], (1, 0, 0))  # +x wall
    add_quad(
        V,
        T,
        [(-0.5, 0.75, -0.5), (0.5, 0.75, -0.5), (0.5, 0.75, 0.5), (-0.5, 0.75, 0.5)],
        (0, 1, 0),
    )  # platform
    add_quad(
        V, T, [(-1, 0.4, -0.025), (1, 0.4, -0.025), (1, 0.4, 0.025), (-1, 0.4, 0.025)], (0, 1, 0)
    )  # bridge
    add_quad(
        V, T, [(0.5, 0, -1.4), (1.5, 1, -1.4), (1.5, 1, 1.4), (0.5, 0, 1.4)], (-1, 1, 0)
    )  # ramp
    return Mesh(V, T)


def meta(**kw) -> CaptureMeta:
    base = dict(environment_id=ENV_ID, capture_mode="tabletop", scale_multiplier=12.0)
    base.update(kw)
    return CaptureMeta(**base)


def build(**kw):
    return build_scene_graph(synthetic_room(), meta(**kw))


def test_scene_graph_validates_against_frozen_schema():
    doc, _ = build()
    schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
    errors = sorted(Draft202012Validator(schema).iter_errors(doc), key=str)
    assert not errors, [e.message for e in errors]


def test_scale_block():
    doc, _ = build(scale_multiplier=12.0, scale_method="inferred-studs")
    assert doc["scale"]["multiplier"] == 12.0
    assert doc["scale"]["method"] == "inferred-studs"
    assert doc["scale"]["metres_per_A"] == round(AVATAR_METRES / 12.0, 6)
    assert doc["frame"] == {"units": "A", "up": "+y", "handedness": "left"}


def test_geometric_classes_present():
    doc, _ = build()
    classes = {s["class"] for s in doc["surfaces"]}
    assert "walkable-hard" in classes  # floor + platform
    assert "walkable-narrow" in classes  # the 0.05 m bridge
    assert "wall-smooth" in classes  # the +x wall
    assert "overhang" in classes  # the ceiling
    assert "slope" in classes  # the 45 deg ramp
    # No vision pass -> every material is unknown, no semantic labels emitted.
    assert all(s["material"] == "unknown" for s in doc["surfaces"])
    assert all("semantic" not in s for s in doc["surfaces"])


def test_floor_is_origin_and_spawn_on_a_low_walkable():
    doc, _ = build()
    assert doc["floor_height_A"] == 0.0
    spawn_ids = {s["id"] for s in doc["surfaces"]}
    assert doc["spawn"]["surface_id"] in spawn_ids
    spawn_surface = next(s for s in doc["surfaces"] if s["id"] == doc["spawn"]["surface_id"])
    assert spawn_surface["class"].startswith("walkable")
    assert spawn_surface["measurements"]["top_height_A"] == 0.0  # the floor
    assert 0.0 <= doc["spawn"]["facing_deg"] <= 360.0


def test_narrow_bridge_width_and_headroom():
    doc, _ = build()
    bridge = next(s for s in doc["surfaces"] if s["class"] == "walkable-narrow")
    assert bridge["measurements"]["width_A"] < 0.5
    # under the ceiling -> finite headroom, less than the open-sky cap
    assert 0.0 < bridge["measurements"]["headroom_A"] < 50.0


def test_triangle_runs_are_contiguous_and_cover_the_mesh():
    doc, collision = build()
    cursor = 0
    for s in doc["surfaces"]:
        assert s["mesh"]["triangle_start"] == cursor
        assert s["mesh"]["triangle_count"] >= 1
        cursor += s["mesh"]["triangle_count"]
    assert cursor == collision.triangle_count


def test_deterministic():
    a, _ = build()
    b, _ = build()
    assert a == b


class _FakeVision:
    def label(self, patch, geom_class, confidence):
        return VisionLabel(
            material="wood", semantic="desk", class_override="ledge", confidence=0.95
        )


def test_vision_pass_port_overrides_material_semantic_and_class():
    doc, _ = build_scene_graph(synthetic_room(), meta(), labeler=_FakeVision())
    schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
    assert not list(Draft202012Validator(schema).iter_errors(doc))
    assert all(s["material"] == "wood" for s in doc["surfaces"])
    assert all(s["semantic"] == "desk" for s in doc["surfaces"])
    assert all(s["class"] == "ledge" for s in doc["surfaces"])
    assert all(s["confidence"] == 0.95 for s in doc["surfaces"])


def test_empty_mesh_rejected():
    with pytest.raises(ValueError, match="no surfaces"):
        build_scene_graph(Mesh([(0.0, 0.0, 0.0)], []), meta())
