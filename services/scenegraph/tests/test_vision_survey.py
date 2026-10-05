"""Vision-pass survey contract (M1-SCEN-02 labels + M3-GAME-01 objects).

Checks the normalisation onto the frozen scene_graph enums, the liftable/pushable segmentation
heuristic, the survey validator, and the ``SurveyVisionLabeler`` port adapter.
"""

from types import SimpleNamespace

from scenegraph import vision_survey as vs
from scenegraph.vision_survey import SceneSurvey, SurveyObject, SurveySurface


def _surface(sid, material, centroid, **kw):
    return SurveySurface(id=sid, material=material, centroid=centroid, **kw)


def _object(oid, **kw):
    return SurveyObject(id=oid, name=kw.pop("name", oid), **kw)


# --- material normalisation onto the frozen enum ---


def test_material_exact_enum_passes_through():
    for m in vs.MATERIALS:
        assert vs.normalize_material(m) == m


def test_material_synonyms_map_into_the_enum():
    cases = {
        "Oak": "wood",
        "reclaimed timber": "wood",
        "white marble": "tile-stone",
        "glazed ceramic": "tile-stone",
        "a plush sofa": "fabric-cushion",
        "corrugated cardboard": "paper-cardboard",
        "LEGO brick": "lego-plastic",
        "brushed steel": "metal",
        "a mirror": "glass",
        "potted fern": "plant",
        "velvet drape": "curtain",
        "a wool rug": "carpet-rug",
    }
    for text, want in cases.items():
        assert vs.normalize_material(text) == want, text


def test_material_miss_is_unknown_never_a_guess():
    for text in ("", None, "zorblax", "something ineffable"):
        assert vs.normalize_material(text) == "unknown"


def test_material_always_returns_a_valid_enum_value():
    for text in ("oak", "zzz", None, "glass table", "weird-thing"):
        assert vs.normalize_material(text) in vs.MATERIALS


# --- semantic normalisation onto ^[a-z][a-z-]{1,31}$ ---


def test_semantic_normalisation():
    assert vs.normalize_semantic("Coffee Table") == "coffee-table"
    assert vs.normalize_semantic("book_shelf") == "book-shelf"
    assert vs.normalize_semantic("  Potted Plant!!  ") == "potted-plant"
    assert vs.normalize_semantic("a") is None  # too short
    assert vs.normalize_semantic("123") is None  # no letters
    assert vs.normalize_semantic(None) is None


def test_semantic_truncates_to_32():
    out = vs.normalize_semantic("x" * 50)
    assert out is not None and len(out) <= 32


# --- the liftable / pushable separability heuristic ---


def test_separability_dynamic_static_reject():
    assert vs.classify_separability(_object("mug", liftable=True)) == "dynamic"
    assert vs.classify_separability(_object("chair", pushable=True)) == "dynamic"
    assert vs.classify_separability(_object("wall", architectural=True)) == "static"
    assert vs.classify_separability(_object("floor", semantic="floor")) == "static"
    assert vs.classify_separability(_object("book-pile", compound=True)) == "reject"
    # present but not established as movable -> conservatively static, never a dynamic object
    assert vs.classify_separability(_object("heavy-cabinet")) == "static"


def test_segmented_objects_returns_only_dynamic_in_order():
    survey = SceneSurvey(
        objects=(
            _object("mug", liftable=True, materials=("ceramic",)),
            _object("floor", semantic="floor"),
            _object("toy", pushable=True),
            _object("book-pile", compound=True),
        )
    )
    got = [o.id for o in vs.segmented_objects(survey)]
    assert got == ["mug", "toy"]


def test_object_primary_material_is_normalised():
    assert _object("mug", materials=("glazed ceramic", "clay")).primary_material == "tile-stone"
    assert _object("x").primary_material == "unknown"


# --- survey validation ---


