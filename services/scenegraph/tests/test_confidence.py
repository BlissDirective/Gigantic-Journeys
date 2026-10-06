"""Confidence gating: low-trust geometry -> void/unknown (M1-SCEN-02)."""

import json
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator
from scenegraph import geometry as g
from scenegraph.classify import SceneConfig, VisionLabel
from scenegraph.confidence import UNKNOWN_MATERIAL, VOID_CLASS, gate_surface
from scenegraph.mesh import Mesh
from scenegraph.scene import CaptureMeta, build_scene_graph

REPO = Path(__file__).resolve().parents[3]
SCHEMA = REPO / "data" / "schemas" / "environment" / "scene_graph.json"
ENV_ID = "3c2b1a09-8f7e-4d6c-b5a4-938271605f4e"


def _add_quad(V, T, corners, want):
    base = len(V)
    V.extend([(float(x), float(y), float(z)) for x, y, z in corners])
    a, b, c, d = base, base + 1, base + 2, base + 3
    tris = [(a, b, c), (a, c, d)]
    if g.dot(g.tri_normal(V[a], V[b], V[c]), want) < 0:
        tris = [(a, c, b), (a, d, c)]
    T.extend(tris)


def _floor_and_wall() -> Mesh:
    V: list = []
    T: list = []
    _add_quad(V, T, [(-2, 0, -1.5), (2, 0, -1.5), (2, 0, 1.5), (-2, 0, 1.5)], (0, 1, 0))  # floor
    _add_quad(V, T, [(2, 0, -1.5), (2, 2.5, -1.5), (2, 2.5, 1.5), (2, 0, 1.5)], (1, 0, 0))  # wall
    return Mesh(V, T)


def _meta() -> CaptureMeta:
    return CaptureMeta(environment_id=ENV_ID, capture_mode="room", scale_multiplier=12.0)


# --- gate_surface unit ---------------------------------------------------------


def test_floor_zero_is_a_passthrough():
    r = gate_surface("walkable-hard", 0.2, "wood", "desk", floor=0.0)
    assert (r.cls, r.material, r.semantic, r.gated) == ("walkable-hard", "wood", "desk", False)


def test_below_floor_is_demoted_to_void_unknown():
    r = gate_surface("walkable-hard", 0.2, "wood", "desk", floor=0.5)
    assert r.cls == VOID_CLASS
    assert r.material == UNKNOWN_MATERIAL
    assert r.semantic is None
    assert r.gated is True


def test_at_or_above_floor_passes_through():
    assert gate_surface("ledge", 0.5, "wood", None, floor=0.5).gated is False
    assert gate_surface("ledge", 0.9, "wood", None, floor=0.5).gated is False


def test_already_void_is_not_regated():
    r = gate_surface(VOID_CLASS, 0.1, "unknown", None, floor=0.5)
    assert r.cls == VOID_CLASS and r.gated is False


# --- integration with build_scene_graph ---------------------------------------


class _UniformVision:
    def __init__(self, conf):
        self.conf = conf

    def label(self, patch, geom_class, confidence):
        return VisionLabel(material="wood", semantic="desk", confidence=self.conf)


class _MixedVision:
    """High confidence on up-facing surfaces, low on everything else."""

    def label(self, patch, geom_class, confidence):
        conf = 0.9 if patch.normal[1] > 0.5 else 0.2
        return VisionLabel(material="wood", semantic="desk", confidence=conf)


def test_default_floor_does_not_gate():
    doc, _ = build_scene_graph(_floor_and_wall(), _meta(), labeler=_UniformVision(0.3))
    assert all(s["class"] != VOID_CLASS for s in doc["surfaces"])
    assert all(s["material"] == "wood" for s in doc["surfaces"])


def test_floor_demotes_every_low_confidence_surface():
    cfg = SceneConfig(confidence_floor=0.5)
    doc, _ = build_scene_graph(_floor_and_wall(), _meta(), cfg=cfg, labeler=_UniformVision(0.3))
    assert all(s["class"] == VOID_CLASS for s in doc["surfaces"])
    assert all(s["material"] == UNKNOWN_MATERIAL for s in doc["surfaces"])
    assert all("semantic" not in s for s in doc["surfaces"])
    # The surface still reports its true (low) confidence, so the demotion is explainable.
    assert all(s["confidence"] == 0.3 for s in doc["surfaces"])


def test_mixed_gating_keeps_trusted_surfaces_and_validates_schema():
    cfg = SceneConfig(confidence_floor=0.5)
    doc, _ = build_scene_graph(_floor_and_wall(), _meta(), cfg=cfg, labeler=_MixedVision())
    classes = {s["class"] for s in doc["surfaces"]}
    assert VOID_CLASS in classes  # the low-confidence wall
    assert any(c != VOID_CLASS for c in classes)  # the trusted floor survived
    # Gated surfaces lose material + semantic; trusted ones keep them.
    for s in doc["surfaces"]:
        if s["class"] == VOID_CLASS:
            assert s["material"] == UNKNOWN_MATERIAL and "semantic" not in s
        else:
            assert s["material"] == "wood" and s["semantic"] == "desk"
    schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
    assert not list(Draft202012Validator(schema).iter_errors(doc))


def test_confidence_floor_is_range_checked():
    with pytest.raises(ValueError, match="confidence_floor"):
        SceneConfig(confidence_floor=1.5)
