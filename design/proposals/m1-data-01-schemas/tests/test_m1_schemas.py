"""M1-DATA-01 proposal: scene_graph / traversal_graph / environment_spec schemas + consistency.

Proposal-stage tests (the schemas move to data/schemas/ only after the freeze AUTH). They prove
the fixtures validate or are rejected as intended, that the verb→tier table matches SPEC §3.4,
that every surface class is the Bible §4 list, and that the cross-document checker catches the
inconsistencies a schema cannot.
"""

from __future__ import annotations

import copy
import json
import re
import sys
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

HERE = Path(__file__).resolve().parents[1]
REPO = HERE.parents[2]
sys.path.insert(0, str(HERE))

import check_consistency  # noqa: E402

KINDS = ("scene_graph", "traversal_graph", "environment_spec")
FIX = HERE / "fixtures"


def load(p: Path) -> dict:
    return json.loads(p.read_text(encoding="utf-8"))


def schema(kind: str) -> dict:
    return load(HERE / f"{kind}.json")


def validator(kind: str) -> Draft202012Validator:
    s = schema(kind)
    Draft202012Validator.check_schema(s)
    return Draft202012Validator(s)


def walk(node, where="#"):
    if isinstance(node, dict):
        yield where, node
        for k, v in node.items():
            yield from walk(v, f"{where}/{k}")
    elif isinstance(node, list):
        for i, v in enumerate(node):
            yield from walk(v, f"{where}/{i}")


def desk():
    return tuple(load(FIX / "valid" / f"{k}.desk-tabletop.json") for k in KINDS)


@pytest.mark.parametrize("kind", KINDS)
def test_schema_is_2020_12_and_versioned(kind):
    s = schema(kind)
    assert s["$schema"] == "https://json-schema.org/draft/2020-12/schema"
    assert s["properties"]["schema_version"]["const"] == "1.0.0"


@pytest.mark.parametrize("path", sorted((FIX / "valid").glob("*.json")), ids=lambda p: p.stem)
def test_valid_fixture_accepted(path):
    errors = list(validator(path.name.split(".")[0]).iter_errors(load(path)))
    assert not errors, [e.message for e in errors]


@pytest.mark.parametrize("path", sorted((FIX / "invalid").glob("*.json")), ids=lambda p: p.stem)
def test_invalid_fixture_rejected(path):
    assert list(validator(path.name.split(".")[0]).iter_errors(load(path))), path.name


@pytest.mark.parametrize("kind", KINDS)
def test_each_schema_has_valid_and_invalid_fixtures(kind):
    assert list((FIX / "valid").glob(f"{kind}.*.json"))
    assert list((FIX / "invalid").glob(f"{kind}.*.json"))


@pytest.mark.parametrize("kind", KINDS)
def test_objects_closed_and_strings_constrained(kind):
    for pointer, node in walk(schema(kind)):
        if node.get("type") == "object" and "properties" in node:
            assert node.get("additionalProperties") is False, pointer
        if node.get("type") == "string":
            assert "enum" in node or "const" in node or "pattern" in node, pointer


def test_surface_classes_are_bible_section_4():
    bible = (REPO / "design" / "MOVEMENT_BIBLE.md").read_text(encoding="utf-8")
    section = bible.split("## 4.", 1)[1].split("\n## 5.", 1)[0]
    bible_classes = re.findall(r"^\| \*\*([a-z-]+)\*\* \|", section, re.M)
    enum = schema("scene_graph")["$defs"]["surface"]["properties"]["class"]["enum"]
    assert enum == bible_classes


def test_verb_tiers_match_spec_3_4():
    """SPEC §3.4 names the T0 set explicitly; beat 1 may use only those verbs (plus crouch)."""
    rules = schema("traversal_graph")["$defs"]["edge"]["allOf"]
    tiers = {
        r["then"]["properties"]["tier"]["const"]: r["if"]["properties"]["verb"]["enum"]
        for r in rules[:4]
    }
    assert set(tiers["T0"]) == {
        "walk",
        "jog",
        "run",
        "step-up",
        "hop-over",
        "mantle",
        "standing-jump",
        "running-jump",
        "crouch",
    }
    assert {"wall-run", "grapple-swing", "grapple-ascend", "grapple-rappel", "pole-vault"} == set(
        tiers["T3"]
    )
    all_verbs = [v for vs in tiers.values() for v in vs]
    assert len(all_verbs) == len(set(all_verbs))
    assert sorted(all_verbs) == sorted(
        schema("traversal_graph")["$defs"]["edge"]["properties"]["verb"]["enum"]
    )