def test_validate_clean_survey_has_no_problems():
    survey = SceneSurvey(
        scene_name="Toy Desk",
        ambient_sound="quiet room tone with a faint clock tick",
        surfaces=(
            _surface(
                "s-desk",
                "oak",
                (0.0, 1.0, 0.0),
                semantic="desk",
                class_override="walkable-hard",
            ),
            _surface("s-wall", "tile-stone", (2.0, 1.5, 0.0), class_override="wall-smooth"),
        ),
        objects=(
            _object("mug", liftable=True, materials=("ceramic",), semantic="mug"),
            _object("book", pushable=True, materials=("paper",), semantic="book"),
        ),
    )
    assert vs.validate_survey(survey) == []


def test_validate_catches_problems():
    survey = SceneSurvey(
        surfaces=(
            _surface("dup", "wood", (0.0, 0.0, 0.0)),
            _surface("dup", "wood", (1.0, 0.0, 0.0)),  # duplicate id
            _surface("bad-class", "wood", (2.0, 0.0, 0.0), class_override="not-a-class"),
            _surface("bad-conf", "wood", (3.0, 0.0, 0.0), confidence=1.5),
        ),
        objects=(
            _object("contradiction", architectural=True, liftable=True),
            _object("zero", liftable=True, count_estimate=0),
        ),
    )
    problems = vs.validate_survey(survey)
    joined = " | ".join(problems)
    assert "duplicate id" in joined
    assert "not a Bible §4 class" in joined
    assert "out of [0, 1]" in joined
    assert "liftable/pushable" in joined
    assert "count_estimate" in joined


# --- the VisionLabeler port adapter ---


def test_labeler_matches_nearest_surface_within_radius():
    survey = SceneSurvey(
        surfaces=(
            _surface(
                "s-wood",
                "reclaimed oak",
                (0.0, 0.0, 0.0),
                semantic="Desk Top",
                class_override="walkable-hard",
                confidence=0.9,
            ),
            _surface("s-glass", "a mirror", (5.0, 0.0, 0.0), semantic="window"),
        )
    )
    labeler = vs.SurveyVisionLabeler(survey, match_radius_A=0.5)

    near_wood = SimpleNamespace(centroid=(0.1, 0.0, 0.0))
    label = labeler.label(near_wood, "walkable-hard", 0.7)
    assert label.material == "wood"
    assert label.semantic == "desk-top"
    assert label.class_override == "walkable-hard"
    assert label.confidence == 0.9


def test_labeler_falls_back_to_unknown_when_no_surface_is_near():
    survey = SceneSurvey(surfaces=(_surface("s", "oak", (0.0, 0.0, 0.0)),))
    labeler = vs.SurveyVisionLabeler(survey, match_radius_A=0.5)
    far = SimpleNamespace(centroid=(10.0, 10.0, 10.0))
    label = labeler.label(far, "walkable-hard", 0.7)
    assert label.material == "unknown"
    assert label.semantic is None
    assert label.class_override is None


# --- JSON parsing (what the self-hosted model emits) ---


def test_parse_survey_from_json_dict():
    data = {
        "scene_name": "Sterile Lab",
        "ambient_sound": "low ventilation hum",
        "surfaces": [
            {
                "id": "s1",
                "material": "white marble",
                "centroid": [0, 1, 0],
                "semantic": "Counter",
                "class_override": "walkable-hard",
                "confidence": 0.8,
            },
        ],
        "objects": [
            {
                "id": "amphora",
                "name": "terracotta amphora",
                "materials": ["terracotta ceramic"],
                "liftable": True,
                "semantic": "vase",
                "count_estimate": 3,
                "evidence": ["view-02"],
            },
        ],
    }
    survey = vs.parse_survey(data)
    assert survey.scene_name == "Sterile Lab"
    assert survey.ambient_sound == "low ventilation hum"
    assert len(survey.surfaces) == 1 and survey.surfaces[0].centroid == (0.0, 1.0, 0.0)
    assert len(survey.objects) == 1
    obj = survey.objects[0]
    assert obj.primary_material == "tile-stone"
    assert obj.count_estimate == 3
    assert vs.segmented_objects(survey) == [obj]
    assert vs.validate_survey(survey) == []
