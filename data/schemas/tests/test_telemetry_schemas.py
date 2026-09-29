"""M0-DATA-01: frozen telemetry and correction event schemas (AUTH #029).

Checks every fixture validates (or is rejected) as expected, that every event has at
least two valid fixtures, and the privacy invariants: closed objects everywhere, no
forbidden field names, and no unconstrained strings (so no free text can be logged).
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator, FormatChecker

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "fixtures"
SCHEMAS = {
    "telemetry": ROOT / "telemetry_events.schema.json",
    "correction": ROOT / "correction_events.schema.json",
}

# Field names that must never appear anywhere in a schema (SECURITY_CHECKLIST §10.1).
FORBIDDEN = re.compile(
    r"(^|_)(gps|lat|latitude|lon|lng|longitude|location|address|geo|email|phone|"
    r"idfa|idfv|device_id|advertising_id|imei|serial|mac|ip|ip_address|name|"
    r"first_name|last_name|username|display_name|photo|image|video|audio|media|"
    r"url|uri|path|file|comment|note|text|message|description_text|face|body)($|_)"
)


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def validator(kind: str) -> Draft202012Validator:
    schema = load(SCHEMAS[kind])
    Draft202012Validator.check_schema(schema)
    return Draft202012Validator(schema, format_checker=FormatChecker())


def fixtures(state: str) -> list[Path]:
    return sorted((FIXTURES / state).glob("*.json"))


def walk(node, where="#"):
    """Yield (pointer, schema-object) for every subschema dict."""
    if isinstance(node, dict):
        yield where, node
        for key, value in node.items():
            yield from walk(value, f"{where}/{key}")
    elif isinstance(node, list):
        for i, value in enumerate(node):
            yield from walk(value, f"{where}/{i}")


@pytest.mark.parametrize("kind", sorted(SCHEMAS))
def test_schema_is_valid_2020_12(kind):
    schema = load(SCHEMAS[kind])
    assert schema["$schema"] == "https://json-schema.org/draft/2020-12/schema"
    Draft202012Validator.check_schema(schema)
    assert schema["properties"]["schema_version"] == {
        "const": "1.0.0",
        "description": schema["properties"]["schema_version"]["description"],
    }


@pytest.mark.parametrize("path", fixtures("valid"), ids=lambda p: p.stem)
def test_valid_fixture_accepted(path):
    kind = path.name.split(".")[0]
    errors = list(validator(kind).iter_errors(load(path)))
    assert not errors, [e.message for e in errors]


@pytest.mark.parametrize("path", fixtures("invalid"), ids=lambda p: p.stem)
def test_invalid_fixture_rejected(path):
    kind = path.name.split(".")[0]
    assert list(validator(kind).iter_errors(load(path))), f"{path.name} should be rejected"


@pytest.mark.parametrize("kind", sorted(SCHEMAS))
def test_every_event_has_two_valid_fixtures_and_one_invalid(kind):
    events = load(SCHEMAS[kind])["properties"]["event"]["enum"]
    for event in events:
        count = len(list((FIXTURES / "valid").glob(f"{kind}.{event}.*.json")))
        assert count >= 2, f"{kind}.{event}: {count} valid fixtures"
    assert list((FIXTURES / "invalid").glob(f"{kind}.*.json"))


@pytest.mark.parametrize("kind", sorted(SCHEMAS))
def test_every_event_has_a_props_definition(kind):
    schema = load(SCHEMAS[kind])
    events = schema["properties"]["event"]["enum"]
    branches = {b["if"]["properties"]["event"]["const"] for b in schema["allOf"]}
    assert branches == set(events)
    assert set(events) <= set(schema["$defs"])


@pytest.mark.parametrize("kind", sorted(SCHEMAS))
def test_objects_are_closed(kind):
    for pointer, node in walk(load(SCHEMAS[kind])):
        # Every object shape is closed; if/then and anyOf selectors carry no "type".
        if node.get("type") == "object" and "properties" in node:
            assert node.get("additionalProperties") is False, pointer


@pytest.mark.parametrize("kind", sorted(SCHEMAS))
def test_no_forbidden_field_names(kind):
    for pointer, node in walk(load(SCHEMAS[kind])):
        if pointer.split("/")[-1] == "properties" and isinstance(node, dict):
            for field in node:
                assert not FORBIDDEN.search(field), f"{pointer}/{field}"


@pytest.mark.parametrize("kind", sorted(SCHEMAS))
def test_no_unconstrained_strings(kind):
    """Every string is an enum, const or pattern-bound: no free text can be logged."""
    for pointer, node in walk(load(SCHEMAS[kind])):
        if node.get("type") == "string":
            assert "enum" in node or "const" in node or "pattern" in node, pointer


def test_forbidden_pattern_catches_obvious_pii():
    for bad in ["lat", "gps_lat", "email", "device_id", "video_url", "user_name", "comment"]:
        assert FORBIDDEN.search(bad), bad
    for ok in ["user_id", "session_id", "surface_id", "height_A", "duration_s", "reason"]:
        assert not FORBIDDEN.search(ok), ok
