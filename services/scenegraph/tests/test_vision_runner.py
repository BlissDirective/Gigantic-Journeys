"""Vision-pass runner (M1-SCEN-02 + M3-GAME-01): model -> validated survey -> labelled scene."""

import pytest
from scenegraph import geometry as g
from scenegraph import vision_runner as vr
from scenegraph.mesh import Mesh
from scenegraph.scene import CaptureMeta, build_scene_graph
from scenegraph.vision_survey import SceneSurvey

ENV_ID = "3c2b1a09-8f7e-4d6c-b5a4-938271605f4e"


def _add_quad(V, T, corners, want):
    base = len(V)
    V.extend([(float(x), float(y), float(z)) for x, y, z in corners])
    a, b, c, d = base, base + 1, base + 2, base + 3
    tris = [(a, b, c), (a, c, d)]
    if g.dot(g.tri_normal(V[a], V[b], V[c]), want) < 0:
        tris = [(a, c, b), (a, d, c)]
    T.extend(tris)


def _floor_mesh() -> Mesh:
    V: list = []
    T: list = []
    _add_quad(V, T, [(-1, 0, -1), (1, 0, -1), (1, 0, 1), (-1, 0, 1)], (0, 1, 0))
    return Mesh(V, T)


def _meta() -> CaptureMeta:
    return CaptureMeta(environment_id=ENV_ID, capture_mode="tabletop", scale_multiplier=12.0)


def test_run_vision_pass_returns_a_validated_survey():
    model = vr.MockVisionModel(
        result={
            "schema_version": 1,
            "scene_name": "mock room",
            "surfaces": [{"id": "s1", "material": "oak", "centroid": [0, 0, 0]}],
            "objects": [{"id": "mug", "materials": ["ceramic"], "liftable": True}],
        }
    )
    survey = vr.run_vision_pass(["view-0.png"], model)
    assert isinstance(survey, SceneSurvey)
    assert len(survey.surfaces) == 1
    assert len(survey.objects) == 1


def test_run_vision_pass_strict_rejects_an_invalid_survey():
    bad = vr.MockVisionModel(
        result={
            "surfaces": [
                {
                    "id": "s",
                    "material": "oak",
                    "centroid": [0, 0, 0],
                    "class_override": "not-a-class",
                }
            ],
            "objects": [],
        }
    )
    with pytest.raises(vr.VisionSurveyError):
        vr.run_vision_pass(["v.png"], bad)
    # non-strict returns the parsed survey anyway
    survey = vr.run_vision_pass(["v.png"], bad, strict=False)
    assert survey.surfaces[0].class_override == "not-a-class"


def test_mock_default_is_an_empty_survey():
    survey = vr.run_vision_pass([], vr.MockVisionModel())
    assert survey.surfaces == () and survey.objects == ()


def test_end_to_end_survey_labels_the_scene_graph():
    """The whole point: a model's survey flows through the labeler into scene_graph.json materials,
    replacing the geometric stub's 'unknown'."""
    model = vr.MockVisionModel(
        result={
            "schema_version": 1,
            "scene_name": "mock room",
            "surfaces": [{"id": "floor", "material": "metal", "centroid": [0, 0, 0]}],
            "objects": [],
        }
    )
    labeler = vr.labeler_from_model(["view-0.png"], model, match_radius_A=1000.0)
    doc, _mesh = build_scene_graph(_floor_mesh(), _meta(), labeler=labeler)
    materials = {s["material"] for s in doc["surfaces"]}
    assert materials == {"metal"}  # survey material reached the built scene graph (not 'unknown')


def test_end_to_end_without_a_match_falls_back_to_unknown():
    model = vr.MockVisionModel(
        result={
            "surfaces": [{"id": "far", "material": "metal", "centroid": [999, 999, 999]}],
            "objects": [],
        }
    )
    labeler = vr.labeler_from_model(["v.png"], model, match_radius_A=0.5)
    doc, _mesh = build_scene_graph(_floor_mesh(), _meta(), labeler=labeler)
    assert {s["material"] for s in doc["surfaces"]} == {"unknown"}  # graceful fallback
