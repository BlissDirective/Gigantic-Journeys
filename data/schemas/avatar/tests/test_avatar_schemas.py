"""Avatar data-contract tests (AUTH #044): avatar_params + consent_record (non-biometric)."""

from __future__ import annotations

import json
import sys
from pathlib import Path

from jsonschema import Draft202012Validator

HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE))

import validate_avatar  # noqa: E402

FIX = HERE / "fixtures"
KINDS = ("avatar_params", "consent_record")


def load(p: Path) -> dict:
    return json.loads(p.read_text(encoding="utf-8"))


def _kind_of(path: Path) -> str:
    return "consent_record" if "consent" in path.name else "avatar_params"


def test_schemas_are_valid_jsonschema():
    for kind in KINDS:
        Draft202012Validator.check_schema(load(HERE / f"{kind}.schema.json"))


def test_valid_fixtures_pass():
    files = sorted((FIX / "valid").glob("*.json"))
    assert files
    for p in files:
        assert validate_avatar.validate(load(p), _kind_of(p)) == [], p.name


def test_invalid_fixtures_fail():
    files = sorted((FIX / "invalid").glob("*.json"))
    assert files
    for p in files:
        assert validate_avatar.validate(load(p), _kind_of(p)) != [], p.name


def test_avatar_params_fixtures_are_non_biometric():
    for p in sorted((FIX / "valid").glob("*avatar*.json")):
        assert validate_avatar.forbidden_keys(load(p)) == [], p.name


def test_forbidden_key_guard_catches_a_biometric_field():
    doc = load(FIX / "valid" / "custom_avatar.json")
    doc["face_landmarks"] = [[0.1, 0.2]]
    assert "face_landmarks" in validate_avatar.forbidden_keys(doc)
    # the closed schema rejects it too (defense in depth)
    assert validate_avatar.validate(doc, "avatar_params") != []


def test_validate_rejects_unknown_kind():
    import pytest

    with pytest.raises(ValueError):
        validate_avatar.validate({}, "not_a_kind")


def test_privacy_invariants_closed_objects_and_constrained_strings():
    # mirrors the telemetry invariant: no open objects; every typed string is enum/const/pattern
    def check(node: object) -> None:
        if not isinstance(node, dict):
            return
        if node.get("type") == "object":
            assert node.get("additionalProperties") is False, node.get("title", node)
        if node.get("type") == "string":
            assert ("enum" in node) or ("const" in node) or ("pattern" in node), node
        for value in node.get("properties", {}).values():
            check(value)
        for key in ("items", "then", "else", "if"):
            if key in node:
                check(node[key])
        for sub in node.get("allOf", []) + node.get("anyOf", []) + node.get("oneOf", []):
            check(sub)

    for kind in KINDS:
        check(load(HERE / f"{kind}.schema.json"))