def test_margin_is_bible_10():
    s = schema("traversal_graph")
    assert s["properties"]["movement"]["properties"]["margin"]["const"] == 0.85
    assert s["$defs"]["edge"]["properties"]["margin_used"]["maximum"] == 0.85


def test_fixture_movement_hash_is_current_config():
    import hashlib

    sha = hashlib.sha256((REPO / "config" / "movement.json").read_bytes()).hexdigest()
    assert desk()[1]["movement"]["config_sha256"] == sha


# ---- cross-document consistency ----


def test_desk_fixture_consistent():
    assert check_consistency.check(*desk()) == []


def test_template_fallback_consistent():
    scene, graph, _ = desk()
    spec = load(FIX / "valid" / "environment_spec.template-fallback.json")
    assert check_consistency.check(scene, graph, spec) == []


def _mutated(fn):
    scene, graph, spec = (copy.deepcopy(d) for d in desk())
    fn(scene, graph, spec)
    return check_consistency.check(scene, graph, spec)


@pytest.mark.parametrize(
    ("name", "mutate", "expect"),
    [
        (
            "broken path",
            lambda s, g, e: e["routes"][0]["beats"][1].update(edge_ids=["edge-9"]),
            "path breaks",
        ),
        (
            "wrong start",
            lambda s, g, e: e["spawn"].update(node_id="node-2"),
            "does not start at the spawn",
        ),
        (
            "unknown edge",
            lambda s, g, e: e["routes"][0]["beats"][3].update(edge_ids=["edge-99"]),
            "unknown edges",
        ),
        (
            "beat tier lies",
            lambda s, g, e: e["routes"][0]["beats"][1].update(max_tier="T2"),
            "max_tier",
        ),
        (
            "teaches unused",
            lambda s, g, e: e["routes"][0]["beats"][2].update(teaches="vault"),
            "never uses it",
        ),
        (
            "margin lies",
            lambda s, g, e: e["routes"][0].update(tightest_margin=0.5),
            "tightest_margin",
        ),
        (
            "summit not plantable",
            lambda s, g, e: g["nodes"][5].update(plantable=False),
            "not plantable",
        ),
        ("node on void", lambda s, g, e: g["nodes"][0].update(surface_id="surface-8"), "void"),
        (
            "env id mismatch",
            lambda s, g, e: s.update(environment_id="00000000-0000-4000-8000-000000000000"),
            "environment_id",
        ),
        ("scale mismatch", lambda s, g, e: e.update(scale_multiplier=10), "scale_multiplier"),
        (
            "stale movement",
            lambda s, g, e: e["generation"]["validator"].update(movement_config_sha256="0" * 64),
            "movement.json",
        ),
        ("rank gap", lambda s, g, e: e["routes"][1].update(rank=3), "ranks"),
        (
            "difficulty inverted",
            lambda s, g, e: e["routes"][1].update(global_difficulty=5),
            "lower global_difficulty",
        ),
        (
            "dangling edge",
            lambda s, g, e: g["edges"][0].update(to="node-77"),
            "not in traversal_graph",
        ),
        (
            "duplicate surface",
            lambda s, g, e: s["surfaces"].append(copy.deepcopy(s["surfaces"][0])),
            "duplicate surface",
        ),
    ],
)
def test_consistency_catches(name, mutate, expect):
    problems = _mutated(mutate)
    assert any(expect in p for p in problems), (name, problems)


def test_required_tool_must_be_taught_before_use():
    def mutate(s, g, e):
        # Route 2 detours through the grapple in its twist without teaching it first.
        g["edges"].append(
            {
                "id": "edge-13",
                "from": "node-5",
                "to": "node-8",
                "verb": "grapple-ascend",
                "tier": "T3",
                "distance_A": 1.0,
                "rise_A": 2.0,
                "margin_used": 0.4,
                "cost": 3.0,
                "commit": False,
                "prerequisites": {"tool": "grapple", "anchor_ledge_A": 0.4},
            }
        )
        g["nodes"][8]["plantable"] = True
        e["summit"].update(node_id="node-9", position=[6, 6.1, -2.2], height_A=6.1)
        r = e["routes"][1]
        r.update(required_tool="grapple", highest_tier="T3")
        r["beats"][2].update(edge_ids=["edge-13"], max_tier="T3", teaches=None)
        r["beats"][3].update(edge_ids=["edge-9"], max_tier="T2", teaches=None)
        e["routes"] = [r | {"rank": 1}]
        e["generation"]["template_fallback"] = False

    problems = _mutated(mutate)
    assert any("must be taught in beat 2+" in p for p in problems), problems
