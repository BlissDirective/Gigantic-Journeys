"""M3-GAME-01 Tier-1 reactivity matrix (AUTH #022): material + verb coverage, AT-2 reactions."""

import copy

import reactivity


def test_shipped_matrix_is_valid_and_complete():
    assert reactivity.validate_reactivity() == []


def test_every_material_has_a_response():
    mr = set(reactivity.load_matrix()["material_response"])
    assert reactivity.scene_graph_materials() <= mr


def test_every_verb_has_a_reaction():
    er = set(reactivity.load_matrix()["event_reaction"])
    assert reactivity.verb_set() <= er


def test_soft_materials_displace_and_rigid_ones_do_not():
    mr = reactivity.load_matrix()["material_response"]
    assert mr["fabric-cushion"]["displacement"] == "dent"
    assert mr["curtain"]["displacement"] == "sway"
    assert mr["plant"]["displacement"] == "flutter"
    assert mr["tile-stone"]["displacement"] == "none"
    assert mr["metal"]["displacement"] == "none"


def test_at2_verb_tool_reactions():
    er = reactivity.load_matrix()["event_reaction"]
    # a wall-run scuffs dust and marks the surface
    assert er["wall-run"]["particle"] == "scuff" and er["wall-run"]["displaces"] is True
    # a rappel sways a curtain (displaces; the curtain material_response = sway)
    assert er["grapple-rappel"]["displaces"] is True
    # the grapple pin mount reacts the anchor object
    assert er["grapple-pin-mount"]["displaces"] is True


def test_no_physics_budget():
    b = reactivity.load_matrix()["budget"]
    assert b["fps_floor"] == 30
    assert "no physics" in b["note"]


def test_validator_catches_a_missing_material_and_bad_kind():
    m = copy.deepcopy(reactivity.load_matrix())
    m["material_response"].pop("wood")
    m["event_reaction"]["walk"]["particle"] = "nope"
    probs = reactivity.validate_reactivity(m)
    assert any("missing scene_graph materials" in p and "wood" in p for p in probs)
    assert any("walk" in p and "particle" in p for p in probs)


def test_validator_catches_a_missing_verb():
    m = copy.deepcopy(reactivity.load_matrix())
    m["event_reaction"].pop("dive-roll")
    probs = reactivity.validate_reactivity(m)
    assert any("missing verbs" in p and "dive-roll" in p for p in probs)


def test_load_is_deterministic():
    assert reactivity.load_matrix() == reactivity.load_matrix()
